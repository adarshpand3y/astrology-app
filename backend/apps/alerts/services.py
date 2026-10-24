"""Build the upcoming notification feed that the phone schedules locally."""
from __future__ import annotations

import hashlib
from datetime import datetime, time, timedelta

from apps.billing.services import is_pro
from apps.remedies import services as rs
from apps.daily.context import DayContext
from apps.daily.services import build_insight, natal
from apps.vedic import services as vedic
from apps.vedic.content.common import HINDI, SANSKRIT, ENGLISH, ordinal, pick
from apps.vedic.content import remedies as rc
from apps.vedic.content.insight import transit_title
from apps.vedic.content.muhurta import alert_text
from apps.vedic.engine import transits as tr
from apps.vedic.engine.chart import jsonable
from apps.vedic.engine.muhurta import compute_muhurtas, find

from .models import AlertPreference

TRANSIT_PLANETS = ("Ma", "Ju", "Sa", "Ra", "Su")
# Period alerts come up to 16 a day (8 day + 8 night), and a phone holds ~60 scheduled alerts
# (iOS caps at 64), so they only cover the next few days; the app re-syncs when it opens.
PERIOD_DAYS = 3
# Alerts go out this long before the event: Android delivers scheduled notifications a few
# minutes late unless the app holds the exact-alarm permission, so arrive early instead.
LEAD = timedelta(minutes=15)


def prefs_for(user) -> AlertPreference:
    prefs, _ = AlertPreference.objects.get_or_create(user=user)
    return prefs


# A mark at the start of each title so the shade reads at a glance: green for a good period,
# amber for neutral, a warning for a bad one, and a symbol of its own for the rest.
_KIND_MARK = {"good": "🟢", "neutral": "🟡", "bad": "⚠️"}
_CATEGORY_MARK = {"rahu": "⛔", "remedy": "🪔", "daily": "✨", "dasha": "🪐", "sade_sati": "🪐"}


def _mark(category: str, kind: str) -> str:
    return _CATEGORY_MARK.get(category) or _KIND_MARK.get(kind, "")


def _item(category: str, event_at: datetime, title: str, body: str, kind: str, lead: timedelta = LEAD,
          end: datetime | None = None) -> dict:
    """`at` is when the phone shows it (`lead` before the event); `event_at` is the event itself.

    Titles and bodies refer to times as `{start}` / `{end}`, with the values in `times`: the phone
    fills them in its own timezone and 12/24-hour setting, which the server can't know."""
    ident = hashlib.sha1(f"{category}:{event_at.isoformat()}:{title}".encode()).hexdigest()[:16]
    times = {"start": event_at, **({"end": end} if end else {})}
    return {"id": ident, "category": category, "at": event_at - lead, "event_at": event_at,
            "title": f"{_mark(category, kind)} {title}".strip(), "body": body, "kind": kind, "times": times}


def _period_items(mu: dict, now: datetime, lang: str, parts: set[str]) -> list[dict]:
    """One alert shortly before each choghadiya of the given parts ("day", "night") begins.
    Night ones get their own category so the phone can post them silently."""
    items = []
    for p in mu["periods"]:
        if p.category != "choghadiya" or p.part not in parts or p.start <= now:
            continue
        text = alert_text(p.key, lang)
        category = "period_night" if p.part == "night" else "period"
        items.append(_item(category, p.start, f"{text['name']}, {{start}}–{{end}}", text["advice"], p.kind,
                           end=p.end))
    return items


def _remedy_item(remedies: list, d, prefs, lang: str, tz) -> dict | None:
    """One reminder listing the remedies due on `d` (reminder on, not already done that day)."""
    due = []
    for r in remedies:
        info = rs.effective(r, lang)
        if not rs.is_due(r, d, info) or any(l.date == d and l.completed for l in r.logs.all()):
            continue
        title = info["title"] or ""
        if r.kind == "charity":
            title = f"{rc.KIND_LABEL[lang]['charity']}: {title}"
        elif r.kind == "mantra" and info.get("target", 1) > 1:
            title = f"{title} ({info['target']}×)"
        due.append(title)
    if not due:
        return None
    at = datetime.combine(d, prefs.remedy_time, tzinfo=tz)
    title = pick(lang, f"Today's remedies · {len(due)}", f"आज के उपाय · {len(due)}")
    return _item("remedy", at, title, ", ".join(due), "good", lead=timedelta(0))


def schedule(ctx: DayContext, days: int) -> list[dict]:
    user, profile, lang, tz = ctx.user, ctx.profile, ctx.lang, ctx.tz
    prefs = prefs_for(user)
    pro = is_pro(user)
    now = ctx.now
    end = now + timedelta(days=days)
    items: list[dict] = []
    n = natal(profile) if profile else None
    v = vedic._vimshottari(profile) if profile else None
    # The phone fetches this feed whenever the app opens, so bring the chart remedies up to date
    # here too (a new Antardasha lord's mantra) instead of waiting for a visit to Remedies.
    rs.sync_chart(user, profile)
    remedies = list(rs.active(user).filter(reminder=True).prefetch_related("logs")) if prefs.remedies else []

    for i in range(days):
        d = ctx.day + timedelta(days=i)
        parts = {part for part, on in (("day", prefs.periods), ("night", prefs.periods_night)) if on}
        mu = compute_muhurtas(d, ctx.lat, ctx.lon, tz) if prefs.rahu or parts else None
        if parts and i < PERIOD_DAYS:
            items.extend(_period_items(mu, now, lang, parts))
        if prefs.rahu:
            rk = find(mu, "rahu_kaal")
            text = alert_text("rahu_kaal", lang)
            items.append(_item("rahu", rk.start, f"{text['name']}, {{start}}–{{end}}", text["advice"], "bad",
                               lead=timedelta(minutes=prefs.rahu_lead_minutes), end=rk.end))
        if prefs.daily and n:
            at = datetime.combine(d, prefs.daily_time, tzinfo=tz)
            if at > now:  # a delivery time the user picked, not an event: no lead
                positions = tr.positions(at, profile.ayanamsa)
                lord = v.current(at, levels=1)[0].lord
                day_ctx = DayContext(**{**ctx.__dict__, "day": d, "now": at})
                text = build_insight(day_ctx, n, positions, lord)["text"]
                items.append(_item("daily", at, pick(lang, "Today, in one line", "आज, एक पंक्ति में"),
                                   text.split(". ")[0].rstrip(".") + ".", "good", lead=timedelta(0)))
        if remedies:
            item = _remedy_item(remedies, d, prefs, lang, tz)
            if item:
                items.append(item)

    if prefs.dasha and v:
        for p in v.current(now, levels=3)[1:]:
            if now < p.end <= end:
                nxt = v.current(p.end + timedelta(seconds=1), levels=p.level)
                if len(nxt) == p.level:
                    chain = " › ".join((HINDI if lang == "hi" else SANSKRIT)[x.lord] for x in nxt)
                    items.append(_item("dasha", p.end, pick(lang, "A new dasha begins at {start}", "{start} से नई दशा"),
                                       chain, "neutral"))

    if pro and prefs.transit and n:
        for code in TRANSIT_PLANETS:
            for ing in tr.ingresses(code, now, end, profile.ayanamsa):
                h = tr.house(ing["to_sign"], n["ref_sign"])
                t = transit_title(code, h, True, lang)
                fav = tr.house(ing["to_sign"], n["moon_sign"]) in tr.GOCHARA_GOOD[code]
                items.append(_item("transit", ing["at"], pick(lang, "Transit at {start}", "{start} पर गोचर परिवर्तन"),
                                   f"{t['title']} — {t['gloss']}", "good" if fav else "bad"))

    if pro and prefs.sade_sati and n:
        ss = tr.sade_sati(n["moon_sign"], now, profile.ayanamsa)
        for label, span in (("start", (ss.get("next") or {}).get("start")), ("end", (ss.get("current") or {}).get("end"))):
            if span and now < span <= end:
                items.append(_item("sade_sati", span, pick(lang, "Sade Sati · {start}", "साढ़े साती · {start}"),
                                   pick(lang, "Saturn's 7½-year passage " + ("begins." if label == "start" else "ends."),
                                        "शनि की साढ़े साती " + ("आरंभ हो रही है।" if label == "start" else "समाप्त हो रही है।")),
                                   "neutral"))

    items = [i for i in items if i["at"] > now]  # too close to the event to warn in time
    items.sort(key=lambda x: x["at"])
    return jsonable(items, tz)
