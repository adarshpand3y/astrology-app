"""Bhava Bala (house strength) per B.V. Raman's "Graha and Bhava Balas"."""
from __future__ import annotations

from datetime import timedelta

from ..constants import (
    JU, MA, ME, MO, PRISHTODAYA, SA, SEVEN_PLANETS, SHEERSHODAYA, SIGN_LORDS, SU, SIGNS,
    UBHAYODAYA,
)
from ..houses import bhava_of
from ..utils import arc, deg_in_sign, norm, sign_of
from .shadbala import drishti, is_benefic

SANDHYA = timedelta(minutes=48)  # two ghatis around sunrise/sunset


def _sign_type(lon: float) -> str:
    s, d = sign_of(lon), deg_in_sign(lon)
    if s in (2, 5, 6, 10) or (s == 8 and d < 15):
        return "nara"
    if s in (3, 11) or (s == 9 and d >= 15):
        return "jalachara"
    if s == 7:
        return "keeta"
    return "chatushpada"


def compute_bhavabala(snap, bhavas: dict, day, shadbala: dict) -> list[dict]:
    madhya, sandhi = bhavas["madhya"], bhavas["sandhi"]
    lons = {p: snap.bodies[p].lon for p in SEVEN_PLANETS}
    moon_waxing = norm(lons[MO] - lons[SU]) < 180
    occupants = {i: [] for i in range(1, 13)}
    for p, lon in lons.items():
        occupants[bhava_of(lon, sandhi)].append(p)

    birth = snap.dt
    twilight = (abs(birth - day.sunrise) <= SANDHYA or abs(birth - day.sunset) <= SANDHYA
                or abs(birth - day.next_sunrise) <= SANDHYA)
    weak_points = {"nara": madhya[6], "jalachara": madhya[9], "keeta": madhya[0],
                   "chatushpada": madhya[3]}

    out = []
    for i in range(12):
        m = madhya[i]
        s = sign_of(m)
        lord = SIGN_LORDS[s]
        adhipati = shadbala["planets"][lord]["total_virupas"]
        stype = _sign_type(m)
        dig = arc(m, weak_points[stype]) / 3.0

        drishti_total = 0.0
        for q in SEVEN_PLANETS:
            v = drishti(q, lons[q], m)
            if q not in (JU, ME):
                v /= 4
            drishti_total += v if is_benefic(q, moon_waxing) else -v

        occ = 0.0
        for q in occupants[i + 1]:
            if q in (JU, ME):
                occ += 60.0
            elif q in (SA, MA, SU):
                occ -= 60.0

        if s in UBHAYODAYA:
            day_night = 15.0 if twilight else 0.0
        elif s in SHEERSHODAYA:
            day_night = 15.0 if day.is_day else 0.0
        elif s in PRISHTODAYA:
            day_night = 0.0 if day.is_day else 15.0
        else:
            day_night = 0.0

        total = adhipati + dig + drishti_total + occ + day_night
        out.append({
            "bhava": i + 1,
            "madhya": m,
            "sign": SIGNS[s],
            "lord": lord,
            "occupants": occupants[i + 1],
            "components": {
                "bhavadhipati": adhipati,
                "dig": dig,
                "drishti": drishti_total,
                "occupation": occ,
                "day_night": day_night,
            },
            "total_virupas": total,
            "total_rupas": total / 60,
        })

    ranked = sorted(out, key=lambda b: b["total_virupas"], reverse=True)
    for rank, b in enumerate(ranked, 1):
        b["rank"] = rank
    return out
