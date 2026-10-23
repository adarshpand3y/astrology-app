from datetime import datetime, timedelta, timezone


def norm(deg: float) -> float:
    """Normalise an angle to [0, 360)."""
    deg = deg % 360.0
    return 0.0 if deg >= 360.0 else deg


def arc(a: float, b: float) -> float:
    """Shortest angular distance between two longitudes, 0..180."""
    d = abs(norm(a) - norm(b))
    return 360.0 - d if d > 180.0 else d


def sign_of(lon: float) -> int:
    return int(norm(lon) // 30) % 12


def deg_in_sign(lon: float) -> float:
    return norm(lon) % 30.0


def dms(deg: float) -> str:
    """Format degrees (within a sign or absolute) as D°M'S"."""
    total = round(abs(deg) * 3600)
    d, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    sign = "-" if deg < 0 else ""
    return f"{sign}{d}°{m:02d}'{s:02d}\""


def house_from(sign: int, ref_sign: int) -> int:
    """1-based house number of ``sign`` counted from ``ref_sign``."""
    return (sign - ref_sign) % 12 + 1


JD_UNIX_EPOCH = 2440587.5


def jd_to_datetime(jd_ut: float) -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=jd_ut - JD_UNIX_EPOCH)


def datetime_to_jd(dt: datetime) -> float:
    dt = dt.astimezone(timezone.utc)
    return JD_UNIX_EPOCH + (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds() / 86400.0


def iso(dt: datetime | None, tz=None) -> str | None:
    if dt is None:
        return None
    if tz is not None:
        dt = dt.astimezone(tz)
    return dt.isoformat(timespec="seconds")
