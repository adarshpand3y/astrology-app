"""Transits (gochara) relative to a natal chart: current positions, sign ingresses,
Sade Sati and the time a planet culminates (peaks) at a location."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np
from skyfield import almanac
from skyfield.framelib import ecliptic_frame
from skyfield.nutationlib import iau2000a_radians

from . import ayanamsa as ayan
from . import ephemeris as ephem
from .constants import JU, KE, MA, ME, MO, RA, SA, SU, VE
from .utils import norm

UTC = timezone.utc

# Classical gochara: favourable houses counted from the natal Moon.
GOCHARA_GOOD = {
    SU: {3, 6, 10, 11}, MO: {1, 3, 6, 7, 10, 11}, MA: {3, 6, 11}, ME: {2, 4, 6, 8, 10, 11},
    JU: {2, 5, 7, 9, 11}, VE: {1, 2, 3, 4, 5, 8, 9, 11, 12}, SA: {3, 6, 11}, RA: {3, 6, 11}, KE: {3, 6, 11},
}
# Typical days per sign, used to pick sensible search steps and "freshness".
SIGN_DAYS = {SU: 30, MO: 2.3, MA: 45, ME: 25, JU: 365, VE: 26, SA: 900, RA: 540, KE: 540}


def _lons(code: str, jd_tt: np.ndarray, ayanamsa_name: str = "lahiri") -> np.ndarray:
    """Vectorised sidereal longitudes for many TT Julian dates."""
    ts = ephem.timescale()
    t = ts.tt_jd(jd_tt)
    dpsi = np.degrees(iau2000a_radians(t)[0])
    mean_ay = ayan.mean_ayanamsa(ayanamsa_name, jd_tt)
    if code in (RA, KE):
        tc = (jd_tt - ayan.J2000) / 36525.0
        node = (125.0445479 - 1934.1362891 * tc + 0.0020754 * tc**2) % 360.0
        lon = (node - mean_ay) % 360.0
        return (lon + 180.0) % 360.0 if code == KE else lon
    eph = ephem.ephemeris()
    body = eph[ephem._BODY_KEYS[code]]
    _, elon, _ = eph["earth"].at(t).observe(body).apparent().frame_latlon(ecliptic_frame)
    return (elon.degrees - mean_ay - dpsi) % 360.0


def _jd(dt: datetime) -> float:
    return ephem.to_time(dt).tt


def _dt(jd_tt: float) -> datetime:
    return ephem.timescale().tt_jd(jd_tt).utc_datetime()


def positions(dt: datetime, ayanamsa_name: str = "lahiri") -> dict[str, dict]:
    """Sidereal longitude and daily speed of all grahas at ``dt``."""
    jd = _jd(dt)
    out = {}
    for code in (SU, MO, MA, ME, JU, VE, SA, RA, KE):
        l3 = _lons(code, np.array([jd - 0.5, jd, jd + 0.5]), ayanamsa_name)
        speed = ((l3[2] - l3[0] + 180) % 360) - 180
        out[code] = {"lon": float(l3[1]), "sign": int(l3[1] // 30), "speed": float(speed),
                     "retrograde": bool(code in (RA, KE) or speed < 0)}
    return out


def _refine(code: str, jd_a: float, jd_b: float, ayanamsa_name: str) -> float:
    """Bisect the sign change between two dates (sign differs at the ends)."""
    sa = int(_lons(code, np.array([jd_a]), ayanamsa_name)[0] // 30)
    for _ in range(40):
        mid = (jd_a + jd_b) / 2
        if int(_lons(code, np.array([mid]), ayanamsa_name)[0] // 30) == sa:
            jd_a = mid
        else:
            jd_b = mid
        if jd_b - jd_a < 1 / 96:  # 15 minutes is plenty for display
            break
    return jd_b


def ingresses(code: str, start: datetime, end: datetime, ayanamsa_name: str = "lahiri") -> list[dict]:
    """All sign changes of ``code`` between start and end (UTC datetimes)."""
    step = 0.05 if code == MO else min(1.0, SIGN_DAYS[code] / 30)
    a, b = _jd(start), _jd(end)
    grid = np.arange(a, b + step, step)
    signs = (_lons(code, grid, ayanamsa_name) // 30).astype(int)
    out = []
    for i in np.nonzero(signs[1:] != signs[:-1])[0]:
        jd = _refine(code, grid[i], grid[i + 1], ayanamsa_name)
        out.append({"planet": code, "at": _dt(jd), "from_sign": int(signs[i]), "to_sign": int(signs[i + 1])})
    return out


def last_ingress(code: str, dt: datetime, ayanamsa_name: str = "lahiri") -> datetime | None:
    span = timedelta(days=SIGN_DAYS[code] * 1.3 + 5)
    found = ingresses(code, dt - span, dt, ayanamsa_name)
    return found[-1]["at"] if found else None


def sade_sati(moon_sign: int, dt: datetime, ayanamsa_name: str = "lahiri") -> dict:
    """Saturn's passage through the 12th, 1st and 2nd signs from the natal Moon."""
    target = {(moon_sign - 1) % 12: "rising", moon_sign: "peak", (moon_sign + 1) % 12: "setting"}
    a, b = _jd(dt - timedelta(days=365 * 9)), _jd(dt + timedelta(days=365 * 30))
    grid = np.arange(a, b, 5.0)
    signs = (_lons(SA, grid, ayanamsa_name) // 30).astype(int)
    inside = np.isin(signs, list(target))

    runs, start = [], None
    for i, flag in enumerate(inside):
        if flag and start is None:
            start = i
        if not flag and start is not None:
            runs.append([start, i - 1])
            start = None
    if start is not None:
        runs.append([start, len(inside) - 1])
    merged = []
    for r in runs:  # merge retrograde dips shorter than ~400 days
        if merged and (r[0] - merged[-1][1]) * 5 < 400:
            merged[-1][1] = r[1]
        else:
            merged.append(r)

    now = _jd(dt)
    sign_now = int(_lons(SA, np.array([now]), ayanamsa_name)[0] // 30)
    current = next((r for r in merged if grid[r[0]] <= now <= grid[r[1]]), None)
    upcoming = next((r for r in merged if grid[r[0]] > now), None)

    def span(r):
        return {"start": _dt(float(grid[r[0]])), "end": _dt(float(grid[r[1]]))} if r else None

    return {
        "active": current is not None,
        "phase": target.get(sign_now) if current else None,
        "current": span(current),
        "next": span(upcoming),
    }


def culmination(code: str, day_start: datetime, lat: float, lon: float) -> datetime | None:
    """Time the planet crosses the local meridian (highest point) within 24h."""
    if code in (RA, KE):
        return None
    ts = ephem.timescale()
    eph = ephem.ephemeris()
    t0, t1 = ts.from_datetime(day_start), ts.from_datetime(day_start + timedelta(days=1))
    times = almanac.find_transits(ephem.observer(lat, lon), eph[ephem._BODY_KEYS[code]], t0, t1)
    return times[0].utc_datetime() if len(times) else None


def house(sign: int, ref_sign: int) -> int:
    return (sign - ref_sign) % 12 + 1


def transit_report(natal_lagna_sign: int, natal_moon_sign: int, dt: datetime,
                   ayanamsa_name: str = "lahiri") -> list[dict]:
    """Current transit of each graha with houses from Lagna and Moon."""
    pos = positions(dt, ayanamsa_name)
    out = []
    for code, p in pos.items():
        from_moon = house(p["sign"], natal_moon_sign)
        out.append({
            "planet": code, "lon": p["lon"], "sign": p["sign"], "retrograde": p["retrograde"],
            "house": house(p["sign"], natal_lagna_sign), "house_from_moon": from_moon,
            "favourable": bool(from_moon in GOCHARA_GOOD[code]),
        })
    return out


def headline_transit(report: list[dict], dt: datetime, ayanamsa_name: str = "lahiri") -> dict:
    """Pick the most notable current transit: the freshest ingress among the
    slower, more influential grahas."""
    weights = {MA: 1.0, JU: 1.3, SA: 1.4, RA: 1.1, SU: 0.8, VE: 0.7, ME: 0.6}
    best, best_score = None, -math.inf
    for r in report:
        code = r["planet"]
        if code not in weights:
            continue
        entered = last_ingress(code, dt, ayanamsa_name)
        age = (dt - entered).total_seconds() / 86400 if entered else SIGN_DAYS[code]
        freshness = 1 - min(age / SIGN_DAYS[code], 1)
        score = weights[code] * (0.4 + freshness)
        if score > best_score:
            best, best_score = {**r, "entered_at": entered, "days_since": age}, score
    return best


# --- Retrograde & combust right now ---------------------------------------------------
_LOOKAHEAD_DAYS = 240  # longer than any retrograde (Saturn ~140 days) or combustion spell
_STEP_DAYS = 0.25


def sky_now(dt: datetime, ayanamsa_name: str = "lahiri") -> list[dict]:
    """Every graha's sign now, whether it is retrograde or combust, and when that ends.

    Rahu and Ketu always move backwards, so they are never reported as retrograde here.
    Combustion uses the BPHS orbs (tighter for a retrograde Mercury or Venus). End times come
    from a 6-hour grid, which is plenty for showing a date."""
    from .attributes import is_combust  # local import: attributes imports from the engine too

    jd = _jd(dt)
    grid = jd + np.arange(0, _LOOKAHEAD_DAYS + _STEP_DAYS, _STEP_DAYS)
    sun = _lons(SU, grid, ayanamsa_name)
    out = []
    for code in (SU, MO, MA, ME, JU, VE, SA, RA, KE):
        lons = _lons(code, grid, ayanamsa_name)
        speed = ((np.roll(lons, -1) - lons + 180) % 360) - 180  # degrees per step, forward difference
        speed[-1] = speed[-2]
        nodes = code in (RA, KE)
        retro = (speed < 0) & (not nodes)
        combust = np.array([code not in (SU, RA, KE) and is_combust(code, l, s, bool(r))
                            for l, s, r in zip(lons, sun, retro)])

        def until(flags):
            if not flags[0]:
                return None
            ends = np.nonzero(~flags)[0]
            return _dt(float(grid[ends[0]])) if len(ends) else None

        out.append({
            "planet": code, "lon": float(lons[0]), "sign": int(lons[0] // 30),
            "retrograde": bool(retro[0]), "retrograde_until": until(retro),
            "combust": bool(combust[0]), "combust_until": until(combust),
        })
    return out
