"""Thin wrapper around Skyfield + JPL DE440s producing sidereal positions.

Conventions:
- Tropical positions are geocentric, apparent, true ecliptic & equinox of date.
- Sidereal longitude = tropical true longitude - true ayanamsa, where
  true ayanamsa = mean ayanamsa + nutation in longitude.
"""
from __future__ import annotations

import math
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
from skyfield.api import Loader, wgs84
from skyfield.framelib import ecliptic_frame
from skyfield.nutationlib import iau2000a_radians, mean_obliquity
from skyfield.positionlib import ICRF

from . import ayanamsa as ayan
from .constants import JU, KE, MA, ME, MO, RA, SA, SU, VE
from .utils import norm

EPHEMERIS_FILE = "de440s.bsp"

_BODY_KEYS = {
    SU: "sun", MO: "moon", MA: "mars barycenter", ME: "mercury",
    JU: "jupiter barycenter", VE: "venus", SA: "saturn barycenter",
}

_lock = threading.Lock()
_state: dict = {}


class EphemerisNotAvailable(RuntimeError):
    pass


def configure(path: str | os.PathLike) -> None:
    """Point the engine at the directory (or file) holding de440s.bsp."""
    with _lock:
        _state.clear()
        _state["path"] = Path(path)


def _default_path() -> Path:
    env = os.environ.get("EPHEMERIS_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "data"


def _load():
    if "eph" in _state:
        return _state["eph"], _state["ts"]
    with _lock:
        if "eph" not in _state:
            path = _state.get("path") or _default_path()
            file = path if path.suffix == ".bsp" else path / EPHEMERIS_FILE
            if not file.exists():
                raise EphemerisNotAvailable(
                    f"Ephemeris file not found at {file}. Run `python manage.py download_ephemeris`."
                )
            loader = Loader(str(file.parent), verbose=False)
            _state["ts"] = loader.timescale(builtin=True)
            _state["eph"] = loader(file.name)
    return _state["eph"], _state["ts"]


def is_available() -> bool:
    try:
        _load()
        return True
    except EphemerisNotAvailable:
        return False


def timescale():
    return _load()[1]


def ephemeris():
    return _load()[0]


def to_time(dt: datetime):
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return timescale().from_datetime(dt)


def nutation_and_obliquity(t):
    """Return (nutation in longitude, true obliquity) in degrees."""
    dpsi, deps = iau2000a_radians(t)
    eps0 = mean_obliquity(t.tdb) / 3600.0
    return math.degrees(dpsi), eps0 + math.degrees(deps)


def true_ayanamsa(t, name: str = ayan.DEFAULT_AYANAMSA) -> float:
    dpsi, _ = nutation_and_obliquity(t)
    return ayan.mean_ayanamsa(name, t.tt) + dpsi


@dataclass
class BodyState:
    lon: float          # sidereal longitude (deg)
    lat: float          # ecliptic latitude (deg)
    speed: float        # deg/day (sidereal, ~ tropical)
    tropical_lon: float
    declination: float  # true equator of date (deg)


@dataclass
class Snapshot:
    """All positional data for one moment and place."""
    dt: datetime
    jd_ut: float
    jd_tt: float
    lat: float
    lon: float
    ayanamsa_name: str
    ayanamsa: float            # true ayanamsa (deg)
    obliquity: float           # true obliquity (deg)
    bodies: dict[str, BodyState] = field(default_factory=dict)
    ascendant: float = 0.0     # sidereal
    mc: float = 0.0            # sidereal
    helio: dict[str, float] = field(default_factory=dict)  # tropical heliocentric lon
    node_mode: str = "mean"


def _mean_node_tropical(jd_tt: float) -> float:
    t = (jd_tt - ayan.J2000) / 36525.0
    return norm(125.0445479 - 1934.1362891 * t + 0.0020754 * t**2
                + t**3 / 467441.0 - t**4 / 60616000.0)


def _true_node_tropical(earth, moon, t) -> np.ndarray:
    pos, vel = (moon - earth).at(t).frame_xyz_and_velocity(ecliptic_frame)
    r, v = pos.au, vel.au_per_d
    h = np.cross(r.T, v.T).T
    return np.degrees(np.arctan2(h[0], -h[1])) % 360.0


def compute_snapshot(dt: datetime, lat: float, lon: float,
                     ayanamsa_name: str = ayan.DEFAULT_AYANAMSA,
                     node_mode: str = "mean") -> Snapshot:
    eph, ts = _load()
    t = to_time(dt)
    step = 1.0 / 24.0  # finite-difference step for speeds (days)
    tt3 = ts.tt_jd(np.array([t.tt - step, t.tt, t.tt + step]))

    dpsi, eps = nutation_and_obliquity(t)
    mean_ay = ayan.mean_ayanamsa(ayanamsa_name, t.tt)
    true_ay = mean_ay + dpsi

    snap = Snapshot(dt=dt, jd_ut=t.ut1, jd_tt=t.tt, lat=lat, lon=lon,
                    ayanamsa_name=ayanamsa_name, ayanamsa=true_ay, obliquity=eps,
                    node_mode=node_mode)

    earth = eph["earth"]
    sun = eph["sun"]
    for code, key in _BODY_KEYS.items():
        body = eph[key]
        app = earth.at(tt3).observe(body).apparent()
        elat, elon, _ = app.frame_latlon(ecliptic_frame)
        lons = elon.degrees
        speed = (((lons[2] - lons[0] + 180.0) % 360.0) - 180.0) / (2 * step)
        _, dec, _ = app.radec(epoch="date")
        trop = float(lons[1])
        snap.bodies[code] = BodyState(
            lon=norm(trop - true_ay), lat=float(elat.degrees[1]), speed=float(speed),
            tropical_lon=trop, declination=float(dec.degrees[1]),
        )
        if code in (MA, ME, JU, VE, SA):
            vec = body.at(t).position.au - sun.at(t).position.au
            _, hlon, _ = ICRF(vec, t=t, center=10).frame_latlon(ecliptic_frame)
            snap.helio[code] = float(hlon.degrees)

    # Lunar nodes
    if node_mode == "true":
        nodes = _true_node_tropical(earth, eph["moon"], tt3)
        rahu_trop = float(nodes[1])
        rahu_speed = (((nodes[2] - nodes[0] + 180.0) % 360.0) - 180.0) / (2 * step)
        rahu_sid = norm(rahu_trop - true_ay)
    else:
        rahu_mean_trop = _mean_node_tropical(t.tt)
        rahu_trop = norm(rahu_mean_trop + dpsi)
        rahu_speed = -0.0529539
        rahu_sid = norm(rahu_mean_trop - mean_ay)
    for code, sid, trop in ((RA, rahu_sid, rahu_trop), (KE, norm(rahu_sid + 180), norm(rahu_trop + 180))):
        snap.bodies[code] = BodyState(
            lon=sid, lat=0.0, speed=float(rahu_speed), tropical_lon=trop,
            declination=math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(trop)))),
        )

    # Ascendant & MC from apparent sidereal time
    ramc = math.radians(norm(t.gast * 15.0 + lon))
    e = math.radians(eps)
    phi = math.radians(lat)
    asc = math.degrees(math.atan2(math.cos(ramc), -(math.sin(ramc) * math.cos(e) + math.tan(phi) * math.sin(e))))
    mc = math.degrees(math.atan2(math.sin(ramc), math.cos(ramc) * math.cos(e)))
    snap.ascendant = norm(asc - true_ay)
    snap.mc = norm(mc - true_ay)
    return snap


def sidereal_lon(code: str, t, ayanamsa_name: str = ayan.DEFAULT_AYANAMSA) -> float:
    """Quick single-body sidereal longitude (used by panchang time searches)."""
    eph, _ = _load()
    app = eph["earth"].at(t).observe(eph[_BODY_KEYS[code]]).apparent()
    _, elon, _ = app.frame_latlon(ecliptic_frame)
    return norm(float(elon.degrees) - true_ayanamsa(t, ayanamsa_name))


def sun_moon_tropical(t):
    """Vectorised tropical longitudes of Sun and Moon (arrays if t is an array)."""
    eph, _ = _load()
    earth = eph["earth"]
    out = []
    for key in ("sun", "moon"):
        _, elon, _ = earth.at(t).observe(eph[key]).apparent().frame_latlon(ecliptic_frame)
        out.append(elon.degrees)
    return out[0], out[1]


def observer(lat: float, lon: float):
    eph, _ = _load()
    return eph["earth"] + wgs84.latlon(lat, lon)
