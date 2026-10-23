"""Shadbala (six-fold planetary strength) per BPHS / B.V. Raman.

All component values are in shashtiamsas (virupas); 60 virupas = 1 rupa.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from ..attributes import planetary_wars
from ..constants import (
    DEBILITATION, DISC_DIAMETERS, FEMALE_PLANETS, HORA_SEQUENCE, JU, MA, MALE_PLANETS, ME, MO,
    MOOLATRIKONA, NAISARGIKA_BALA, NEUTER_PLANETS, OWN_SIGNS, REQUIRED_SHADBALA_RUPAS, SA,
    SEVEN_PLANETS, SU, VE, WEEKDAY_LORDS,
)
from ..houses import bhava_of
from ..relationships import compound
from ..utils import arc, deg_in_sign, norm, sign_of
from ..vargas import varga_lord, varga_sign

SAPTAVARGA = ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]
_VARGA_POINTS = {"great_friend": 20.0, "friend": 15.0, "neutral": 10.0, "enemy": 4.0, "great_enemy": 2.0}
KALI_EPOCH_JD = 588465.5  # 3102 BCE Feb 18, midnight (a Friday)
MEAN_OBLIQUITY = 23.45


# --- aspects ---------------------------------------------------------------------------

def drishti(aspecting: str, from_lon: float, to_lon: float) -> float:
    """BPHS aspect value (0..60 virupas) of ``aspecting`` at from_lon onto to_lon."""
    d = norm(to_lon - from_lon)
    if d < 30 or d >= 300:
        v = 0.0
    elif d < 60:
        v = (d - 30) / 2
    elif d < 90:
        v = d - 45
    elif d < 120:
        v = 30 + (120 - d) / 2
    elif d < 150:
        v = 150 - d
    elif d < 180:
        v = 2 * (d - 150)
    else:
        v = (300 - d) / 2
    if aspecting == SA and (60 <= d < 90 or 270 <= d < 300):
        v += 45
    elif aspecting == JU and (120 <= d < 150 or 240 <= d < 270):
        v += 30
    elif aspecting == MA and (90 <= d < 120 or 210 <= d < 240):
        v += 15
    return min(v, 60.0)


def is_benefic(planet: str, moon_waxing: bool) -> bool:
    if planet == MO:
        return moon_waxing
    return planet in (JU, VE, ME)


# --- sthana bala -------------------------------------------------------------------------

def uchcha_bala(p: str, lon: float) -> float:
    s, d = DEBILITATION[p]
    return arc(lon, s * 30 + d) / 3.0


def saptavargaja_bala(p: str, lon: float, signs: dict[str, int]) -> dict:
    out = {}
    for code in SAPTAVARGA:
        vs = varga_sign(lon, code)
        lord = varga_lord(lon, code)
        mt_sign, mt_from, mt_to = MOOLATRIKONA[p]
        if code == "D1" and vs == mt_sign and mt_from <= deg_in_sign(lon) < mt_to:
            out[code] = 45.0
        elif lord == p or (code != "D2" and vs in OWN_SIGNS[p]):
            out[code] = 30.0
        else:
            out[code] = _VARGA_POINTS[compound(p, lord, signs)]
    return out


def ojhayugma_bala(p: str, lon: float) -> float:
    rasi, nav = sign_of(lon), varga_sign(lon, "D9")
    want_even = p in (MO, VE)
    score = 0.0
    for s in (rasi, nav):
        is_even = s % 2 == 1  # Taurus (index 1) is an even sign
        if is_even == want_even:
            score += 15.0
    return score


def kendradi_bala(bhava: int) -> float:
    if bhava in (1, 4, 7, 10):
        return 60.0
    if bhava in (2, 5, 8, 11):
        return 30.0
    return 15.0


def drekkana_bala(p: str, lon: float) -> float:
    part = min(int(deg_in_sign(lon) // 10), 2)
    if (p in MALE_PLANETS and part == 0) or (p in NEUTER_PLANETS and part == 1) \
            or (p in FEMALE_PLANETS and part == 2):
        return 15.0
    return 0.0


# --- dig bala ----------------------------------------------------------------------------

def dig_bala(p: str, lon: float, madhya: list[float]) -> float:
    weak_point = {SU: madhya[3], MA: madhya[3], JU: madhya[6], ME: madhya[6],
                  MO: madhya[9], VE: madhya[9], SA: madhya[0]}[p]
    return arc(lon, weak_point) / 3.0


# --- kala bala ---------------------------------------------------------------------------

def _kranti(tropical_lon: float, eps: float) -> float:
    return math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(tropical_lon))))


def ayana_bala(p: str, tropical_lon: float, eps: float = MEAN_OBLIQUITY) -> float:
    dec = _kranti(tropical_lon, eps)
    if p in (MO, SA):
        dec = -dec
    elif p == ME:
        dec = abs(dec)
    value = max(0.0, min(60.0, 60.0 * (MEAN_OBLIQUITY + dec) / (2 * MEAN_OBLIQUITY)))
    return value


def ahargana(civil: date) -> int:
    jd0 = civil.toordinal() - 1 + 1721425.5
    return int(round(jd0 - KALI_EPOCH_JD))


def kala_lords(civil: date, birth: datetime, sunrise: datetime) -> dict:
    a = ahargana(civil)
    vara = WEEKDAY_LORDS[(a + 5) % 7]
    hours = int((birth - sunrise).total_seconds() // 3600)
    hora = HORA_SEQUENCE[(HORA_SEQUENCE.index(vara) + hours) % 7]
    return {
        "ahargana": a,
        "abda": WEEKDAY_LORDS[(3 * (a // 360) + 5) % 7],
        "masa": WEEKDAY_LORDS[(2 * (a // 30) + 5) % 7],
        "vara": vara,
        "hora": hora,
    }


def compute_shadbala(snap, bhavas: dict, day, ) -> dict:
    """``snap``: ephemeris.Snapshot; ``bhavas``: houses.sripati_bhavas(); ``day``: panchang.SunDay."""
    lons = {p: snap.bodies[p].lon for p in SEVEN_PLANETS}
    trop = {p: snap.bodies[p].tropical_lon for p in SEVEN_PLANETS}
    signs = {p: sign_of(lons[p]) for p in SEVEN_PLANETS}
    madhya, sandhi = bhavas["madhya"], bhavas["sandhi"]
    birth = snap.dt

    moon_sun = norm(lons[MO] - lons[SU])
    moon_waxing = moon_sun < 180
    elong = arc(lons[MO], lons[SU])

    # Nathonnata: distance from local apparent midnight
    noon = day.sunrise + (day.sunset - day.sunrise) / 2
    midnights = [noon - timedelta(hours=12), noon + timedelta(hours=12)]
    delta_h = min(abs((birth - m).total_seconds()) for m in midnights) / 3600
    delta_h = min(delta_h, 12.0)

    # Tribhaga
    if day.is_day:
        third = (day.sunset - day.sunrise) / 3
        idx = min(int((birth - day.sunrise) / third), 2)
        tribhaga_lord = [ME, SU, SA][idx]
    else:
        third = (day.next_sunrise - day.sunset) / 3
        idx = min(int((birth - day.sunset) / third), 2)
        tribhaga_lord = [MO, VE, MA][idx]

    lords = kala_lords(day.civil_date.date(), birth, day.sunrise)

    result: dict[str, dict] = {}
    for p in SEVEN_PLANETS:
        lon = lons[p]
        sv = saptavargaja_bala(p, lon, signs)
        sthana = {
            "uchcha": uchcha_bala(p, lon),
            "saptavargaja": sum(sv.values()),
            "ojhayugma": ojhayugma_bala(p, lon),
            "kendradi": kendradi_bala(bhava_of(lon, sandhi)),
            "drekkana": drekkana_bala(p, lon),
        }

        if p == ME:
            nathonnata = 60.0
        elif p in (MO, MA, SA):
            nathonnata = 60.0 * (1 - delta_h / 12)
        else:
            nathonnata = 60.0 * delta_h / 12

        paksha = elong / 3 if is_benefic(p, True) or p == MO else 60 - elong / 3
        if p == MO:
            paksha *= 2

        ayana = ayana_bala(p, trop[p])
        kala = {
            "nathonnata": nathonnata,
            "paksha": paksha,
            "tribhaga": 60.0 if (p == JU or p == tribhaga_lord) else 0.0,
            "abda": 15.0 if lords["abda"] == p else 0.0,
            "masa": 30.0 if lords["masa"] == p else 0.0,
            "vara": 45.0 if lords["vara"] == p else 0.0,
            "hora": 60.0 if lords["hora"] == p else 0.0,
            "ayana": ayana * 2 if p == SU else ayana,
            "yuddha": 0.0,
        }

        if p == SU:
            chesta = ayana
        elif p == MO:
            chesta = elong / 3
        else:
            geo, helio, sun = trop[p], snap.helio[p], trop[SU]
            if p in (MA, JU, SA):
                mid = norm(helio + ((geo - helio + 180) % 360 - 180) / 2)
                kendra = sun - mid
            else:
                mid = norm(sun + ((geo - sun + 180) % 360 - 180) / 2)
                kendra = helio - mid
            chesta = arc(kendra, 0) / 3.0

        drik = 0.0
        for q in SEVEN_PLANETS:
            if q == p:
                continue
            v = drishti(q, lons[q], lon) / 4
            drik += v if is_benefic(q, moon_waxing) else -v

        result[p] = {
            "sthana": sthana,
            "saptavargaja_detail": sv,
            "dig": dig_bala(p, lon, madhya),
            "kala": kala,
            "chesta": chesta,
            "naisargika": NAISARGIKA_BALA[p],
            "drik": drik,
        }

    # Graha yuddha between star planets within 1 degree
    wars = []
    for a, b in planetary_wars(lons):
        def partial(x):
            r = result[x]
            return sum(r["sthana"].values()) + r["dig"] + sum(r["kala"].values())
        ta, tb = partial(a), partial(b)
        diff_d = abs(DISC_DIAMETERS[a] - DISC_DIAMETERS[b]) or 1.0
        yb = abs(ta - tb) / diff_d
        winner, loser = (a, b) if ta >= tb else (b, a)
        result[winner]["kala"]["yuddha"] += yb
        result[loser]["kala"]["yuddha"] -= yb
        wars.append({"winner": winner, "loser": loser, "value": yb})

    for p, r in result.items():
        sthana_total = sum(r["sthana"].values())
        kala_total = sum(r["kala"].values())
        total = sthana_total + r["dig"] + kala_total + r["chesta"] + r["naisargika"] + r["drik"]
        r["totals"] = {
            "sthana": sthana_total, "dig": r["dig"], "kala": kala_total, "chesta": r["chesta"],
            "naisargika": r["naisargika"], "drik": r["drik"],
        }
        r["total_virupas"] = total
        r["total_rupas"] = total / 60
        r["required_rupas"] = REQUIRED_SHADBALA_RUPAS[p]
        r["ratio"] = r["total_rupas"] / REQUIRED_SHADBALA_RUPAS[p]
        u, c = r["sthana"]["uchcha"], r["chesta"]
        r["ishta_phala"] = math.sqrt(max(u, 0) * max(c, 0))
        r["kashta_phala"] = math.sqrt(max(60 - u, 0) * max(60 - c, 0))

    ranked = sorted(result, key=lambda x: result[x]["ratio"], reverse=True)
    for i, p in enumerate(ranked, 1):
        result[p]["rank"] = i

    return {"planets": result, "kala_lords": lords, "tribhaga_lord": tribhaga_lord, "wars": wars}
