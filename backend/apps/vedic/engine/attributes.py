"""Per-planet attributes: dignity, combustion, avasthas, nakshatra, war."""
from itertools import combinations

from .constants import (
    COMBUSTION_ORBS, DEBILITATION, EXALTATION, MA, ME, JU, MOOLATRIKONA, NAKSHATRA_LORDS,
    NAKSHATRA_SPAN, NAKSHATRAS, OWN_SIGNS, PADA_SPAN, SA, SIGN_LORDS, SU, VE,
)
from .relationships import compound
from .utils import arc, deg_in_sign, norm, sign_of

EXALTED, DEBILITATED, MOOLATRIKONA_D, OWN = "exalted", "debilitated", "moolatrikona", "own"


def nakshatra_info(lon: float) -> dict:
    lon = norm(lon)
    idx = int(lon // NAKSHATRA_SPAN) % 27
    within = lon - idx * NAKSHATRA_SPAN
    return {
        "index": idx + 1,
        "name": NAKSHATRAS[idx],
        "pada": int(within // PADA_SPAN) + 1,
        "lord": NAKSHATRA_LORDS[idx],
        "degrees_elapsed": within,
        "fraction_elapsed": within / NAKSHATRA_SPAN,
    }


def dignity(planet: str, lon: float, signs: dict[str, int]) -> str:
    s, d = sign_of(lon), deg_in_sign(lon)
    if EXALTATION[planet][0] == s:
        return EXALTED
    if DEBILITATION[planet][0] == s:
        return DEBILITATED
    mt_sign, mt_from, mt_to = MOOLATRIKONA[planet]
    if s == mt_sign and mt_from <= d < mt_to:
        return MOOLATRIKONA_D
    if s in OWN_SIGNS[planet]:
        return OWN
    lord = SIGN_LORDS[s]
    if lord == planet:
        return OWN
    return compound(planet, lord, {**signs, planet: s})


def is_combust(planet: str, lon: float, sun_lon: float, retrograde: bool) -> bool:
    if planet not in COMBUSTION_ORBS:
        return False
    direct, retro = COMBUSTION_ORBS[planet]
    return arc(lon, sun_lon) < (retro if retrograde else direct)


_BALADI = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]


def baladi_avastha(lon: float) -> str:
    idx = min(int(deg_in_sign(lon) // 6), 4)
    odd = sign_of(lon) % 2 == 0
    return _BALADI[idx] if odd else _BALADI[4 - idx]


def jagradadi_avastha(dig: str) -> str:
    if dig in (EXALTED, OWN, MOOLATRIKONA_D):
        return "Jagrat"
    if dig in ("great_friend", "friend", "neutral"):
        return "Swapna"
    return "Sushupti"


def planetary_wars(lons: dict[str, float]) -> list[tuple[str, str]]:
    """Pairs of star-planets within 1 degree of each other (graha yuddha)."""
    cands = [p for p in (MA, ME, JU, VE, SA) if p in lons]
    return [(a, b) for a, b in combinations(cands, 2) if arc(lons[a], lons[b]) < 1.0]


def planet_attributes(code: str, lon: float, speed: float, sun_lon: float,
                      signs: dict[str, int]) -> dict:
    # Nodes included: the mean node always moves backwards; the true node does too except
    # for brief stationary/direct spells, which its speed shows.
    retro = speed < 0
    dig = dignity(code, lon, signs)
    return {
        "retrograde": retro,
        "combust": code != SU and is_combust(code, lon, sun_lon, retro),
        "dignity": dig,
        "avastha": {
            "baladi": baladi_avastha(lon),
            "jagradadi": jagradadi_avastha(dig),
        },
    }
