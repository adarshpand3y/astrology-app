from datetime import date

from rest_framework import serializers

from apps.places.models import Place
from apps.places.services import local_to_utc, resolve_timezone, validate_tz
from apps.vedic.engine.ayanamsa import AYANAMSAS

from .models import BirthProfile

# de440s.bsp coverage, with a margin for dasha/panchang searches
MIN_DATE, MAX_DATE = date(1850, 1, 1), date(2149, 12, 31)

BIRTH_FIELDS = ("birth_date", "birth_time", "latitude", "longitude", "tz_name", "ayanamsa")


class BirthProfileSerializer(serializers.ModelSerializer):
    place_id = serializers.PrimaryKeyRelatedField(
        source="place", queryset=Place.objects.all(), required=False, allow_null=True)
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)
    tz_name = serializers.CharField(max_length=64, required=False)
    ayanamsa = serializers.ChoiceField(choices=sorted(AYANAMSAS), default="lahiri")

    class Meta:
        model = BirthProfile
        fields = [
            "id", "name", "gender", "relation", "birth_date", "birth_time",
            "place_id", "place_label", "latitude", "longitude", "tz_name",
            "utc_offset_minutes", "birth_utc", "ayanamsa", "notes", "goals", "goals_chosen_at",
            "created_at", "updated_at",
        ]
        # Goals are set through PUT /remedies/goals/?profile=<id>, which also suggests their remedies.
        read_only_fields = ["id", "utc_offset_minutes", "birth_utc", "goals", "goals_chosen_at",
                            "created_at", "updated_at"]

    def validate_birth_date(self, value):
        if not (MIN_DATE <= value <= MAX_DATE):
            raise serializers.ValidationError(f"Birth date must be between {MIN_DATE} and {MAX_DATE}.")
        return value

    def validate(self, attrs):
        inst = self.instance
        get = lambda k: attrs.get(k, getattr(inst, k, None) if inst else None)  # noqa: E731

        place = attrs.get("place")
        if place is not None:
            attrs.setdefault("latitude", place.latitude)
            attrs.setdefault("longitude", place.longitude)
            attrs.setdefault("tz_name", place.timezone)
            attrs.setdefault("place_label", place.label)

        if get("latitude") is None or get("longitude") is None:
            raise serializers.ValidationError("Provide place_id or latitude and longitude.")
        if "tz_name" in attrs:
            validate_tz(attrs["tz_name"])
        elif not get("tz_name") or {"latitude", "longitude"} & attrs.keys():
            attrs["tz_name"] = resolve_timezone(get("latitude"), get("longitude"))

        if get("birth_date") is None:
            raise serializers.ValidationError({"birth_date": "This field is required."})
        birth_utc, offset = local_to_utc(get("birth_date"), get("birth_time"), get("tz_name"))
        attrs["birth_utc"], attrs["utc_offset_minutes"] = birth_utc, offset
        return attrs
