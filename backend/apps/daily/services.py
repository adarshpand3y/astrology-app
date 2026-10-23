"""Daily companion features: home, day timeline, panchang, decisions, transits."""
from __future__ import annotations

from datetime import datetime, timedelta

from django.core.cache import cache

from apps.vedic import services as vedic
from apps.vedic.content import insight as insight_text
from apps.vedic.content import panchang as pc
from apps.vedic.content.activities import RANGES, activity_meta
from apps.vedic.content.common import KIND_LABEL, nakshatra_name, yoga_name
from apps.vedic.content.muhurta import period_text
from apps.vedic.engine import transits as tr
from apps.vedic.engine.attributes import is_combust
from apps.vedic.engine.chart import compute_day_panchang, jsonable
from apps.vedic.engine.decision import rank_windows
from apps.vedic.engine.muhurta import compute_muhurtas, find
from apps.vedic.engine.panchang import tithi_name

from .context import DayContext

GOOD_FROM_MOON = {1, 3, 6, 7, 10, 11}


# --- natal helpers --------------------------------------------------------------------
def natal(profile) -> dict:
    chart = vedic.get_chart(profile)
    moon = next(p for p in chart["planets"] if p["code"] == "Mo")
    lagna_sign = chart["lagna"]["sign_index"] - 1
    moon_sign = moon["sign_index"] - 1
    return {
        "chart": chart,
        "lagna_sign": lagna_sign,
        "moon_sign": moon_sign,
        "moon_nakshatra": moon["nakshatra"]["index"],
        # Without a birth time the Lagna is unreliable: read houses from the Moon (Chandra lagna).
        "ref_sign": lagna_sign if profile.time_known else moon_sign,
    }


def _period(p, now: datetime) -> dict:
    total = (p.end - p.start).total_seconds()
    return {"lord": p.lord, "level": p.level, "path": "/".join(p.path), "start": p.start, "end": p.end,
            "progress": max(0.0, min(1.0, (now - p.start).total_seconds() / total)),
            "remaining_seconds": max(0, (p.end - now).total_seconds())}


def _kind_label(kind: str, lang: str) -> str:
    return KIND_LABEL[lang][kind]


def _block(p, lang: str, *, key: str | None = None) -> dict:
    key = key or p.key
    text = period_text(key, lang)
    return {"key": p.key, "category": p.category, "kind": p.kind, "part": p.part, "start": p.start, "end": p.end,
            "name": text["name"], "short": text["short"], "gloss": text["gloss"],
            "kind_label": _kind_label(p.kind, lang)}


def _abhijit_key(p, weekday: int) -> str:
    return "abhijit_wed" if p.key == "abhijit" and weekday == 3 else p.key


# --- Home -------------------------------------------------------------------------------
def build_insight(ctx: DayContext, n: dict, positions: dict, md_lord: str) -> dict:
    moon_sign = positions["Mo"]["sign"]
    moon_house = tr.house(moon_sign, n["ref_sign"])
    supportive = tr.house(moon_sign, n["moon_sign"]) in GOOD_FROM_MOON
    lp = positions[md_lord]
    if md_lord in ("Ra", "Ke"):
        state = "favourable" if tr.house(lp["sign"], n["moon_sign"]) in tr.GOCHARA_GOOD[md_lord] else "strained"
    elif lp["retrograde"]:
        state = "retrograde"
    elif md_lord not in ("Su", "Mo") and is_combust(md_lord, lp["lon"], positions["Su"]["lon"], lp["retrograde"]):
        state = "combust"
    elif tr.house(lp["sign"], n["moon_sign"]) in tr.GOCHARA_GOOD[md_lord]:
        state = "favourable"
    else:
        state = "strained"
    out = insight_text.compose(moon_house, supportive, md_lord, state, ctx.lang)
    out.update({"moon_house": moon_house, "supportive": supportive, "lord": md_lord, "lord_state": state})
    return out


def home(ctx: DayContext) -> dict:
    profile = ctx.profile
    n = natal(profile)
    positions = tr.positions(ctx.now, profile.ayanamsa)
    v = vedic._vimshottari(profile)
    chain = v.current(ctx.now, levels=2)
    md, ad = chain[0], chain[1]

    report = tr.transit_report(n["ref_sign"], n["moon_sign"], ctx.now, profile.ayanamsa)
    head = tr.headline_transit(report, ctx.now, profile.ayanamsa)
    fresh = head["days_since"] <= 10
    peak = tr.culmination(head["planet"], ctx.local_midnight(), ctx.lat, ctx.lon)

    mu = compute_muhurtas(ctx.day, ctx.lat, ctx.lon, ctx.tz)
    wd = mu["weekday"]
    windows = []
    abhijit = find(mu, "abhijit")
    windows.append(_block(abhijit, ctx.lang, key=_abhijit_key(abhijit, wd)))
    windows.append(_block(find(mu, "rahu_kaal"), ctx.lang))
    goods = [p for p in mu["periods"] if p.category == "choghadiya" and p.kind == "good" and p.part == "day"]
    upcoming = [p for p in goods if p.end > ctx.now] or goods
    best = next((p for p in upcoming if p.key == "choghadiya.amrit"), upcoming[0] if upcoming else None)
    if best:
        windows.append(_block(best, ctx.lang))

    local_hour = ctx.now.astimezone(ctx.tz).hour if ctx.is_today else 9
    greeting = "morning" if local_hour < 12 else "afternoon" if local_hour < 17 else "evening"
    return jsonable({
        "date": ctx.day.isoformat(),
        "weekday": wd,
        "greeting": greeting,
        "name": profile.name.split(" ")[0],
        "profile": {"id": str(profile.id), "name": profile.name, "relation": profile.relation},
        "location": {"label": ctx.place_label, "city": ctx.place_city, "region": ctx.place_region},
        "insight": build_insight(ctx, n, positions, md.lord),
        "period": {"mahadasha": _period(md, ctx.now), "antardasha": _period(ad, ctx.now)},
        "transit": {**{k: head[k] for k in ("planet", "house", "house_from_moon", "favourable", "retrograde")},
                    **insight_text.transit_title(head["planet"], head["house"], fresh, ctx.lang),
                    "kind": "good" if head["favourable"] else "bad",
                    "entered_at": head["entered_at"], "fresh": fresh, "peak": peak},
        "windows": windows,
    }, ctx.tz)


# --- Day timeline ---------------------------------------------------------------------
def timeline(ctx: DayContext) -> dict:
    mu = compute_muhurtas(ctx.day, ctx.lat, ctx.lon, ctx.tz)
    day = mu["day"]
    wd = mu["weekday"]
    blocks = []
    for p in mu["periods"]:
        if p.key == "brahma":
            blocks.append(_block(p, ctx.lang))
            continue
        blocks.append(_block(p, ctx.lang, key=_abhijit_key(p, wd)))
    marker = lambda key, at, kind: {  # noqa: E731
        "key": key, "category": "marker", "kind": kind, "part": "day", "start": at, "end": None,
        **{k: v for k, v in period_text(key, ctx.lang).items()}, "kind_label": _kind_label(kind, ctx.lang)}
    blocks.append(marker("sunrise", day.sunrise, "good"))
    blocks.append(marker("sunset", day.sunset, "neutral"))
    order = {"marker": 0, "muhurta": 1, "kaal": 2, "choghadiya": 3}
    blocks.sort(key=lambda b: (b["start"], order[b["category"]]))
    return jsonable({
        "date": ctx.day.isoformat(), "weekday": wd,
        "location": {"label": ctx.place_label, "city": ctx.place_city, "region": ctx.place_region,
                     "latitude": ctx.lat, "longitude": ctx.lon},
        "sunrise": day.sunrise, "sunset": day.sunset, "next_sunrise": day.next_sunrise,
        "blocks": blocks,
        "now": ctx.now if ctx.is_today else None,
    }, ctx.tz)


# --- Panchang -------------------------------------------------------------------------
def panchang(ctx: DayContext) -> dict:
    mu = compute_muhurtas(ctx.day, ctx.lat, ctx.lon, ctx.tz)
    at = mu["day"].sunrise + timedelta(minutes=1)
    ayanamsa = ctx.profile.ayanamsa if ctx.profile else "lahiri"
    raw = compute_day_panchang(at, ctx.lat, ctx.lon, ctx.tz_name, ayanamsa)
    p = raw["panchang"]
    lang = ctx.lang

    t_idx = p["tithi"]["index"]
    nak = p["nakshatra"]
    nak_info = pc.nakshatra_info(nak["index"], nak["lord"], lang)
    yoga = p["yoga"]
    yoga_info = pc.yoga_info(yoga["index"], lang)
    karana_info = pc.karana_info(p["karana"]["name"], lang)
    vara = pc.vara_info(mu["weekday"], lang)
    month = p["lunar_month"]
    shaka = pc.shaka_year(ctx.day.year, ctx.day.month, month["amanta"])
    nak_display = nakshatra_name(nak["index"], nak["name"], lang)
    yoga_display = yoga_name(yoga["index"], yoga["name"], lang)

    rows = [
        {"key": "tithi", "kind": pc.tithi_kind(t_idx), "name": tithi_name(t_idx - 1), "paksha": p["tithi"]["paksha"],
         "detail": pc.tithi_detail(t_idx, lang), "end": p["tithi"]["end"]},
        {"key": "vara", "kind": vara["kind"], "name": p["vara"]["name"], "detail": vara["detail"], "end": None},
        {"key": "nakshatra", "kind": nak_info["kind"], "name": nak["name"], "detail": nak_info["detail"],
         "pada": nak["pada"], "end": nak["end"]},
        {"key": "yoga", "kind": yoga_info["kind"], "name": yoga["name"], "detail": yoga_info["detail"], "end": yoga["end"]},
        {"key": "karana", "kind": karana_info["kind"], "name": p["karana"]["name"], "detail": karana_info["detail"],
         "end": p["karana"]["end"]},
    ]
    return {
        "date": ctx.day.isoformat(),
        "location": {"label": ctx.place_label, "city": ctx.place_city, "region": ctx.place_region,
                     "latitude": ctx.lat, "longitude": ctx.lon},
        "shaka_year": shaka, "vikram_year": shaka + 135,
        "month": month["amanta"], "is_adhika": month["is_adhika"], "paksha": p["tithi"]["paksha"],
        "sunrise": p["sunrise"], "sunset": p["sunset"], "moonrise": p["moonrise"], "moonset": p["moonset"],
        "rows": rows,
        "note": pc.note(yoga_display, yoga_info["kind"], nak_display, nak_info["nature"], lang),
    }


# --- Decision assistant ---------------------------------------------------------------
def decision(ctx: DayContext, activity: str, range_key: str) -> dict:
    profile = ctx.profile
    n = natal(profile)
    days = RANGES[range_key][2]
    hour = ctx.now.replace(minute=0, second=0, microsecond=0)
    cache_key = f"decision:{profile.pk}:{vedic.input_hash(profile)[:12]}:{activity}:{range_key}:{ctx.lat:.3f}:{ctx.lon:.3f}:{hour.isoformat()}:{ctx.lang}"
    results = cache.get(cache_key)
    if results is None:
        results = rank_windows(activity, ctx.now.astimezone(ctx.tz).date(), days, ctx.now, ctx.lat, ctx.lon, ctx.tz,
                               n["moon_nakshatra"], n["moon_sign"], ctx.lang, profile.ayanamsa)
        results = jsonable(results, ctx.tz)
        cache.set(cache_key, results, 60 * 30)
    return {"activity": activity_meta(activity, ctx.lang), "range": range_key,
            "range_label": RANGES[range_key][1 if ctx.lang == "hi" else 0], "results": results,
            "location": {"label": ctx.place_label}}


# --- Transits ---------------------------------------------------------------------------
def transits(ctx: DayContext) -> dict:
    profile = ctx.profile
    n = natal(profile)
    report = tr.transit_report(n["ref_sign"], n["moon_sign"], ctx.now, profile.ayanamsa)
    return jsonable({"at": ctx.now, "planets": report,
                     "sade_sati": tr.sade_sati(n["moon_sign"], ctx.now, profile.ayanamsa)}, ctx.tz)
