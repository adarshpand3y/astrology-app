"""Avakhada chakra (birth particulars derived from Moon and Lagna)."""
from .constants import (
    NAKSHATRA_AKSHAR, NAKSHATRA_GANA, NAKSHATRA_LORDS, NAKSHATRA_NADI, NAKSHATRA_SPAN,
    NAKSHATRA_YONI, NAKSHATRAS, PADA_SPAN, SIGN_LORDS, SIGN_TATVA, SIGN_VARNA, SIGNS,
)
from .utils import deg_in_sign, sign_of

_VASHYA = {
    0: "Chatushpada", 1: "Chatushpada", 2: "Manava", 3: "Jalachara", 4: "Vanachara",
    5: "Manava", 6: "Manava", 7: "Keeta", 10: "Manava", 11: "Jalachara",
}

_PAYA = {1: "Swarna (Gold)", 6: "Swarna (Gold)", 11: "Swarna (Gold)",
         2: "Rajat (Silver)", 5: "Rajat (Silver)", 9: "Rajat (Silver)",
         3: "Tamra (Copper)", 7: "Tamra (Copper)", 10: "Tamra (Copper)",
         4: "Loha (Iron)", 8: "Loha (Iron)", 12: "Loha (Iron)"}


def vashya(moon_lon: float) -> str:
    s, d = sign_of(moon_lon), deg_in_sign(moon_lon)
    if s == 8:
        return "Manava" if d < 15 else "Chatushpada"
    if s == 9:
        return "Chatushpada" if d < 15 else "Jalachara"
    return _VASHYA[s]


def compute_avakhada(moon_lon: float, asc_lon: float) -> dict:
    ms = sign_of(moon_lon)
    n = int(moon_lon // NAKSHATRA_SPAN) % 27
    pada = int((moon_lon % NAKSHATRA_SPAN) // PADA_SPAN)
    moon_house = (ms - sign_of(asc_lon)) % 12 + 1
    return {
        "lagna": SIGNS[sign_of(asc_lon)],
        "lagna_lord": SIGN_LORDS[sign_of(asc_lon)],
        "rashi": SIGNS[ms],
        "rashi_lord": SIGN_LORDS[ms],
        "nakshatra": NAKSHATRAS[n],
        "nakshatra_pada": pada + 1,
        "nakshatra_lord": NAKSHATRA_LORDS[n],
        "varna": SIGN_VARNA[ms],
        "vashya": vashya(moon_lon),
        "yoni": NAKSHATRA_YONI[n],
        "gana": NAKSHATRA_GANA[n],
        "nadi": NAKSHATRA_NADI[n],
        "tatva": SIGN_TATVA[ms],
        "paya": _PAYA[moon_house],
        "name_akshar": NAKSHATRA_AKSHAR[n][pada],
    }
