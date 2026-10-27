"""Daily companion features: home, day timeline, panchang, decisions, transits."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from django.core.cache import cache

from apps.vedic import services as vedic
from apps.vedic.content import insight as insight_text
from apps.vedic.content import panchang as pc
from apps.vedic.content import sky as sky_text
from apps.vedic.content.activities import RANGES, activity_meta
from apps.vedic.content.common import KIND_LABEL, nakshatra_name, yoga_name
from apps.vedic.content.muhurta import period_text
from apps.vedic.engine import transits as tr
from apps.vedic.engine.attributes import is_combust
from apps.vedic.engine.chart import compute_day_panchang, jsonable
from apps.vedic.engine.constants import (
    DEBILITATION, EXALTATION, GANDMOOL_NAKSHATRAS, NAKSHATRA_SPAN, NAKSHATRAS, PADA_SPAN, SIGNS, SIGNS_SANSKRIT,
)
from apps.vedic.engine.decision import rank_windows
from apps.vedic.engine.muhurta import compute_muhurtas, find
from apps.vedic.engine.panchang import tithi_name

from .context import DayContext

GOOD_FROM_MOON = {1, 3, 6, 7, 10, 11}
UTC = timezone.utc


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
        "now": right_now(ctx) if ctx.is_today else None,
        "sky": sky(ctx, n, positions),
    }, ctx.tz)


# Each period's traditional ruling graha, shown as its glyph on the "Right now" card.
_PERIOD_GLYPH = {
    "choghadiya.amrit": "☽", "choghadiya.shubh": "♃", "choghadiya.labh": "☿", "choghadiya.char": "♀",
    "choghadiya.udveg": "☉", "choghadiya.kaal": "♄", "choghadiya.rog": "♂",
    "rahu_kaal": "☊", "yamaganda": "♃", "gulika": "♄", "abhijit": "☉", "brahma": "☽",
}
# When periods overlap, the one to show: a kaal first, then a muhurta, then the choghadiya.
_PRIORITY = {"kaal": 0, "muhurta": 1, "choghadiya": 2}


def right_now(ctx: DayContext) -> dict | None:
    """The period in force now (Rahu Kaal over the choghadiya under it, and so on), how far
    through it we are, and what comes next."""
    periods = []
    for offset in (-1, 0, 1):  # before sunrise we are still in yesterday's night; near its end, tomorrow's
        mu = compute_muhurtas(ctx.day + timedelta(days=offset), ctx.lat, ctx.lon, ctx.tz)
        wd = mu["weekday"]
        periods += [(p, wd) for p in mu["periods"] if p.category in _PRIORITY]
    def active_at(t):
        live = [pw for pw in periods if pw[0].start <= t < pw[0].end]
        return min(live, key=lambda pw: (_PRIORITY[pw[0].category], pw[0].start), default=None)

    current = active_at(ctx.now)
    if current is None:
        return None
    p, wd = current
    # Next is what this card will show at the next change: when this period ends, or earlier if a
    # higher-priority period (e.g. Abhijit over a choghadiya) starts before then.
    change = min([p.end] + [q.start for q, _ in periods
                            if ctx.now < q.start < p.end and _PRIORITY[q.category] < _PRIORITY[p.category]])
    nxt = active_at(change)

    def named(period, weekday) -> str:
        key = _abhijit_key(period, weekday) if period.key == "abhijit" else period.key
        return period_text(key, ctx.lang)["name"]

    span = (p.end - p.start).total_seconds()
    return {
        "key": p.key, "name": named(p, wd), "kind": p.kind, "kind_label": _kind_label(p.kind, ctx.lang),
        "glyph": _PERIOD_GLYPH.get(p.key, "◈"), "start": p.start, "end": p.end,
        "progress": round(min(1.0, max(0.0, (ctx.now - p.start).total_seconds() / span)), 3) if span else 0,
        "next": {"name": named(*nxt), "start": nxt[0].start, "kind": nxt[0].kind} if nxt else None,
    }


def sky(ctx: DayContext, n: dict, positions: dict) -> dict:
    """Every graha now: sign and degree, nakshatra, house from the lagna, dignity, retrograde and
    combust, plus advice for each retrograde / combust one and until when.

    Positions are live (`positions` at ctx.now); the retrograde / combust spans need a look ahead
    and are cached per hour."""
    ayanamsa = ctx.profile.ayanamsa
    hour = ctx.now.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    states = {p["planet"]: p for p in cache.get_or_set(
        f"sky:{ayanamsa}:{hour:%Y%m%d%H}", lambda: tr.sky_now(hour, ayanamsa), 2 * 3600)}
    planets = []
    for code, pos in positions.items():
        st = states[code]
        lon, sign = pos["lon"], pos["sign"]
        nak = int(lon // NAKSHATRA_SPAN)
        house = tr.house(sign, n["ref_sign"])
        dignity = "exalted" if EXALTATION[code][0] == sign else "debilitated" if DEBILITATION[code][0] == sign else None
        active = {
            "retrograde": st["retrograde"] or code in ("Ra", "Ke"),  # the nodes always move backwards
            "exalted": dignity == "exalted", "debilitated": dignity == "debilitated", "combust": st["combust"],
            "gandmool": nak in GANDMOOL_NAKSHATRAS,
        }
        guide = []
        for cond in sky_text.CONDITIONS:
            text = active[cond] and sky_text.guide(code, cond, house, ctx.lang, nakshatra=nak)
            if text:
                # Retrograde / combust spells end; the nodes' motion and a sign placement don't.
                until = st.get(f"{cond}_until") if cond in ("retrograde", "combust") and st[cond] else None
                guide.append({"condition": cond, **text, "until": until})
        planets.append({
            "planet": code, "sign": SIGNS[sign], "sign_sanskrit": SIGNS_SANSKRIT[sign], "degree": lon % 30,
            "nakshatra": NAKSHATRAS[nak], "pada": int((lon % NAKSHATRA_SPAN) // PADA_SPAN) + 1,
            "house": house, "dignity": dignity, "retrograde": active["retrograde"], "combust": active["combust"],
            "gandmool": active["gandmool"],
            # What to do and avoid for each condition the graha is in (shown when its row is opened).
            "guide": guide,
        })
    return {
        "planets": planets,
        # What the houses are counted from: the lagna, or the Moon sign when the birth time is unknown.
        "reference": {"basis": "lagna" if ctx.profile.time_known else "moon", "sign": SIGNS[n["ref_sign"]],
                      "ayanamsa": ayanamsa},
    }


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
