"""Panchang: tithi, vara, nakshatra, yoga, karana + sunrise/sunset and lunar month."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from skyfield import almanac

from . import ephemeris as ephem
from .constants import (
    LUNAR_MONTHS, MOVABLE_KARANAS, NAKSHATRA_SPAN, NAKSHATRAS, NAKSHATRA_LORDS, PADA_SPAN,
    TITHI_NAMES, WEEKDAY_LORDS, WEEKDAYS, WEEKDAYS_SANSKRIT, YOGA_NAMES, SIGNS,
)
from .utils import norm


@dataclass
class SunDay:
    """The Vedic day (sunrise to next sunrise) containing a moment."""
    sunrise: datetime
    sunset: datetime
    next_sunrise: datetime
    prev_sunset: datetime
    is_day: bool
    civil_date: datetime  # local civil date of the sunrise (midnight, tz-aware)

    @property
    def weekday_index(self) -> int:
        """0 = Sunday."""
        return (self.civil_date.weekday() + 1) % 7


def _events(lat, lon, start: datetime, end: datetime, kind: str, body: str = "sun"):
    ts = ephem.timescale()
    obs = ephem.observer(lat, lon)
    target = ephem.ephemeris()[body]
    fn = almanac.find_risings if kind == "rise" else almanac.find_settings
    times, ok = fn(obs, target, ts.from_datetime(start), ts.from_datetime(end))
    return [t.utc_datetime() for t, y in zip(times, ok) if y]


def sun_day(dt: datetime, lat: float, lon: float, tz: ZoneInfo) -> SunDay:
    local = dt.astimezone(tz)
    midnight = datetime.combine(local.date(), time(0), tzinfo=tz)
    start, end = midnight - timedelta(days=1), midnight + timedelta(days=2)
    rises = _events(lat, lon, start, end, "rise")
    sets = _events(lat, lon, start, end, "set")
    if not rises or not sets:  # polar day/night: fall back to 06:00 / 18:00 local
        rises = [midnight + timedelta(days=k, hours=6) for k in (-1, 0, 1)]
        sets = [midnight + timedelta(days=k, hours=18) for k in (-1, 0, 1)]

    sunrise = max((r for r in rises if r <= dt), default=rises[0])
    next_sunrise = min((r for r in rises if r > dt), default=sunrise + timedelta(days=1))
    sunset = min((s for s in sets if s > sunrise), default=sunrise + timedelta(hours=12))
    prev_sunset = max((s for s in sets if s <= sunrise), default=sunset - timedelta(days=1))
    civil = datetime.combine(sunrise.astimezone(tz).date(), time(0), tzinfo=tz)
    return SunDay(sunrise=sunrise, sunset=sunset, next_sunrise=next_sunrise,
                  prev_sunset=prev_sunset, is_day=sunrise <= dt < sunset, civil_date=civil)


# --- angle functions of time (jd TT) ---------------------------------------------------

def _angles(jd_tt: float, ayanamsa_name: str):
    t = ephem.timescale().tt_jd(jd_tt)
    sun, moon = ephem.sun_moon_tropical(t)
    ay = ephem.true_ayanamsa(t, ayanamsa_name)
    return float(sun), float(moon), ay


def _elongation(jd, ay_name):
    s, m, _ = _angles(jd, ay_name)
    return norm(m - s)


def _moon_sid(jd, ay_name):
    _, m, ay = _angles(jd, ay_name)
    return norm(m - ay)


def _yoga_sum(jd, ay_name):
    s, m, ay = _angles(jd, ay_name)
    return norm(s + m - 2 * ay)


def _find_crossing(fn, target: float, jd_guess: float, rate: float, ay_name: str) -> float:
    """Solve fn(jd) == target (mod 360) near jd_guess with a damped Newton iteration."""
    jd = jd_guess
    for _ in range(12):
        diff = ((target - fn(jd, ay_name) + 180.0) % 360.0) - 180.0
        if abs(diff) < 1e-6:
            break
        jd += diff / rate
    return jd


def _span_times(fn, value: float, unit: float, rate: float, jd: float, ay_name: str):
    start_val = (value // unit) * unit
    end_val = start_val + unit
    start = _find_crossing(fn, start_val, jd - (value - start_val) / rate, rate, ay_name)
    end = _find_crossing(fn, norm(end_val), jd + (end_val - value) / rate, rate, ay_name)
    ts = ephem.timescale()
    return ts.tt_jd(start).utc_datetime(), ts.tt_jd(end).utc_datetime()


def karana_name(k: int) -> str:
    if k == 0:
        return "Kimstughna"
    if k >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][k - 57]
    return MOVABLE_KARANAS[(k - 1) % 7]


def tithi_name(i: int) -> str:
    if i == 14:
        return "Purnima"
    if i == 29:
        return "Amavasya"
    return TITHI_NAMES[i % 15]


def lunar_month(jd_tt: float, ay_name: str) -> dict:
    """Amanta lunar month: named after the Sun's sign at the preceding new moon."""
    elong = _elongation(jd_tt, ay_name)
    prev_nm = _find_crossing(_elongation, 0.0, jd_tt - elong / 12.19, 12.19, ay_name)
    next_nm = _find_crossing(_elongation, 0.0, prev_nm + 29.53, 12.19, ay_name)
    ts = ephem.timescale()
    s1 = int(ephem.sidereal_lon("Su", ts.tt_jd(prev_nm), ay_name) // 30)
    s2 = int(ephem.sidereal_lon("Su", ts.tt_jd(next_nm), ay_name) // 30)
    return {
        "amanta": LUNAR_MONTHS[(s1 + 1) % 12],
        "is_adhika": s1 == s2,
        "new_moon_start": ts.tt_jd(prev_nm).utc_datetime(),
        "new_moon_end": ts.tt_jd(next_nm).utc_datetime(),
    }


def compute_panchang(dt: datetime, lat: float, lon: float, tz: ZoneInfo,
                     sun_lon: float, moon_lon: float, sun_tropical: float,
                     ayanamsa_name: str = "lahiri", day: SunDay | None = None) -> dict:
    """Panchang for a moment. ``sun_lon``/``moon_lon`` are sidereal longitudes."""
    jd = ephem.to_time(dt).tt
    day = day or sun_day(dt, lat, lon, tz)

    elong = norm(moon_lon - sun_lon)
    t_idx = int(elong // 12)
    t_start, t_end = _span_times(_elongation, elong, 12.0, 12.19, jd, ayanamsa_name)

    n_idx = int(moon_lon // NAKSHATRA_SPAN)
    n_start, n_end = _span_times(_moon_sid, moon_lon, NAKSHATRA_SPAN, 13.18, jd, ayanamsa_name)

    ysum = norm(sun_lon + moon_lon)
    y_idx = int(ysum // NAKSHATRA_SPAN)
    y_start, y_end = _span_times(_yoga_sum, ysum, NAKSHATRA_SPAN, 14.17, jd, ayanamsa_name)

    k_idx = int(elong // 6)
    k_start, k_end = _span_times(_elongation, elong, 6.0, 12.19, jd, ayanamsa_name)

    wd = day.weekday_index
    moonrise = _events(lat, lon, day.sunrise, day.next_sunrise, "rise", "moon")
    moonset = _events(lat, lon, day.sunrise, day.next_sunrise, "set", "moon")
    trop_sun = norm(sun_tropical)

    return {
        "tithi": {
            "index": t_idx + 1,
            "name": tithi_name(t_idx),
            "paksha": "Shukla" if t_idx < 15 else "Krishna",
            "fraction_elapsed": (elong % 12) / 12,
            "start": t_start, "end": t_end,
        },
        "vara": {
            "index": wd + 1,
            "name": WEEKDAYS[wd],
            "sanskrit": WEEKDAYS_SANSKRIT[wd],
            "lord": WEEKDAY_LORDS[wd],
        },
        "nakshatra": {
            "index": n_idx + 1,
            "name": NAKSHATRAS[n_idx],
            "pada": int((moon_lon % NAKSHATRA_SPAN) // PADA_SPAN) + 1,
            "lord": NAKSHATRA_LORDS[n_idx],
            "fraction_elapsed": (moon_lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN,
            "start": n_start, "end": n_end,
        },
        "yoga": {"index": y_idx + 1, "name": YOGA_NAMES[y_idx], "start": y_start, "end": y_end},
        "karana": {"index": k_idx + 1, "name": karana_name(k_idx), "start": k_start, "end": k_end},
        "sun_sign": SIGNS[int(sun_lon // 30)],
        "moon_sign": SIGNS[int(moon_lon // 30)],
        "lunar_month": lunar_month(jd, ayanamsa_name),
        "ayana": "Uttarayana" if (trop_sun >= 270 or trop_sun < 90) else "Dakshinayana",
        "sunrise": day.sunrise,
        "sunset": day.sunset,
        "next_sunrise": day.next_sunrise,
        "moonrise": moonrise[0] if moonrise else None,
        "moonset": moonset[0] if moonset else None,
        "is_day_birth": day.is_day,
        "day_duration_hours": (day.sunset - day.sunrise).total_seconds() / 3600,
        "night_duration_hours": (day.next_sunrise - day.sunset).total_seconds() / 3600,
    }
