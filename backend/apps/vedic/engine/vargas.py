"""Shodashvarga divisional charts (Parashara rules)."""
from .constants import SIGN_LORDS, SU, MO
from .utils import deg_in_sign, norm, sign_of

VARGA_NAMES = {
    "D1": "Rasi", "D2": "Hora", "D3": "Drekkana", "D4": "Chaturthamsa", "D7": "Saptamsa",
    "D9": "Navamsa", "D10": "Dasamsa", "D12": "Dwadasamsa", "D16": "Shodasamsa",
    "D20": "Vimsamsa", "D24": "Chaturvimsamsa", "D27": "Saptavimsamsa", "D30": "Trimsamsa",
    "D40": "Khavedamsa", "D45": "Akshavedamsa", "D60": "Shashtiamsa",
}
VARGA_CODES = list(VARGA_NAMES)


def _odd(sign: int) -> bool:
    """Odd sign in 1-based counting (Aries, Gemini, ...)."""
    return sign % 2 == 0


def _part(d: float, n: int) -> int:
    return min(int(d / (30.0 / n)), n - 1)


def varga_sign(lon: float, code: str) -> int:
    lon = norm(lon)
    s, d = sign_of(lon), deg_in_sign(lon)
    movable, fixed = s % 3 == 0, s % 3 == 1

    if code == "D1":
        return s
    if code == "D2":
        first = d < 15
        return (4 if first else 3) if _odd(s) else (3 if first else 4)
    if code == "D3":
        return (s + 4 * _part(d, 3)) % 12
    if code == "D4":
        return (s + 3 * _part(d, 4)) % 12
    if code == "D7":
        return (s + _part(d, 7) + (0 if _odd(s) else 6)) % 12
    if code == "D9":
        return int(lon / (30.0 / 9)) % 12
    if code == "D10":
        return (s + _part(d, 10) + (0 if _odd(s) else 8)) % 12
    if code == "D12":
        return (s + _part(d, 12)) % 12
    if code == "D16":
        return ((0 if movable else 4 if fixed else 8) + _part(d, 16)) % 12
    if code == "D20":
        return ((0 if movable else 8 if fixed else 4) + _part(d, 20)) % 12
    if code == "D24":
        return ((4 if _odd(s) else 3) + _part(d, 24)) % 12
    if code == "D27":
        return int(lon / (30.0 / 27)) % 12
    if code == "D30":
        if _odd(s):
            bounds = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]
        else:
            bounds = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]
        for limit, sign in bounds:
            if d < limit:
                return sign
        return bounds[-1][1]
    if code == "D40":
        return ((0 if _odd(s) else 6) + _part(d, 40)) % 12
    if code == "D45":
        return ((0 if movable else 4 if fixed else 8) + _part(d, 45)) % 12
    if code == "D60":
        return (s + _part(d, 60)) % 12
    raise ValueError(f"Unknown varga {code}")


def varga_lord(lon: float, code: str) -> str:
    """Lord of the varga sign (for Hora: Sun for Leo, Moon for Cancer)."""
    sign = varga_sign(lon, code)
    if code == "D2":
        return SU if sign == 4 else MO
    return SIGN_LORDS[sign]
