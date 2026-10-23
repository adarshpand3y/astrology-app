"""Vimshottari dasha: Mahadasha -> Antardasha -> Pratyantardasha -> Sookshma -> Prana.

Periods are generated lazily; a full five-level expansion (~59k pranas per
120-year cycle) is never materialised. Paths identify periods, e.g. "Ve/Su/Mo".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..constants import NAKSHATRA_SPAN, VIMSHOTTARI_ORDER, VIMSHOTTARI_TOTAL, VIMSHOTTARI_YEARS
from ..utils import norm

LEVEL_NAMES = ["mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana"]
MAX_LEVEL = len(LEVEL_NAMES)
DEFAULT_YEAR_DAYS = 365.2425


@dataclass(frozen=True)
class Period:
    lord: str
    level: int            # 1..5
    start: datetime
    end: datetime
    path: tuple[str, ...]

    @property
    def level_name(self) -> str:
        return LEVEL_NAMES[self.level - 1]

    def to_dict(self) -> dict:
        return {
            "lord": self.lord,
            "level": self.level,
            "level_name": self.level_name,
            "path": "/".join(self.path),
            "start": self.start,
            "end": self.end,
        }


def _sequence_from(lord: str) -> list[str]:
    i = VIMSHOTTARI_ORDER.index(lord)
    return VIMSHOTTARI_ORDER[i:] + VIMSHOTTARI_ORDER[:i]


class Vimshottari:
    def __init__(self, moon_lon: float, birth: datetime, year_days: float = DEFAULT_YEAR_DAYS):
        self.birth = birth
        self.year_days = year_days
        moon_lon = norm(moon_lon)
        nak = int(moon_lon // NAKSHATRA_SPAN) % 27
        self.first_lord = VIMSHOTTARI_ORDER[nak % 9]
        self.elapsed_fraction = (moon_lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
        first_years = VIMSHOTTARI_YEARS[self.first_lord]
        self.cycle_start = birth - self._years(first_years * self.elapsed_fraction)

    def _years(self, years: float) -> timedelta:
        return timedelta(days=years * self.year_days)

    def balance_at_birth(self) -> dict:
        years = VIMSHOTTARI_YEARS[self.first_lord] * (1 - self.elapsed_fraction)
        total_days = years * self.year_days
        y = int(total_days // self.year_days)
        rem = total_days - y * self.year_days
        m = int(rem // (self.year_days / 12))
        d = (rem - m * self.year_days / 12)
        return {"lord": self.first_lord, "years": y, "months": m, "days": round(d, 2),
                "total_years": years}

    def _children(self, lord: str, start: datetime, duration_years: float,
                  level: int, path: tuple[str, ...]) -> list[Period]:
        out, cursor = [], start
        for sub in _sequence_from(lord):
            years = duration_years * VIMSHOTTARI_YEARS[sub] / VIMSHOTTARI_TOTAL
            end = cursor + self._years(years)
            out.append(Period(sub, level, cursor, end, path + (sub,)))
            cursor = end
        return out

    def mahadashas(self) -> list[Period]:
        return self._children(self.first_lord, self.cycle_start, VIMSHOTTARI_TOTAL, 1, ())

    def children(self, period: Period) -> list[Period]:
        if period.level >= MAX_LEVEL:
            return []
        years = (period.end - period.start).total_seconds() / 86400 / self.year_days
        return self._children(period.lord, period.start, years, period.level + 1, period.path)

    def resolve(self, path: list[str]) -> Period:
        """Find a period by its lord path (e.g. ["Ve", "Su"])."""
        if not path or len(path) > MAX_LEVEL:
            raise ValueError("path must have 1..5 lords")
        nodes, found = self.mahadashas(), None
        for lord in path:
            found = next((p for p in nodes if p.lord == lord), None)
            if found is None:
                raise ValueError(f"Invalid dasha path: {'/'.join(path)}")
            nodes = self.children(found)
        return found

    def tree(self, depth: int = 2) -> list[dict]:
        depth = max(1, min(depth, 3))

        def build(p: Period, d: int) -> dict:
            node = p.to_dict()
            if d < depth:
                node["children"] = [build(c, d + 1) for c in self.children(p)]
            return node

        return [build(p, 1) for p in self.mahadashas()]

    def current(self, at: datetime, levels: int = MAX_LEVEL) -> list[Period]:
        chain, nodes = [], self.mahadashas()
        for _ in range(levels):
            p = next((n for n in nodes if n.start <= at < n.end), None)
            if p is None:
                break
            chain.append(p)
            nodes = self.children(p)
        return chain
