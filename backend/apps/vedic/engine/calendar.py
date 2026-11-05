"""Festival calendar: the Ekadashis and festivals of a civil month.

Each observance is fixed by the tithi in force at a deciding moment of the day: sunrise for most
(udaya tithi), midday for Ram Navami and Ganesh Chaturthi, the afternoon (aparahna) for Dussehra and
Bhai Dooj, sunset for Dhanteras, Holika Dahan, Diwali, Sharad Purnima and Ahoi Ashtami, local
midnight for Maha Shivaratri and Janmashtami, moonrise for Karva Chauth. A tithi in force at two such
moments (vriddhi) counts on the first day; one that no moment sees (kshaya) counts on the day it
begins. Bhadra and other finer rules are not modelled, so a published panchang can differ by a day
at the edges. Months are amanta (a festival kept in a purnimanta Krishna paksha sits in the amanta
month before); festivals are skipped in an adhika month, and Ekadashis there take the adhika names.
Makar Sankranti is the local date of the Sun's sidereal ingress into Makara.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import ephemeris as ephem
from .panchang import _elongation, _events, lunar_month, tithi_name
from .transits import ingresses

MOMENTS = ("sunrise", "midday", "aparahna", "sunset", "midnight", "moonrise")

# The Ekadashis, every lunar month: key -> (0-based tithi, moment). Each carries its month, which names it.
EKADASHI = {
    "ekadashi_shukla": (10, "sunrise"),
    "ekadashi_krishna": (25, "sunrise"),
}

# key -> (amanta month, 0-based tithi, moment); None for a solar festival (see `month_calendar`).
FESTIVALS = {
    "makar_sankranti": None,
    "vasant_panchami": ("Magha", 4, "sunrise"),
    "maha_shivaratri": ("Magha", 28, "midnight"),
    "holika_dahan": ("Phalguna", 14, "sunset"),
    "holi": ("Phalguna", 15, "sunrise"),
    "chaitra_navratri": ("Chaitra", 0, "sunrise"),  # with Gudi Padwa / Ugadi
    "ram_navami": ("Chaitra", 8, "midday"),
    "hanuman_jayanti": ("Chaitra", 14, "sunrise"),
    "akshaya_tritiya": ("Vaishakha", 2, "sunrise"),
    "buddha_purnima": ("Vaishakha", 14, "sunrise"),
    "vat_savitri": ("Vaishakha", 29, "sunrise"),  # Jyeshtha Amavasya, purnimanta
    "guru_purnima": ("Ashadha", 14, "sunrise"),
    "hariyali_teej": ("Shravana", 2, "sunrise"),
    "nag_panchami": ("Shravana", 4, "sunrise"),
    "raksha_bandhan": ("Shravana", 14, "sunrise"),
    "janmashtami": ("Shravana", 22, "midnight"),  # Bhadrapada Krishna Ashtami, purnimanta
    "hartalika_teej": ("Bhadrapada", 2, "sunrise"),
    "ganesh_chaturthi": ("Bhadrapada", 3, "midday"),
    "navratri": ("Ashwin", 0, "sunrise"),
    "dussehra": ("Ashwin", 9, "aparahna"),
    "sharad_purnima": ("Ashwin", 14, "sunset"),
    "karva_chauth": ("Ashwin", 18, "moonrise"),  # Kartika Krishna Chaturthi, purnimanta
    "ahoi_ashtami": ("Ashwin", 22, "sunset"),
    "dhanteras": ("Ashwin", 27, "sunset"),
    "narak_chaturdashi": ("Ashwin", 28, "sunrise"),
    "diwali": ("Ashwin", 29, "sunset"),
    "govardhan_puja": ("Kartika", 0, "sunrise"),
    "bhai_dooj": ("Kartika", 1, "aparahna"),
    "chhath": ("Kartika", 5, "sunrise"),
    "kartik_purnima": ("Kartika", 14, "sunrise"),  # with Dev Deepawali
}
MAKARA = 9


def _tithi(dt: datetime) -> int:
    """0-based tithi (0 = Shukla Pratipada … 29 = Amavasya) at a moment. Independent of ayanamsa."""
    return int(_elongation(ephem.to_time(dt).tt, "lahiri") // 12.0) % 30


def _first_after(events: list[datetime], start: datetime, end: datetime) -> datetime | None:
    return next((e for e in events if start <= e < end), None)


def _moments(days: list[date], lat: float, lon: float, tz: ZoneInfo) -> list[dict]:
    """Sunrise, midday, aparahna (in the fourth fifth of daylight), sunset, the following local
    midnight and moonrise (or None) of each civil day."""
    start = datetime.combine(days[0] - timedelta(days=1), time(0), tzinfo=tz)
    end = datetime.combine(days[-1] + timedelta(days=2), time(0), tzinfo=tz)
    rises, sets = _events(lat, lon, start, end, "rise"), _events(lat, lon, start, end, "set")
    moonrises = _events(lat, lon, start, end, "rise", "moon")
    out = []
    for d in days:
        midnight = datetime.combine(d, time(0), tzinfo=tz)
        # Polar day/night: fall back to 06:00 / 18:00 local, as `panchang.sun_day` does.
        sunrise = _first_after(rises, midnight, midnight + timedelta(days=1)) or midnight + timedelta(hours=6)
        sunset = _first_after(sets, sunrise, sunrise + timedelta(days=1)) or sunrise + timedelta(hours=12)
        moonrise = _first_after(moonrises, sunrise, sunrise + timedelta(days=1))
        daylight = sunset - sunrise
        out.append({"sunrise": sunrise, "midday": sunrise + daylight / 2, "aparahna": sunrise + daylight * 0.7,
                    "sunset": sunset, "midnight": midnight + timedelta(days=1), "moonrise": moonrise})
    return out


def _days_of(values: list[int], target: int) -> list[int]:
    """Indexes of the days a tithi is observed, given the tithi at the deciding moment of each day.
    The first day only covers the lookbehind and is never returned."""
    out = []
    for i in range(1, len(values)):
        prev, cur = values[i - 1], values[i]
        if cur == target and prev != target:
            out.append(i)
        elif prev != target and cur != target and 0 < (target - prev) % 30 < (cur - prev) % 30:
            out.append(i - 1)  # kshaya: it began after day i-1's moment and ended before day i's
    return [i for i in out if i > 0]


def month_calendar(year: int, month: int, lat: float, lon: float, tz: ZoneInfo,
                   ayanamsa: str = "lahiri") -> list[dict]:
    """Each civil day of the month: sunrise, the tithi in force then, the amanta month and the
    observances (`{"key"}`; an Ekadashi also has `"month"` and `"is_adhika"`, which name it)."""
    first = date(year, month, 1)
    last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    span = [first - timedelta(days=1) + timedelta(days=i) for i in range((last - first).days + 3)]
    moments = _moments(span, lat, lon, tz)
    values = {m: [_tithi(x[m] or x["midnight"]) for x in moments] for m in MOMENTS}  # no moonrise: midnight

    # Amanta month at each sunrise; it only changes when the tithi wraps to Shukla.
    months, current = [], None
    for i, x in enumerate(moments):
        if current is None or values["sunrise"][i] < values["sunrise"][i - 1]:
            current = lunar_month(ephem.to_time(x["sunrise"]).tt, ayanamsa)
        months.append(current)

    found: dict[int, list[dict]] = {i: [] for i in range(len(span))}
    for key, (tithi, moment) in EKADASHI.items():
        for i in _days_of(values[moment], tithi):
            found[i].append({"key": key, "month": months[i]["amanta"], "is_adhika": months[i]["is_adhika"]})
    for key, rule in FESTIVALS.items():
        if rule is None:
            continue
        masa, tithi, moment = rule
        for i in _days_of(values[moment], tithi):
            # A new month's early tithi that began after this day's sunrise (kshaya at the new moon)
            # belongs to the month in force from the next sunrise.
            month = months[i + 1] if values["sunrise"][i] - tithi > 15 else months[i]
            if month["amanta"] == masa and not month["is_adhika"]:
                found[i].append({"key": key})

    utc_start = datetime.combine(first, time(0), tzinfo=tz)
    for ing in ingresses("Su", utc_start, utc_start + timedelta(days=(last - first).days + 1), ayanamsa):
        local = ing["at"].astimezone(tz).date()
        if ing["to_sign"] == MAKARA and first <= local <= last:
            found[span.index(local)].append({"key": "makar_sankranti"})

    out = []
    for i, d in enumerate(span):
        if not first <= d <= last:
            continue
        t = values["sunrise"][i]
        out.append({"date": d, "sunrise": moments[i]["sunrise"], "tithi": t + 1, "tithi_name": tithi_name(t),
                    "paksha": "Shukla" if t < 15 else "Krishna", "month": months[i]["amanta"],
                    "is_adhika": months[i]["is_adhika"], "observances": found[i]})
    return out
