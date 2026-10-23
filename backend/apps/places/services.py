"""Place search and timezone resolution."""
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db.models import Q

from apps.core.exceptions import ServiceError

from .models import Place

MAX_RESULTS = 20


def search_places(query: str, limit: int = MAX_RESULTS):
    parts = [p.strip() for p in query.split(",") if p.strip()]
    if not parts:
        return []
    city, qualifiers = parts[0], parts[1:]
    base = Place.objects.all()
    for qual in qualifiers:
        base = base.filter(Q(admin1__icontains=qual) | Q(country__icontains=qual)
                           | Q(country_code__iexact=qual))
    prefix = Q(ascii_name__istartswith=city) | Q(name__istartswith=city)
    results = list(base.filter(prefix).order_by("-population")[:limit])
    if len(results) < limit:
        seen = [p.pk for p in results]
        results += list(base.filter(Q(ascii_name__icontains=city) | Q(name__icontains=city))
                        .exclude(pk__in=seen).order_by("-population")[:limit - len(results)])
    return results


@lru_cache(maxsize=1)
def _finder():
    from timezonefinder import TimezoneFinder
    return TimezoneFinder()


def resolve_timezone(lat: float, lon: float) -> str:
    tz = _finder().timezone_at(lat=lat, lng=lon) or _finder().certain_timezone_at(lat=lat, lng=lon)
    if not tz:
        raise ServiceError("Could not determine a timezone for these coordinates.", code="timezone_unknown")
    return tz


def validate_tz(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ServiceError(f"Unknown timezone '{name}'.", code="invalid_timezone") from exc


def local_to_utc(d: date, t: time, tz_name: str) -> tuple[datetime, int]:
    """Convert local civil date/time to an aware UTC datetime and UTC offset (minutes).

    Uses the IANA database, so historical offsets and DST are honoured. For
    ambiguous times (DST fall-back) the first occurrence is used.
    """
    tz = validate_tz(tz_name)
    local = datetime.combine(d, t).replace(tzinfo=tz, fold=0)
    offset: timedelta = local.utcoffset()
    return local.astimezone(ZoneInfo("UTC")), int(offset.total_seconds() // 60)
