from datetime import timezone as dt_timezone

from django.utils import timezone
from rest_framework import serializers

from apps.places.models import Place

from .engine.ayanamsa import AYANAMSAS
from .engine.vargas import VARGA_CODES


class ChartQuerySerializer(serializers.Serializer):
    vargas = serializers.CharField(required=False, help_text="Comma separated, e.g. D9,D10. Default: all.")

    def validate_vargas(self, value):
        codes = [c.strip().upper() for c in value.split(",") if c.strip()]
        bad = [c for c in codes if c not in VARGA_CODES]
        if bad:
            raise serializers.ValidationError(f"Unknown vargas: {', '.join(bad)}")
        return codes


class DashaTreeQuerySerializer(serializers.Serializer):
    depth = serializers.IntegerField(min_value=1, max_value=3, default=2)


class DashaDrillQuerySerializer(serializers.Serializer):
    path = serializers.RegexField(r"^(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)(/(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)){0,3}$",
                                  help_text="Lord path of the parent period, e.g. Ve/Su/Mo")


class DashaCurrentQuerySerializer(serializers.Serializer):
    at = serializers.DateTimeField(required=False, help_text="ISO datetime; defaults to now.")

    def validate_at(self, value):
        return value if timezone.is_aware(value) else timezone.make_aware(value, dt_timezone.utc)


class PanchangRequestSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, help_text="Local date at the place; defaults to today.")
    time = serializers.TimeField(required=False, help_text="Local time at the place; defaults to now.")
    place_id = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all(), required=False)
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)
    tz_name = serializers.CharField(required=False)
    ayanamsa = serializers.ChoiceField(choices=sorted(AYANAMSAS), default="lahiri")

    def validate(self, attrs):
        place = attrs.pop("place_id", None)
        if place:
            attrs.setdefault("latitude", place.latitude)
            attrs.setdefault("longitude", place.longitude)
            attrs.setdefault("tz_name", place.timezone)
        if attrs.get("latitude") is None or attrs.get("longitude") is None:
            raise serializers.ValidationError("Provide place_id or latitude and longitude.")
        return attrs
