"""Daily muhurta timings: Rahu Kaal, Yamaganda, Gulika, Abhijit, Brahma muhurta
and day/night Choghadiya, all derived from local sunrise/sunset."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .panchang import SunDay, sun_day

GOOD, NEUTRAL, BAD = "good", "neutral", "bad"

# Weekday index: 0 = Sunday. Values are the 1-based eighth of daytime.
RAHU_KAAL = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
YAMAGANDA = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
GULIKA = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}

CHOGHADIYA_KIND = {
    "amrit": GOOD, "shubh": GOOD, "labh": GOOD, "char": NEUTRAL,
    "udveg": BAD, "kaal": BAD, "rog": BAD,
}
_DAY_ORDER = ["udveg", "char", "labh", "amrit", "kaal", "shubh", "rog"]
_DAY_START = {0: "udveg", 1: "amrit", 2: "rog", 3: "labh", 4: "shubh", 5: "char", 6: "kaal"}
_NIGHT_ORDER = ["shubh", "amrit", "char", "rog", "kaal", "labh", "udveg"]
_NIGHT_START = {0: "shubh", 1: "char", 2: "kaal", 3: "udveg", 4: "amrit", 5: "rog", 6: "labh"}


@dataclass(frozen=True)
class Period:
    key: str          # e.g. "rahu_kaal", "choghadiya.amrit", "abhijit"
    category: str     # "kaal" | "choghadiya" | "muhurta" | "marker"
    kind: str         # good | neutral | bad
    start: datetime
    end: datetime
    part: str = "day"  # day | night

    def to_dict(self) -> dict:
        return {"key": self.key, "category": self.category, "kind": self.kind, "part": self.part,
                "start": self.start, "end": self.end}

    def overlaps(self, start: datetime, end: datetime) -> bool:
        return self.start < end and start < self.end


def _eighths(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    step = (end - start) / 8
    return [(start + step * i, start + step * (i + 1)) for i in range(8)]


def _sequence(order: list[str], first: str) -> list[str]:
    i = order.index(first)
    return [order[(i + k) % 7] for k in range(8)]


def day_for(d: date, lat: float, lon: float, tz: ZoneInfo) -> SunDay:
    """The Vedic day whose sunrise falls on civil date ``d``."""
    return sun_day(datetime.combine(d, time(12, 0), tzinfo=tz), lat, lon, tz)


def compute_muhurtas(d: date, lat: float, lon: float, tz: ZoneInfo) -> dict:
    day = day_for(d, lat, lon, tz)
    wd = day.weekday_index
    day_parts = _eighths(day.sunrise, day.sunset)
    night_parts = _eighths(day.sunset, day.next_sunrise)

    periods: list[Period] = []
    for key, table in (("rahu_kaal", RAHU_KAAL), ("yamaganda", YAMAGANDA), ("gulika", GULIKA)):
        s, e = day_parts[table[wd] - 1]
        periods.append(Period(key, "kaal", BAD if key != "gulika" else NEUTRAL, s, e))

    day_len = day.sunset - day.sunrise
    midday = day.sunrise + day_len / 2
    muhurta = day_len / 15
    # Abhijit is traditionally not used on Wednesdays.
    periods.append(Period("abhijit", "muhurta", NEUTRAL if wd == 3 else GOOD,
                          midday - muhurta / 2, midday + muhurta / 2))

    prev_night = day.sunrise - day.prev_sunset
    night_muhurta = prev_night / 15
    periods.append(Period("brahma", "muhurta", GOOD, day.sunrise - 2 * night_muhurta,
                          day.sunrise - night_muhurta, part="dawn"))

    for (s, e), name in zip(day_parts, _sequence(_DAY_ORDER, _DAY_START[wd])):
        periods.append(Period(f"choghadiya.{name}", "choghadiya", CHOGHADIYA_KIND[name], s, e))
    for (s, e), name in zip(night_parts, _sequence(_NIGHT_ORDER, _NIGHT_START[wd])):
        periods.append(Period(f"choghadiya.{name}", "choghadiya", CHOGHADIYA_KIND[name], s, e, part="night"))

    periods.sort(key=lambda p: (p.start, p.category != "kaal"))
    return {"day": day, "weekday": wd, "periods": periods}


def kaal_periods(result: dict) -> list[Period]:
    return [p for p in result["periods"] if p.category == "kaal" and p.kind == BAD]


def find(result: dict, key: str) -> Period | None:
    return next((p for p in result["periods"] if p.key == key), None)
