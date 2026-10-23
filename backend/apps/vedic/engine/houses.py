"""House systems: whole-sign rashi houses and Sripati bhavas (bhava chalit)."""
from .utils import norm, sign_of


def _span(a: float, b: float) -> float:
    """Forward arc from a to b (0..360)."""
    return norm(b - a)


def sripati_bhavas(asc: float, mc: float) -> dict:
    """Sripati (Porphyry-style trisection) bhava madhyas and sandhis.

    Returns ``{"madhya": [12 lons], "sandhi": [12 lons]}`` where sandhi[i] is the
    start of bhava i+1 (midpoint between madhya i and madhya i-1).
    """
    ic = norm(mc + 180)
    desc = norm(asc + 180)
    madhya = [0.0] * 12
    quadrants = [(asc, ic, 0), (ic, desc, 3), (desc, mc, 6), (mc, asc, 9)]
    for start, end, idx in quadrants:
        arc = _span(start, end)
        for k in range(3):
            madhya[idx + k] = norm(start + arc * k / 3.0)
    sandhi = [norm(madhya[i - 1] + _span(madhya[i - 1], madhya[i]) / 2.0) for i in range(12)]
    return {"madhya": madhya, "sandhi": sandhi}


def bhava_of(lon: float, sandhi: list[float]) -> int:
    """1-based bhava number containing ``lon`` given bhava start points."""
    for i in range(12):
        start, end = sandhi[i], sandhi[(i + 1) % 12]
        if _span(start, lon) < _span(start, end):
            return i + 1
    return 1


def whole_sign_house(lon: float, asc: float) -> int:
    return (sign_of(lon) - sign_of(asc)) % 12 + 1
