"""Bridge between Django models and the pure-Python engine, with DB caching."""
import hashlib
import json
import logging
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction

from apps.core.exceptions import ServiceError, ServiceUnavailable
from apps.profiles.models import BirthProfile

from .engine import ENGINE_VERSION, BirthInput, compute_chart, compute_strengths
from .engine.chart import compute_day_panchang, jsonable
from .engine.dasha.vimshottari import Vimshottari
from .engine.ephemeris import EphemerisNotAvailable
from .models import ComputedResult

logger = logging.getLogger(__name__)


def birth_input(profile: BirthProfile) -> BirthInput:
    return BirthInput(
        dt=profile.birth_utc, lat=profile.latitude, lon=profile.longitude,
        tz_name=profile.tz_name, ayanamsa=profile.ayanamsa, node_mode=profile.node_mode,
    )


def input_hash(profile: BirthProfile) -> str:
    raw = json.dumps([
        profile.birth_utc.isoformat(), round(profile.latitude, 6), round(profile.longitude, 6),
        profile.tz_name, profile.ayanamsa, profile.node_mode, ENGINE_VERSION,
    ])
    return hashlib.sha256(raw.encode()).hexdigest()


def _run(fn: Callable[[], dict]) -> dict:
    try:
        return fn()
    except EphemerisNotAvailable as exc:
        logger.error("Ephemeris unavailable: %s", exc)
        raise ServiceUnavailable("Astronomical data is not available on the server.") from exc
    except ValueError as exc:
        raise ServiceError(str(exc), code="calculation_error") from exc


def _cached(profile: BirthProfile, kind: str, fn: Callable[[], dict]) -> dict:
    h = input_hash(profile)
    row = ComputedResult.objects.filter(profile=profile, kind=kind, input_hash=h).only("payload").first()
    if row:
        return row.payload
    payload = _run(fn)
    try:
        with transaction.atomic():
            ComputedResult.objects.filter(profile=profile, kind=kind).exclude(input_hash=h).delete()
            ComputedResult.objects.create(profile=profile, kind=kind, input_hash=h, payload=payload)
    except IntegrityError:  # concurrent request stored it first
        pass
    return payload


def get_chart(profile: BirthProfile) -> dict:
    return _cached(profile, ComputedResult.Kind.CHART, lambda: compute_chart(birth_input(profile)))


def get_strengths(profile: BirthProfile) -> dict:
    return _cached(profile, ComputedResult.Kind.STRENGTHS, lambda: compute_strengths(birth_input(profile)))


def _vimshottari(profile: BirthProfile) -> Vimshottari:
    chart = get_chart(profile)
    moon = next(p for p in chart["planets"] if p["code"] == "Mo")
    return Vimshottari(moon["longitude"], profile.birth_utc)


def get_dasha_tree(profile: BirthProfile, depth: int) -> dict:
    tz = ZoneInfo(profile.tz_name)

    def build():
        v = _vimshottari(profile)
        return jsonable({"balance_at_birth": v.balance_at_birth(), "periods": v.tree(3)}, tz)

    data = _cached(profile, ComputedResult.Kind.DASHA_TREE, build)

    def prune(nodes, level):
        out = []
        for n in nodes:
            n = dict(n)
            if level >= depth:
                n.pop("children", None)
            else:
                n["children"] = prune(n.get("children", []), level + 1)
            out.append(n)
        return out

    return {"balance_at_birth": data["balance_at_birth"], "depth": depth,
            "periods": prune(data["periods"], 1)}


def get_dasha_children(profile: BirthProfile, path: list[str]) -> dict:
    v = _vimshottari(profile)
    parent = _run(lambda: v.resolve(path))
    return jsonable({"parent": parent.to_dict(), "periods": [p.to_dict() for p in v.children(parent)]},
                    ZoneInfo(profile.tz_name))


def get_current_dasha(profile: BirthProfile, at: datetime) -> dict:
    v = _vimshottari(profile)
    chain = v.current(at)
    return jsonable({"at": at, "periods": [p.to_dict() for p in chain]}, ZoneInfo(profile.tz_name))


def day_panchang(dt: datetime, lat: float, lon: float, tz_name: str, ayanamsa: str) -> dict:
    return _run(lambda: compute_day_panchang(dt, lat, lon, tz_name, ayanamsa))


# --- Strength report (Shadbala + Bhava Bala with guidance) ---------------------------
def strength_report(profile: BirthProfile, lang: str) -> dict:
    from django.utils import timezone as dj_tz

    from .content import strength as sc
    from .content.common import GLYPH, HOUSE_MEANING, KARAKA, full

    s = get_strengths(profile)
    chart = get_chart(profile)
    md_lord = _vimshottari(profile).current(dj_tz.now(), levels=1)[0].lord
    shad = s["shadbala"]["planets"]

    planets = []
    for code, r in shad.items():
        kind = sc.status_of_ratio(r["ratio"])
        planets.append({
            "code": code, "glyph": GLYPH[code], "name": full(code, lang),
            "total_rupas": r["total_rupas"], "required_rupas": r["required_rupas"], "ratio": r["ratio"],
            "kind": kind, "status": sc.STATUS[lang][kind], "rank": r["rank"], "is_dasha_lord": code == md_lord,
            "sources": [{"key": k, "name": v[2 if lang == "hi" else 0], "gloss": v[3 if lang == "hi" else 1],
                         "virupas": r["totals"][k]} for k, v in sc.SOURCES.items()],
            "advice": sc.planet_advice(code, kind, lang),
        })
    planets.sort(key=lambda p: -p["ratio"])
    full_strength = sum(1 for p in planets if p["ratio"] >= 1.0)
    dasha_planet = next((p for p in planets if p["code"] == md_lord), None)

    houses = []
    for b in s["bhavabala"]:
        rupas = b["total_rupas"]
        kind = sc.status_of_house(rupas)
        c = b["components"]
        sign_idx = next(h["sign_index"] for h in chart["houses"] if h["house"] == b["bhava"]) - 1
        houses.append({
            "house": b["bhava"], "sign": b["sign"], "lord": b["lord"], "rupas": rupas, "kind": kind,
            "status": sc.STATUS[lang][kind], "rank": b["rank"], "occupants": b["occupants"],
            "karaka": KARAKA[lang][b["bhava"] - 1], "meaning": HOUSE_MEANING[lang][b["bhava"] - 1],
            "rasi_sign_index": sign_idx + 1,
            "lord_ratio": shad[b["lord"]]["ratio"] if b["lord"] in shad else None,
            "components": [
                {"key": "bhavadhipati", "name": sc.BHAVA_COMPONENTS["bhavadhipati"][lang == "hi"], "rupas": c["bhavadhipati"] / 60},
                {"key": "dig", "name": sc.BHAVA_COMPONENTS["dig"][lang == "hi"], "rupas": c["dig"] / 60},
                {"key": "drishti", "name": sc.BHAVA_COMPONENTS["drishti"][lang == "hi"], "rupas": c["drishti"] / 60},
                {"key": "other", "name": sc.BHAVA_COMPONENTS["other"][lang == "hi"],
                 "rupas": (c["occupation"] + c["day_night"]) / 60},
            ],
            "advice": sc.house_advice(b["bhava"], kind, b["lord"], lang),
        })

    return {
        "summary": {
            "full_strength": full_strength, "total": len(planets),
            "strongest": {k: planets[0][k] for k in ("code", "glyph", "ratio")},
            "weakest": {k: planets[-1][k] for k in ("code", "glyph", "ratio")},
            "dasha_lord": md_lord,
            "dasha_note": sc.dasha_note(md_lord, dasha_planet["kind"], lang) if dasha_planet else "",
            "weak_planets": sum(1 for p in planets if p["kind"] == "bad"),
            "weak_houses": sum(1 for h in houses if h["kind"] == "bad"),
            "house_minimum": 7.0,
        },
        "planets": planets,
        "houses": houses,
    }
