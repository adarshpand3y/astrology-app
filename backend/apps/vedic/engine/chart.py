"""Engine entry points. Pure Python: no Django imports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from zoneinfo import ZoneInfo

from . import ephemeris as ephem
from .attributes import nakshatra_info, planet_attributes
from .avakhada import compute_avakhada
from .constants import DEBILITATION, EXALTATION, PLANET_NAMES, PLANETS, SIGN_LORDS, SIGNS, SIGNS_SANSKRIT
from .dasha.vimshottari import DEFAULT_YEAR_DAYS, Vimshottari
from .houses import bhava_of, sripati_bhavas, whole_sign_house
from .panchang import compute_panchang, sun_day
from .relationships import compound_table
from .strength.bhavabala import compute_bhavabala
from .strength.shadbala import compute_shadbala
from .utils import deg_in_sign, dms, sign_of
from .vargas import VARGA_CODES, VARGA_NAMES, varga_sign

ENGINE_VERSION = "1.2.0"  # 1.1: varga planets carry retrograde/combust/dignity marks; 1.2: incl. Rahu/Ketu


@dataclass(frozen=True)
class BirthInput:
    dt: datetime            # timezone-aware moment of birth
    lat: float
    lon: float
    tz_name: str
    ayanamsa: str = "lahiri"
    node_mode: str = "mean"  # "mean" | "true"
    year_days: float = DEFAULT_YEAR_DAYS

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.tz_name)


class ChartContext:
    """Lazily computed, shared intermediate results for one birth moment."""

    def __init__(self, inp: BirthInput):
        self.inp = inp

    @cached_property
    def snap(self):
        return ephem.compute_snapshot(self.inp.dt, self.inp.lat, self.inp.lon,
                                      self.inp.ayanamsa, self.inp.node_mode)

    @cached_property
    def bhavas(self):
        return sripati_bhavas(self.snap.ascendant, self.snap.mc)

    @cached_property
    def day(self):
        return sun_day(self.inp.dt, self.inp.lat, self.inp.lon, self.inp.tz)

    @cached_property
    def signs(self) -> dict[str, int]:
        return {p: sign_of(b.lon) for p, b in self.snap.bodies.items()}

    @cached_property
    def shadbala(self):
        return compute_shadbala(self.snap, self.bhavas, self.day)

    @cached_property
    def dasha(self) -> Vimshottari:
        return Vimshottari(self.snap.bodies["Mo"].lon, self.inp.dt, self.inp.year_days)

    # --- report builders -------------------------------------------------------------

    def _position(self, lon: float) -> dict:
        s = sign_of(lon)
        return {
            "longitude": lon,
            "sign": SIGNS[s],
            "sign_sanskrit": SIGNS_SANSKRIT[s],
            "sign_index": s + 1,
            "sign_lord": SIGN_LORDS[s],
            "degree": deg_in_sign(lon),
            "degree_dms": dms(deg_in_sign(lon)),
            "nakshatra": nakshatra_info(lon),
        }

    def meta(self) -> dict:
        i, s = self.inp, self.snap
        return {
            "engine_version": ENGINE_VERSION,
            "ayanamsa": {"name": i.ayanamsa, "value": s.ayanamsa, "dms": dms(s.ayanamsa)},
            "node_mode": i.node_mode,
            "birth_local": i.dt.astimezone(i.tz),
            "birth_utc": i.dt,
            "timezone": i.tz_name,
            "latitude": i.lat,
            "longitude": i.lon,
            "julian_day_ut": s.jd_ut,
            "obliquity": s.obliquity,
            "house_system": "whole_sign (rasi) + sripati (bhava chalit)",
        }

    def lagna(self) -> dict:
        return self._position(self.snap.ascendant)

    def planets(self) -> list[dict]:
        s = self.snap
        sun_lon = s.bodies["Su"].lon
        out = []
        for code in PLANETS:
            b = s.bodies[code]
            item = {"code": code, "name": PLANET_NAMES[code], **self._position(b.lon)}
            item.update({
                "house": whole_sign_house(b.lon, s.ascendant),
                "bhava": bhava_of(b.lon, self.bhavas["sandhi"]),
                "speed": b.speed,
                "latitude": b.lat,
                "declination": b.declination,
                "navamsa_sign": SIGNS[varga_sign(b.lon, "D9")],
                **planet_attributes(code, b.lon, b.speed, sun_lon, self.signs),
            })
            out.append(item)
        return out

    def houses(self) -> list[dict]:
        asc_sign = sign_of(self.snap.ascendant)
        out = []
        for h in range(12):
            sign = (asc_sign + h) % 12
            out.append({
                "house": h + 1, "sign": SIGNS[sign], "sign_index": sign + 1,
                "lord": SIGN_LORDS[sign],
                "occupants": [p for p in PLANETS if self.signs[p] == sign],
            })
        return out

    def bhava_chalit(self) -> list[dict]:
        madhya, sandhi = self.bhavas["madhya"], self.bhavas["sandhi"]
        return [{
            "bhava": i + 1,
            "start": sandhi[i],
            "madhya": madhya[i],
            "sign": SIGNS[sign_of(madhya[i])],
            "occupants": [p for p in PLANETS if bhava_of(self.snap.bodies[p].lon, sandhi) == i + 1],
        } for i in range(12)]

    def varga(self, code: str) -> dict:
        asc = varga_sign(self.snap.ascendant, code)
        planets = {p: varga_sign(b.lon, code) for p, b in self.snap.bodies.items()}
        natal = {p["code"]: p for p in self.natal_planets}

        def marks(p: str, s: int) -> dict:
            # Motion and combustion belong to the planet itself (same in every varga);
            # exaltation/debilitation are read from the planet's sign in this varga.
            return {
                "retrograde": natal[p]["retrograde"],
                "combust": natal[p]["combust"],
                "dignity": "exalted" if EXALTATION[p][0] == s else "debilitated" if DEBILITATION[p][0] == s else None,
            }

        return {
            "code": code,
            "name": VARGA_NAMES[code],
            "ascendant": {"sign": SIGNS[asc], "sign_index": asc + 1},
            "planets": [{"code": p, "sign": SIGNS[s], "sign_index": s + 1,
                         "house": (s - asc) % 12 + 1, **marks(p, s)} for p, s in planets.items()],
        }

    @cached_property
    def natal_planets(self) -> list[dict]:
        return self.planets()

    def panchang(self) -> dict:
        b = self.snap.bodies
        return compute_panchang(self.inp.dt, self.inp.lat, self.inp.lon, self.inp.tz,
                                b["Su"].lon, b["Mo"].lon, b["Su"].tropical_lon,
                                self.inp.ayanamsa, self.day)

    def avakhada(self) -> dict:
        return compute_avakhada(self.snap.bodies["Mo"].lon, self.snap.ascendant)

    def relationships(self) -> dict:
        seven = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
        return compound_table(seven, self.signs)

    def bhavabala(self) -> list[dict]:
        return compute_bhavabala(self.snap, self.bhavas, self.day, self.shadbala)


def compute_chart(inp: BirthInput, vargas: list[str] | None = None) -> dict:
    ctx = ChartContext(inp)
    codes = VARGA_CODES if vargas is None else vargas
    return jsonable({
        "meta": ctx.meta(),
        "lagna": ctx.lagna(),
        "planets": ctx.planets(),
        "houses": ctx.houses(),
        "bhava_chalit": ctx.bhava_chalit(),
        "vargas": {c: ctx.varga(c) for c in codes},
        "panchang": ctx.panchang(),
        "avakhada": ctx.avakhada(),
        "relationships": ctx.relationships(),
        "dasha_balance": ctx.dasha.balance_at_birth(),
    }, inp.tz)


def compute_strengths(inp: BirthInput) -> dict:
    ctx = ChartContext(inp)
    return jsonable({"shadbala": ctx.shadbala, "bhavabala": ctx.bhavabala()}, inp.tz)


def compute_day_panchang(dt: datetime, lat: float, lon: float, tz_name: str,
                         ayanamsa: str = "lahiri") -> dict:
    inp = BirthInput(dt=dt, lat=lat, lon=lon, tz_name=tz_name, ayanamsa=ayanamsa)
    ctx = ChartContext(inp)
    return jsonable({"meta": ctx.meta(), "panchang": ctx.panchang(),
                     "lagna": ctx.lagna()}, inp.tz)


def jsonable(obj, tz: ZoneInfo | None = None, ndigits: int = 6):
    """Convert datetimes to local ISO strings and round floats, recursively."""
    if isinstance(obj, dict):
        return {k: jsonable(v, tz, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v, tz, ndigits) for v in obj]
    if isinstance(obj, datetime):
        return (obj.astimezone(tz) if tz else obj).isoformat(timespec="seconds")
    if isinstance(obj, float):  # includes numpy.float64
        return round(float(obj), ndigits)
    if isinstance(obj, (bool, int, str)) or obj is None:
        return obj
    if hasattr(obj, "item"):  # other numpy scalars
        return jsonable(obj.item(), tz, ndigits)
    return obj
