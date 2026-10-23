from rest_framework import serializers

from .models import Place


class PlaceSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)

    class Meta:
        model = Place
        fields = ["id", "name", "admin1", "country", "country_code", "latitude", "longitude",
                  "timezone", "population", "label"]


class CoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)


class TimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField()
