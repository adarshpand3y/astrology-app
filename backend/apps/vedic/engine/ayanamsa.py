"""Ayanamsa models.

Each model returns the *mean* ayanamsa (relative to the mean equinox of date) in
degrees for a Julian date (TT). Nutation in longitude is added by the caller to
obtain the true ayanamsa used against true-equinox tropical longitudes.
"""

J2000 = 2451545.0


def _general_precession_arcsec(jd_tt: float) -> float:
    """IAU 2006 general precession in longitude p_A, arcseconds since J2000."""
    t = (jd_tt - J2000) / 36525.0
    return (5028.796195 * t + 1.1054348 * t**2 + 0.00007964 * t**3
            - 0.000023857 * t**4 - 0.0000000383 * t**5)


def _from_epoch(epoch_jd: float, value_deg: float):
    base = _general_precession_arcsec(epoch_jd)

    def model(jd_tt: float) -> float:
        return value_deg + (_general_precession_arcsec(jd_tt) - base) / 3600.0

    return model


# Lahiri (Chitrapaksha): 23 deg 15' 00.658" mean value at 1956-03-21 0h TT, as
# adopted by the Indian Calendar Reform Committee (Swiss Ephemeris reference).
lahiri = _from_epoch(2435553.5, 23.250182778 - 0.004658035)

AYANAMSAS = {
    "lahiri": lahiri,
    # "raman" / "kp" can be registered here later.
}

DEFAULT_AYANAMSA = "lahiri"


def mean_ayanamsa(name: str, jd_tt: float) -> float:
    try:
        return AYANAMSAS[name](jd_tt)
    except KeyError as exc:
        raise ValueError(f"Unsupported ayanamsa: {name}") from exc
