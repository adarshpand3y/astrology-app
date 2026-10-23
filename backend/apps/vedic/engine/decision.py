"""Decision assistant: rank auspicious windows for an activity against a birth chart."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from ..content import activities as A
from ..content.common import nakshatra_name
from ..content.muhurta import period_text
from ..content.panchang import tithi_kind
from . import ephemeris as ephem
from .constants import NAKSHATRA_SPAN, NAKSHATRAS
from .muhurta import compute_muhurtas, kaal_periods
from .transits import _lons, positions

CANDIDATES = {"choghadiya.amrit": 20, "abhijit": 18, "choghadiya.shubh": 16,
              "choghadiya.labh": 16, "choghadiya.char": 10}
MIN_CLEAR = timedelta(minutes=24)


def _clear_segment(start: datetime, end: datetime, bad) -> tuple[datetime, datetime] | None:
    """Largest part of [start, end) not covered by any bad period."""
    segs = [(start, end)]
    for b in bad:
        nxt = []
        for s, e in segs:
            if b.end <= s or b.start >= e:
                nxt.append((s, e))
                continue
            if s < b.start:
                nxt.append((s, b.start))
            if b.end < e:
                nxt.append((b.end, e))
        segs = nxt
    return max(segs, key=lambda x: x[1] - x[0]) if segs else None


def rank_windows(activity: str, start_day: date, days: int, now: datetime, lat: float, lon: float,
                 tz: ZoneInfo, birth_nakshatra: int, birth_moon_sign: int, lang: str = "en",
                 ayanamsa_name: str = "lahiri", limit: int = 6) -> list[dict]:
    """birth_nakshatra: 1..27; birth_moon_sign: 0..11."""
    cands = []
    for i in range(days):
        d = start_day + timedelta(days=i)
        mu = compute_muhurtas(d, lat, lon, tz)
        bad = kaal_periods(mu)
        for p in mu["periods"]:
            if p.key not in CANDIDATES or p.kind != "good" or p.part != "day":
                continue
            if p.end <= now:
                continue
            seg = _clear_segment(max(p.start, now), p.end, bad)
            overlap = seg is None or (seg[1] - seg[0]) < MIN_CLEAR
            if overlap:
                seg = (max(p.start, now), p.end)
            cands.append({"period": p, "start": seg[0], "end": seg[1], "weekday": mu["weekday"],
                          "overlap": overlap, "bad": bad})
    if not cands:
        return []

    mids = np.array([ephem.to_time(c["start"] + (c["end"] - c["start"]) / 2).tt for c in cands])
    moon = _lons("Mo", mids, ayanamsa_name)
    sun = _lons("Su", mids, ayanamsa_name)
    key_planet = A.KEY_PLANET.get(activity)
    retro_cache: dict[date, bool] = {}

    results = []
    for c, m, s in zip(cands, moon, sun):
        p = c["period"]
        factors: list[tuple[float, str]] = []
        name = period_text(p.key, lang)["name"]
        base = CANDIDATES[p.key] + (6 if A.WINDOW_BONUS.get(activity) == p.key else 0)
        factors.append((base, A.factor_phrase("window", lang, name=name)))

        nak = int(m // NAKSHATRA_SPAN) + 1
        count = (nak - birth_nakshatra) % 27
        tara = count % 9
        factors.append((A.TARA_SCORE[tara], A.factor_phrase("tara", lang, tara=tara)))

        moon_house = (int(m // 30) - birth_moon_sign) % 12 + 1
        good_ch = moon_house in (1, 3, 6, 7, 10, 11)
        factors.append((8 if good_ch else -8, A.factor_phrase("chandra", lang, house=moon_house, good=good_ch)))

        tithi_index = int(((m - s) % 360) // 12) + 1
        t_bad = tithi_kind(tithi_index) == "bad"
        factors.append((-10 if t_bad else 3, A.factor_phrase("tithi", lang, bad=t_bad)))

        nak_name = nakshatra_name(nak, NAKSHATRAS[nak - 1], lang)
        if nak in A.GOOD_NAK[activity]:
            factors.append((10, A.factor_phrase("nakshatra", lang, name=nak_name, good=True)))
        elif nak in A.BAD_NAK:
            factors.append((-10, A.factor_phrase("nakshatra", lang, name=nak_name, good=False)))

        wd = c["weekday"]
        if wd in A.GOOD_DAYS[activity]:
            factors.append((6, A.factor_phrase("weekday", lang, weekday=wd, good=True)))
        elif wd in A.BAD_DAYS[activity]:
            factors.append((-8, A.factor_phrase("weekday", lang, weekday=wd, good=False)))

        if key_planet:
            day_key = c["start"].astimezone(tz).date()
            if day_key not in retro_cache:
                retro_cache[day_key] = positions(c["start"], ayanamsa_name)[key_planet]["retrograde"]
            if retro_cache[day_key]:
                factors.append((-12, A.factor_phrase("retro", lang, planet=key_planet)))

        if c["overlap"]:
            hit = next((b for b in c["bad"] if b.overlaps(c["start"], c["end"])), None)
            kname = period_text(hit.key, lang)["name"] if hit else ""
            factors.append((-40, A.factor_phrase("kaal", lang, name=kname)))

        score = int(max(1, min(99, round(40 + sum(v for v, _ in factors)))))
        kind = "good" if score >= 75 else "neutral" if score >= 50 else "bad"
        # Explain with the window name plus the strongest other factor in the score's direction.
        others = sorted(factors[1:], key=lambda f: -f[0] if kind != "bad" else f[0])
        reason = A.join_reason([factors[0][1]] + [o[1] for o in others[:1]], lang)
        results.append({"start": c["start"], "end": c["end"], "score": score, "kind": kind,
                        "window": p.key, "reason": reason})

    results.sort(key=lambda r: -r["score"])
    picked, per_day = [], {}
    for r in results:  # keep variety: at most two windows per day
        k = r["start"].astimezone(tz).date()
        if per_day.get(k, 0) >= 2:
            continue
        per_day[k] = per_day.get(k, 0) + 1
        picked.append(r)
        if len(picked) >= limit:
            break
    return picked
