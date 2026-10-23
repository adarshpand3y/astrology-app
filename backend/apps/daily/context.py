"""Resolve whose chart, which place and which day a daily request is about."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from django.utils import timezone as dj_tz

from apps.core.exceptions import ServiceError
from apps.places.models import Place
from apps.places.services import resolve_timezone, validate_tz
from apps.profiles.models import BirthProfile
from apps.vedic.content.common import norm_lang


@dataclass
class DayContext:
    user: object
    profile: BirthProfile | None
    lang: str
    tz_name: str
    lat: float
    lon: float
    place_label: str
    place_city: str
    place_region: str
    day: date
    now: datetime  # aware UTC; "now" if day is today, else local noon of that day

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.tz_name)

    @property
    def is_today(self) -> bool:
        return self.day == dj_tz.now().astimezone(self.tz).date()

    def local_midnight(self) -> datetime:
        return datetime.combine(self.day, time(0), tzinfo=self.tz)


def request_lang(request) -> str:
    return norm_lang(request.query_params.get("lang") or request.headers.get("Accept-Language"))


def resolve_profile(request, required: bool = True) -> BirthProfile | None:
    user = request.user
    pid = request.query_params.get("profile") or (request.data.get("profile") if hasattr(request, "data") and isinstance(request.data, dict) else None)
    qs = BirthProfile.objects.filter(owner=user)
    profile = None
    if pid:
        profile = qs.filter(pk=pid).first()
        if profile is None:
            raise ServiceError("Unknown profile.", code="unknown_profile")
    else:
        profile = user.active_profile or qs.order_by("created_at").first()
    if profile is None and required:
        raise ServiceError("Add a birth profile first.", code="profile_required")
    return profile


def resolve(request, profile_required: bool = True) -> DayContext:
    user = request.user
    params = request.query_params
    profile = resolve_profile(request, profile_required)

    place = None
    if params.get("place_id"):
        place = Place.objects.filter(pk=params["place_id"]).first()
    if place is not None:
        lat, lon, tz_name = place.latitude, place.longitude, place.timezone
        label, city, region = place.label, place.ascii_name or place.name, place.admin1 or place.country
    elif params.get("lat") and params.get("lon"):
        lat, lon = float(params["lat"]), float(params["lon"])
        tz_name = params.get("tz") or resolve_timezone(lat, lon)
        label, city, region = f"{lat:.2f}, {lon:.2f}", f"{lat:.2f}, {lon:.2f}", ""
    elif user.current_place_id:
        p = user.current_place
        lat, lon, tz_name = p.latitude, p.longitude, p.timezone
        label, city, region = p.label, p.ascii_name or p.name, p.admin1 or p.country
    elif profile is not None:
        lat, lon, tz_name = profile.latitude, profile.longitude, profile.tz_name
        label = profile.place_label or f"{lat:.2f}, {lon:.2f}"
        city, region = label.split(",")[0], ", ".join(label.split(",")[1:2]).strip()
    else:
        raise ServiceError("Choose where you live to see daily timings.", code="location_required")
    validate_tz(tz_name)
    tz = ZoneInfo(tz_name)

    today = dj_tz.now().astimezone(tz).date()
    day = today
    if params.get("date"):
        try:
            day = date.fromisoformat(params["date"])
        except ValueError as exc:
            raise ServiceError("Invalid date; use YYYY-MM-DD.", code="invalid_date") from exc
    now = dj_tz.now() if day == today else datetime.combine(day, time(12, 0), tzinfo=tz).astimezone(timezone.utc)

    return DayContext(user=user, profile=profile, lang=request_lang(request), tz_name=tz_name, lat=lat, lon=lon,
                      place_label=label, place_city=city, place_region=region, day=day, now=now)
