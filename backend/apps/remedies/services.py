"""Remedy recommendations, goal seeding, progress, streaks and history, per chart (birth profile)."""
from __future__ import annotations

from datetime import date, timedelta

from django.core.cache import cache
from django.db import transaction
from django.db.models import Count
from django.utils import timezone as dj_tz

from apps.vedic import services as vedic
from apps.vedic.content import goals as gc
from apps.vedic.content import remedies as rc
from apps.vedic.content.common import GLYPH, WEEKDAY_SHORT, short
from apps.vedic.engine.constants import GANDMOOL_NAKSHATRAS, SIGN_TATVA

from .models import RemedyLog, UserRemedy

SEED_REMINDERS = {"mantra": True, "fast": True, "charity": False, "gem": False, "seva": True, "puja": True,
                  "element": True, "custom": True}
ALL_DAYS = list(range(7))
# Bump when the chart rules change, so every account syncs again after a deploy.
SYNC_VERSION = 1


def active(profile):
    """The chart's remedies (not removed)."""
    return UserRemedy.objects.filter(profile=profile, archived_at__isnull=True)


def owned(user):
    """Every chart's remedies of the user (not removed), for lookups by id and reminders."""
    return UserRemedy.objects.filter(user=user, archived_at__isnull=True)


def _new(profile, **fields) -> UserRemedy:
    return UserRemedy.objects.create(user_id=profile.owner_id, profile=profile, **fields)


def current_lords(profile, at=None) -> tuple[str, str]:
    """The running Mahadasha and Antardasha lords."""
    md, ad = vedic._vimshottari(profile).current(at or dj_tz.now(), levels=2)[:2]
    return md.lord, ad.lord


def focus_planets(profile, md: str | None = None) -> list[str]:
    """Graha to support: the Mahadasha lord first, then the weakest graha if it needs support."""
    md = md or current_lords(profile)[0]
    planets = [md]
    shad = vedic.get_strengths(profile)["shadbala"]["planets"]
    weakest = min(shad, key=lambda k: shad[k]["ratio"])
    if shad[weakest]["ratio"] < 1.0 and weakest not in planets:
        planets.append(weakest)
    return planets


FALLBACK_KINDS = ("mantra", "fast", "charity")  # no gemstone, as with goal suggestions


@transaction.atomic
def seed_for(profile, dasha: tuple[str, str] | None = None) -> None:
    """Fallback for a chart without goals (skipped, or never set): mantra, fast and charity for its
    Mahadasha and Antardasha lords."""
    if profile is None or profile.goals or UserRemedy.objects.filter(profile=profile).exists():
        return
    for lord in dict.fromkeys(dasha or current_lords(profile)):
        for kind in FALLBACK_KINDS:
            _new(profile, planet=lord, kind=kind, reminder=SEED_REMINDERS[kind])


CHART_KIND = "mantra"  # chart remedies are each graha's beej mantra


def chart_reasons(profile, at=None, dasha: tuple[str, str] | None = None) -> dict[str, list[str]]:
    """Graha -> reasons it gets a remedy whatever the goals: the lagna lord (when the birth time is
    known), Chandra, the current Mahadasha and Antardasha lords, and, when Chandra was born in a Gandmool
    nakshatra, that nakshatra's lord (Ketu or Budh). Order is kept for badges. `dasha` is the
    (MD, AD) lords at `at`, when the caller already has them."""
    if profile is None:
        return {}
    md, ad = dasha or current_lords(profile, at)
    pairs = []
    lords = house_lords(profile)
    if lords:
        pairs.append(("lagna", lords[1]))
    pairs += [("moon", "Mo"), ("mahadasha", md), ("antardasha", ad)]
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


def lagna_element(profile) -> str | None:
    """The lagna's tattva ("Fire", "Earth", "Air", "Water"), only when the birth time is known."""
    if profile is None or not profile.time_known:
        return None
    return SIGN_TATVA[vedic.get_chart(profile)["lagna"]["sign_index"] - 1]


def chart_wants(profile, at=None, dasha: tuple[str, str] | None = None) -> dict[tuple[str, str], list[str]]:
    """(graha, kind) -> chart reasons: each `chart_reasons` graha's mantra; for no graha, gau seva when
    any graha was born in a Gandmool nakshatra, the one-time shanti puja when Chandra was, and the
    lagna element's practice when the birth time is known."""
    reasons = chart_reasons(profile, at, dasha)
    want = {(planet, CHART_KIND): r for planet, r in reasons.items()}
    if gandmool_birth_planets(profile):
        want[("", UserRemedy.Kind.SEVA)] = ["gandmool_birth"]
    if any("gandmool" in r for r in reasons.values()):
        want[("", UserRemedy.Kind.PUJA)] = ["gandmool"]
    if lagna_element(profile):
        want[("", UserRemedy.Kind.ELEMENT)] = ["lagna_element"]
    return want


def _sync_cache_key(profile) -> str:
    return f"remedy-sync:{profile.pk}"


def _sync_stamp(profile, dasha: tuple[str, str]) -> str:
    """What a chart sync depends on: the profile, its birth data and the running dasha lords."""
    return f"{SYNC_VERSION}:{profile.pk}:{vedic.input_hash(profile)}:{'/'.join(dasha)}"


def forget_sync(profile) -> None:
    """The chart's list changed: the next `refresh_chart` runs the sync again."""
    if profile is not None:
        cache.delete(_sync_cache_key(profile))


def refresh_chart(profile, dasha: tuple[str, str] | None = None) -> None:
    """`sync_chart`, skipped while the profile and the dasha lords are what the last sync saw."""
    if profile is None:
        return
    dasha = dasha or current_lords(profile)
    if cache.get(_sync_cache_key(profile)) != _sync_stamp(profile, dasha):
        sync_chart(profile, dasha=dasha)


@transaction.atomic
def sync_chart(profile, at=None, dasha: tuple[str, str] | None = None) -> None:
    """Keep the chart remedies (see `chart_wants`) on the list as the dasha moves on.

    A reason that no longer holds is dropped; a suggested remedy left with no reason and no goal is
    archived (its history stays on the heatmap). A remedy the user removed while a reason held is
    not added back for that reason."""
    if profile is None:
        return
    dasha = dasha or current_lords(profile, at)
    want = chart_wants(profile, at, dasha)
    now = dj_tz.now()
    rows = list(active(profile).exclude(kind=UserRemedy.Kind.CUSTOM))
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
    dismissed = {(r.planet, r.kind, b) for r in UserRemedy.objects.filter(profile=profile, archived_at__isnull=False)
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
            _new(profile, planet=planet, kind=kind, basis=reasons, reminder=SEED_REMINDERS[kind])
    if at is None:  # a sync for another moment says nothing about now
        cache.set(_sync_cache_key(profile), _sync_stamp(profile, dasha), 60 * 60 * 24)


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


def goal_limit(profile, pro: bool) -> int:
    """How many goals a chart may have: up to 3 with Pro; on the free plan 1 on the user's own chart
    and none on the charts of others."""
    if pro:
        return gc.MAX_GOALS
    return gc.FREE_GOALS if profile.relation == profile.Relation.SELF else 0


@transaction.atomic
def set_goals(profile, goals: list[str]) -> None:
    """Save the chart's goals (empty: skipped) and add the remedies they call for. Suggestions from
    dropped goals are archived, unless the user edited or logged them; once there are goals, so are
    untouched dasha-lord fallback remedies (see `seed_for`)."""
    wanted = suggestions(goals, profile)
    wanted_keys = {(p, k) for p, k, _ in wanted}
    current = {(r.planet, r.kind): r for r in active(profile).exclude(kind=UserRemedy.Kind.CUSTOM)
               .annotate(n_logs=Count("logs"))}
    now = dj_tz.now()
    for key, r in current.items():
        untouched = not r.basis and not r.edited and not r.n_logs and not r.user_added and key not in wanted_keys
        dropped = r.goal and r.goal not in goals
        fallback = not r.goal and goals
        if untouched and (dropped or fallback):
            r.archived_at = now
            r.save(update_fields=["archived_at"])
    for planet, kind, g in wanted:
        r = current.get((planet, kind))
        if r is None:
            _new(profile, planet=planet, kind=kind, goal=g, reminder=SEED_REMINDERS[kind])
        elif r.goal not in goals:
            r.goal = g
            r.save(update_fields=["goal"])
    profile.goals = list(goals)
    profile.goals_chosen_at = now
    profile.save(update_fields=["goals", "goals_chosen_at"])
    forget_sync(profile)


def add_for_planet(profile, planet: str, kinds=("mantra", "charity")) -> list[UserRemedy]:
    forget_sync(profile)
    out = []
    for kind in kinds:
        obj, created = UserRemedy.objects.get_or_create(
            profile=profile, planet=planet, kind=kind, archived_at=None,
            defaults={"user_id": profile.owner_id, "user_added": True})
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


def _element(remedy: UserRemedy) -> str | None:
    """The tattva an "element" remedy is for, from its chart."""
    return lagna_element(remedy.profile) if remedy.kind == UserRemedy.Kind.ELEMENT else None


def effective(remedy: UserRemedy, lang: str) -> dict:
    """Catalogue display data with the user's edits applied. `weekdays` is None for every day;
    `once` marks a remedy done a single time (the shanti puja)."""
    if remedy.kind == UserRemedy.Kind.CUSTOM:
        info = {"title": "", "cadence": "", "text": "", "how": "", "target": 1, "weekday": None}
    else:
        info = rc.remedy(remedy.planet, remedy.kind, lang, _element(remedy))
    info.setdefault("once", False)
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


def done_on(remedy: UserRemedy) -> date | None:
    """The first day a one-time remedy was completed."""
    return min((l.date for l in remedy.logs.all() if l.completed), default=None)


def is_due(remedy: UserRemedy, day: date, info: dict | None = None) -> bool:
    """A one-time remedy is due every day until the day it is done (so it still shows as done that day)."""
    info = info or effective(remedy, "en")
    if info["once"]:
        first = done_on(remedy)
        return first is None or first >= day
    weekdays = info["weekdays"]
    return weekdays is None or (day.weekday() + 1) % 7 in weekdays  # Sunday = 0


def completed_days(profile) -> set[date]:
    if profile is None:
        return set()
    return set(RemedyLog.objects.filter(remedy__profile=profile, completed=True).values_list("date", flat=True))


def _best_run(days: set[date]) -> int:
    best, run, prev = 0, 0, None
    for d in sorted(days):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best


def streak(profile, today: date) -> dict:
    days = completed_days(profile)
    current = 0
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    week = [{"date": (monday + timedelta(days=i)).isoformat(), "done": (monday + timedelta(days=i)) in days,
             "future": monday + timedelta(days=i) > today} for i in range(7)]
    return {"current": current, "best": max(_best_run(days), current), "week": week}


def history(profile, today: date, days: int = 365) -> dict:
    """Per-day remedies done vs due on a chart for the last `days` days (archived remedies included)."""
    start = today - timedelta(days=days - 1)
    remedies = UserRemedy.objects.filter(profile=profile) if profile else UserRemedy.objects.none()
    done = dict(RemedyLog.objects.filter(remedy__in=remedies, completed=True, date__range=(start, today))
                .values("date").annotate(n=Count("id")).values_list("date", "n"))
    due = {start + timedelta(days=i): 0 for i in range(days)}
    for r in remedies.select_related("profile").prefetch_related("logs"):
        info = effective(r, "en")
        if info["once"]:  # counts only on the day it was done, not every day before
            d = done_on(r)
            if d in due:
                due[d] += 1
            continue
        weekdays = info["weekdays"]
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
    # Gau seva names the grahas it is for, and the tattva practice its element, from its chart.
    gandmool = gandmool_birth_planets(remedy.profile) if "gandmool_birth" in remedy.basis else []
    element = _element(remedy)
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
        "basis": remedy.basis, "basis_label": rc.basis_label(remedy.basis, lang, gandmool, element),
        "element": element.lower() if element else None,
        "done_on": d.isoformat() if info["once"] and (d := done_on(remedy)) else None,
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
