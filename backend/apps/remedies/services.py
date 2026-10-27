"""Remedy recommendations, goal seeding, progress, streaks and history."""
from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone as dj_tz

from apps.vedic import services as vedic
from apps.vedic.content import goals as gc
from apps.vedic.content import remedies as rc
from apps.vedic.content.common import GLYPH, WEEKDAY_SHORT, short
from apps.vedic.engine.constants import GANDMOOL_NAKSHATRAS

from .models import RemedyLog, UserRemedy

SEED_REMINDERS = {"mantra": True, "fast": True, "charity": False, "gem": False, "seva": True, "custom": True}
ALL_DAYS = list(range(7))


def active(user):
    return UserRemedy.objects.filter(user=user, archived_at__isnull=True)


def focus_planets(profile) -> list[str]:
    """Graha to support: the Mahadasha lord first, then the weakest graha if it needs support."""
    md = vedic._vimshottari(profile).current(dj_tz.now(), levels=1)[0].lord
    planets = [md]
    shad = vedic.get_strengths(profile)["shadbala"]["planets"]
    weakest = min(shad, key=lambda k: shad[k]["ratio"])
    if shad[weakest]["ratio"] < 1.0 and weakest not in planets:
        planets.append(weakest)
    return planets


@transaction.atomic
def seed_for(user, profile) -> None:
    """Fallback for accounts without goals: the four remedies of the Mahadasha lord."""
    if user.goals or UserRemedy.objects.filter(user=user).exists() or profile is None:
        return
    lord = focus_planets(profile)[0]
    for kind in rc.KINDS:
        UserRemedy.objects.get_or_create(user=user, planet=lord, kind=kind, archived_at=None,
                                         defaults={"reminder": SEED_REMINDERS[kind]})


CHART_KIND = "mantra"  # chart remedies are each graha's beej mantra


def chart_reasons(profile, at=None) -> dict[str, list[str]]:
    """Graha -> reasons it gets a remedy whatever the goals: the lagna lord (when the birth time is
    known), Chandra, the current Mahadasha and Antardasha lords, and, when Chandra was born in a Gandmool
    nakshatra, that nakshatra's lord (Ketu or Budh). Order is kept for badges."""
    if profile is None:
        return {}
    md, ad = vedic._vimshottari(profile).current(at or dj_tz.now(), levels=2)[:2]
    pairs = []
    lords = house_lords(profile)
    if lords:
        pairs.append(("lagna", lords[1]))
    pairs += [("moon", "Mo"), ("mahadasha", md.lord), ("antardasha", ad.lord)]
    moon_nak = next(p for p in vedic.get_chart(profile)["planets"] if p["code"] == "Mo")["nakshatra"]
    if moon_nak["index"] - 1 in GANDMOOL_NAKSHATRAS:
        pairs.append(("gandmool", moon_nak["lord"]))
    out: dict[str, list[str]] = {}
    for reason, planet in pairs:
        out.setdefault(planet, []).append(reason)
    return out


def gandmool_birth_planets(profile) -> list[str]:
    """Grahas that were in a Gandmool nakshatra at birth, in chart order."""
    if profile is None:
        return []
    return [p["code"] for p in vedic.get_chart(profile)["planets"]
            if p["nakshatra"]["index"] - 1 in GANDMOOL_NAKSHATRAS]


def chart_wants(profile, at=None) -> dict[tuple[str, str], list[str]]:
    """(graha, kind) -> chart reasons: each `chart_reasons` graha's mantra, plus gau seva (no graha)
    when any graha was born in a Gandmool nakshatra."""
    want = {(planet, CHART_KIND): reasons for planet, reasons in chart_reasons(profile, at).items()}
    if gandmool_birth_planets(profile):
        want[("", UserRemedy.Kind.SEVA)] = ["gandmool_birth"]
    return want


@transaction.atomic
def sync_chart(user, profile, at=None) -> None:
    """Keep the chart remedies (see `chart_wants`) on the list as the dasha moves on.

    A reason that no longer holds is dropped; a suggested remedy left with no reason and no goal is
    archived (its history stays on the heatmap). A remedy the user removed while a reason held is
    not added back for that reason."""
    if profile is None:
        return
    want = chart_wants(profile, at)
    now = dj_tz.now()
    rows = list(active(user).exclude(kind=UserRemedy.Kind.CUSTOM))
    for r in rows:
        if not r.basis:
            continue
        keep = [b for b in r.basis if b in want.get((r.planet, r.kind), [])]
        if keep != r.basis:
            r.basis = keep
            if not keep and not r.goal and not r.user_added:
                r.archived_at = now
            r.save(update_fields=["basis", "archived_at"])
    current = {(r.planet, r.kind): r for r in rows if r.archived_at is None}
    dismissed = {(r.planet, r.kind, b) for r in UserRemedy.objects.filter(user=user, archived_at__isnull=False)
                 for b in r.basis}
    for (planet, kind), reasons in want.items():
        r = current.get((planet, kind))
        if r is not None:
            missing = [b for b in reasons if b not in r.basis]
            if missing:
                r.basis = r.basis + missing
                r.save(update_fields=["basis"])
            continue
        reasons = [b for b in reasons if (planet, kind, b) not in dismissed]
        if reasons:
            UserRemedy.objects.create(user=user, planet=planet, kind=kind, basis=reasons,
                                      reminder=SEED_REMINDERS[kind])


def house_lords(profile) -> dict[int, str] | None:
    """Bhava -> lord, only when the birth time (and so the lagna) is known."""
    if profile is None or not profile.time_known:
        return None
    return {b["bhava"]: b["lord"] for b in vedic.get_strengths(profile)["bhavabala"]}


def suggestions(goals: list[str], profile) -> list[tuple[str, str, str]]:
    """(planet, kind, goal) to suggest: mantra, fast and charity for each goal's main graha,
    a mantra for its second graha. No gemstones — those need an expert's review."""
    lords = house_lords(profile)
    out, seen = [], set()
    for g in goals:
        for i, planet in enumerate(gc.planets_for(g, lords)):
            for kind in (("mantra", "fast", "charity") if i == 0 else ("mantra",)):
                if (planet, kind) not in seen:
                    seen.add((planet, kind))
                    out.append((planet, kind, g))
    return out


@transaction.atomic
def set_goals(user, profile, goals: list[str]) -> None:
    """Save the user's goals and add the remedies they call for. Suggestions from goals the user
    dropped are archived, unless the user edited or logged them."""
    wanted = suggestions(goals, profile)
    wanted_keys = {(p, k) for p, k, _ in wanted}
    current = {(r.planet, r.kind): r for r in active(user).exclude(kind=UserRemedy.Kind.CUSTOM)
               .annotate(n_logs=Count("logs"))}
    now = dj_tz.now()
    for key, r in current.items():
        if (r.goal and r.goal not in goals and key not in wanted_keys and not r.basis
                and not r.edited and not r.n_logs):
            r.archived_at = now
            r.save(update_fields=["archived_at"])
    for planet, kind, g in wanted:
        r = current.get((planet, kind))
        if r is None:
            UserRemedy.objects.create(user=user, planet=planet, kind=kind, goal=g, reminder=SEED_REMINDERS[kind])
        elif r.goal not in goals:
            r.goal = g
            r.save(update_fields=["goal"])
    user.goals = list(goals)
    user.save(update_fields=["goals"])


def add_for_planet(user, planet: str, kinds=("mantra", "charity")) -> list[UserRemedy]:
    out = []
    for kind in kinds:
        obj, created = UserRemedy.objects.get_or_create(user=user, planet=planet, kind=kind, archived_at=None,
                                                        defaults={"user_added": True})
        if not created and not obj.user_added:
            obj.user_added = True  # the user asked for it, so it stays when its chart reason ends
            obj.save(update_fields=["user_added"])
        out.append(obj)
    return out


def _cadence(weekdays: list[int] | None, target: int, lang: str) -> str:
    hi = lang == "hi"
    days = ("रोज़" if hi else "daily") if not weekdays or len(weekdays) == 7 else \
        ", ".join(WEEKDAY_SHORT[lang][d] for d in weekdays)
    return f"{target}× · {days}" if target > 1 else days


def effective(remedy: UserRemedy, lang: str) -> dict:
    """Catalogue display data with the user's edits applied. `weekdays` is None for every day."""
    if remedy.kind == UserRemedy.Kind.CUSTOM:
        info = {"title": "", "cadence": "", "text": "", "how": "", "target": 1, "weekday": None}
    else:
        info = rc.remedy(remedy.planet, remedy.kind, lang)
    weekdays = None if info["weekday"] is None else [info["weekday"]]
    for f in ("title", "text", "how"):
        if getattr(remedy, f):
            info[f] = getattr(remedy, f)
    if remedy.target:
        info["target"] = remedy.target
    if remedy.weekdays is not None:
        weekdays = sorted(set(remedy.weekdays)) if len(set(remedy.weekdays)) < 7 else None
    if remedy.cadence:
        info["cadence"] = remedy.cadence
    elif remedy.target or remedy.weekdays is not None or not info["cadence"]:
        info["cadence"] = _cadence(weekdays, info["target"], lang)
    info["weekdays"] = weekdays
    info.pop("weekday", None)
    return info


def is_due(remedy: UserRemedy, day: date, info: dict | None = None) -> bool:
    weekdays = (info or effective(remedy, "en"))["weekdays"]
    return weekdays is None or (day.weekday() + 1) % 7 in weekdays  # Sunday = 0


def completed_days(user) -> set[date]:
    return set(RemedyLog.objects.filter(remedy__user=user, completed=True).values_list("date", flat=True))


def _best_run(days: set[date]) -> int:
    best, run, prev = 0, 0, None
    for d in sorted(days):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best


def streak(user, today: date) -> dict:
    days = completed_days(user)
    current = 0
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    week = [{"date": (monday + timedelta(days=i)).isoformat(), "done": (monday + timedelta(days=i)) in days,
             "future": monday + timedelta(days=i) > today} for i in range(7)]
    return {"current": current, "best": max(_best_run(days), current), "week": week}


def history(user, today: date, days: int = 365) -> dict:
    """Per-day remedies done vs due for the last `days` days (archived remedies included)."""
    start = today - timedelta(days=days - 1)
    done = dict(RemedyLog.objects.filter(remedy__user=user, completed=True, date__range=(start, today))
                .values("date").annotate(n=Count("id")).values_list("date", "n"))
    due = {start + timedelta(days=i): 0 for i in range(days)}
    for r in UserRemedy.objects.filter(user=user):
        weekdays = effective(r, "en")["weekdays"]
        first = max(start, r.created_at.date())
        last = min(today, r.archived_at.date() - timedelta(days=1)) if r.archived_at else today
        d = first
        while d <= last:
            if weekdays is None or (d.weekday() + 1) % 7 in weekdays:
                due[d] += 1
            d += timedelta(days=1)
    rows = [{"date": d.isoformat(), "done": done.get(d, 0), "due": max(n, done.get(d, 0))} for d, n in due.items()]
    active_days = {d for d, n in done.items() if n}
    return {
        "start": start.isoformat(), "end": today.isoformat(), "days": rows,
        "totals": {"active_days": len(active_days), "completions": sum(done.values()),
                   "best_streak": _best_run(active_days)},
    }


def serialize(remedy: UserRemedy, today: date, lang: str) -> dict:
    info = effective(remedy, lang)
    # Gau seva names the grahas it is for, from the active chart.
    gandmool = gandmool_birth_planets(remedy.user.active_profile) if "gandmool_birth" in remedy.basis else []
    log = next((l for l in remedy.logs.all() if l.date == today), None)
    monday = today - timedelta(days=today.weekday())
    done = {l.date for l in remedy.logs.all() if l.completed}
    custom = remedy.kind == UserRemedy.Kind.CUSTOM
    return {
        "id": remedy.id, "planet": remedy.planet, "planet_glyph": GLYPH.get(remedy.planet, ""),
        "planet_name": short(remedy.planet, lang) if remedy.planet else "", "kind": remedy.kind,
        "kind_label": ("अपना" if lang == "hi" else "Your own") if custom else rc.KIND_LABEL[lang][remedy.kind],
        "glyph": "✦" if custom else rc.KIND_GLYPH[remedy.kind],
        "goal": remedy.goal, "goal_label": gc.label(remedy.goal, lang),
        # Badge: the goal it serves, else why the chart calls for it ("Mahadasha", "Lagna"…).
        "goal_short": gc.short_label(remedy.goal, lang) or rc.basis_short(remedy.basis, lang),
        "basis": remedy.basis, "basis_label": rc.basis_label(remedy.basis, lang, gandmool),
        "reminder": remedy.reminder, "due_today": is_due(remedy, today, info),
        "edited": remedy.edited,
        "overrides": {f: getattr(remedy, f) for f in UserRemedy.OVERRIDES},
        **info,
        "today": {"count": log.count if log else 0, "completed": bool(log and log.completed)},
        "week": [{"date": (monday + timedelta(days=i)).isoformat(),
                  "done": (monday + timedelta(days=i)) in done} for i in range(7)],
    }


def log_for(remedy: UserRemedy, day: date) -> RemedyLog:
    log, _ = RemedyLog.objects.get_or_create(remedy=remedy, date=day)
    return log
