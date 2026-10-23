"""Build the upcoming notification feed that the phone schedules locally."""
from __future__ import annotations

import hashlib
from datetime import datetime, time, timedelta

from apps.billing.services import is_pro
from apps.daily.context import DayContext
from apps.daily.services import build_insight, natal
from apps.vedic import services as vedic
from apps.vedic.content.common import HINDI, SANSKRIT, ENGLISH, ordinal, pick
from apps.vedic.content.insight import transit_title
from apps.vedic.content.muhurta import period_text
from apps.vedic.engine import transits as tr
from apps.vedic.engine.chart import jsonable
from apps.vedic.engine.muhurta import compute_muhurtas, find

from .models import AlertPreference

TRANSIT_PLANETS = ("Ma", "Ju", "Sa", "Ra", "Su")
# Period alerts come 8 a day, and a phone holds ~60 scheduled alerts (iOS caps at 64), so they
# only cover the next few days; the app re-syncs the schedule each time it opens.
PERIOD_DAYS = 3


def prefs_for(user) -> AlertPreference:
    prefs, _ = AlertPreference.objects.get_or_create(user=user)
    return prefs


def _item(category: str, at: datetime, title: str, body: str, kind: str) -> dict:
    ident = hashlib.sha1(f"{category}:{at.isoformat()}:{title}".encode()).hexdigest()[:16]
    return {"id": ident, "category": category, "at": at, "title": title, "body": body, "kind": kind}


def _hm(dt: datetime, tz) -> str:
    return dt.astimezone(tz).strftime("%H:%M")


def _period_items(mu: dict, now: datetime, lang: str, tz) -> list[dict]:
    """One alert as each daytime choghadiya begins (night ones would fire in the small hours)."""
    items = []
    for p in mu["periods"]:
        if p.category != "choghadiya" or p.part != "day" or p.start <= now:
            continue
        text = period_text(p.key, lang)
        items.append(_item("period", p.start, pick(lang, f"Now: {text['name']}", f"अब: {text['name']}"),
                           pick(lang, f"Until {_hm(p.end, tz)}. {text['gloss']}.",
                                f"{_hm(p.end, tz)} तक। {text['gloss']}।"), p.kind))
    return items


def schedule(ctx: DayContext, days: int) -> list[dict]:
    user, profile, lang, tz = ctx.user, ctx.profile, ctx.lang, ctx.tz
    prefs = prefs_for(user)
    pro = is_pro(user)
    now = ctx.now
    end = now + timedelta(days=days)
    items: list[dict] = []
    n = natal(profile) if profile else None
    v = vedic._vimshottari(profile) if profile else None

    for i in range(days):
        d = ctx.day + timedelta(days=i)
        mu = compute_muhurtas(d, ctx.lat, ctx.lon, tz) if prefs.rahu or prefs.periods else None
        if prefs.periods and i < PERIOD_DAYS:
            items.extend(_period_items(mu, now, lang, tz))
        if prefs.rahu:
            rk = find(mu, "rahu_kaal")
            at = rk.start - timedelta(minutes=prefs.rahu_lead_minutes)
            if at > now:
                items.append(_item("rahu", at, pick(lang, "Rahu Kaal soon", "राहु काल शीघ्र"),
                                   pick(lang, f"Hold new commitments until {_hm(rk.end, tz)}.",
                                        f"{_hm(rk.end, tz)} तक नए संकल्प रोकें।"), "bad"))
        if prefs.daily and n:
            at = datetime.combine(d, prefs.daily_time, tzinfo=tz)
            if at > now:
                positions = tr.positions(at, profile.ayanamsa)
                lord = v.current(at, levels=1)[0].lord
                day_ctx = DayContext(**{**ctx.__dict__, "day": d, "now": at})
                text = build_insight(day_ctx, n, positions, lord)["text"]
                items.append(_item("daily", at, pick(lang, "Today, in one line", "आज, एक पंक्ति में"),
                                   text.split(". ")[0].rstrip(".") + ".", "good"))

    if prefs.dasha and v:
        for p in v.current(now, levels=3)[1:]:
            if now < p.end <= end:
                nxt = v.current(p.end + timedelta(seconds=1), levels=p.level)
                if len(nxt) == p.level:
                    chain = " › ".join((HINDI if lang == "hi" else SANSKRIT)[x.lord] for x in nxt)
                    items.append(_item("dasha", p.end, pick(lang, "A new period begins", "नई दशा आरंभ"),
                                       chain, "neutral"))

    if pro and prefs.transit and n:
        for code in TRANSIT_PLANETS:
            for ing in tr.ingresses(code, now, end, profile.ayanamsa):
                h = tr.house(ing["to_sign"], n["ref_sign"])
                t = transit_title(code, h, True, lang)
                fav = tr.house(ing["to_sign"], n["moon_sign"]) in tr.GOCHARA_GOOD[code]
                items.append(_item("transit", ing["at"], pick(lang, "Transit hit", "गोचर परिवर्तन"),
                                   f"{t['title']} — {t['gloss']}", "good" if fav else "bad"))

    if pro and prefs.sade_sati and n:
        ss = tr.sade_sati(n["moon_sign"], now, profile.ayanamsa)
        for label, span in (("start", (ss.get("next") or {}).get("start")), ("end", (ss.get("current") or {}).get("end"))):
            if span and now < span <= end:
                items.append(_item("sade_sati", span, pick(lang, "Sade Sati", "साढ़े साती"),
                                   pick(lang, "Saturn's 7½-year passage " + ("begins." if label == "start" else "ends."),
                                        "शनि की साढ़े साती " + ("आरंभ हो रही है।" if label == "start" else "समाप्त हो रही है।")),
                                   "neutral"))

    items.sort(key=lambda x: x["at"])
    return jsonable(items, tz)
