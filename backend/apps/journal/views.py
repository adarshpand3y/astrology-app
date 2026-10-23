from datetime import date
from zoneinfo import ZoneInfo

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ServiceError
from apps.daily.context import request_lang, resolve_profile
from apps.daily.services import natal
from apps.remedies.views import local_today

from . import services
from .models import JournalEntry


class EntrySerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(max_length=30), max_length=12, required=False)

    class Meta:
        model = JournalEntry
        fields = ["date", "rating", "tags", "note", "updated_at"]
        read_only_fields = ["date", "updated_at"]


def _parse(day: str) -> date:
    try:
        return date.fromisoformat(day)
    except ValueError as exc:
        raise ServiceError("Invalid date; use YYYY-MM-DD.", code="invalid_date") from exc


class JournalDayView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="Entry for a day (null if none) and suggested tags")
    def get(self, request, day):
        entry = JournalEntry.objects.filter(user=request.user, date=_parse(day)).first()
        lang = request_lang(request)
        return Response({"entry": EntrySerializer(entry).data if entry else None,
                         "suggested_tags": services.DEFAULT_TAGS[lang]})

    @extend_schema(request=EntrySerializer, responses={200: EntrySerializer}, summary="Create or update a day's entry")
    def put(self, request, day):
        d = _parse(day)
        if d > local_today(request):
            raise ServiceError("You can't log a future day.", code="future_date")
        entry = JournalEntry.objects.filter(user=request.user, date=d).first()
        ser = EntrySerializer(entry, data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(user=request.user, date=d)
        return Response(ser.data)


class TrendsView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT},
                   summary="Mood and remedies done/due over the last N days (?days=7-90) with insights")
    def get(self, request):
        try:
            days = max(7, min(int(request.query_params.get("days", 14)), 90))
        except ValueError:
            days = 14
        profile = resolve_profile(request, required=False)
        moon_sign = natal(profile)["moon_sign"] if profile else None
        place = request.user.current_place
        tz = ZoneInfo(place.timezone if place else (profile.tz_name if profile else "UTC"))
        return Response(services.trends(request.user, local_today(request), days, request_lang(request), moon_sign, tz))
