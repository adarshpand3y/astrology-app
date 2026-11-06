from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import is_pro, require_pro
from apps.daily.context import resolve
from apps.vedic.services import _run

from . import services
from .models import AlertPreference


class PrefsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertPreference
        fields = ["dasha", "transit", "rahu", "sade_sati", "daily", "periods", "periods_night", "remedies", "vrat", "daily_time", "remedy_time", "rahu_lead_minutes"]


def prefs_payload(prefs: AlertPreference, user) -> dict:
    """Preferences as they take effect: on the free plan the Pro-only alerts read as off (the stored
    choice is kept, so they come back on with Pro)."""
    pro = is_pro(user)
    data = PrefsSerializer(prefs).data
    if not pro:
        data.update({f: False for f in AlertPreference.PRO_FIELDS})
    return {**data, "pro_fields": list(AlertPreference.PRO_FIELDS), "is_pro": pro}


class PrefsView(APIView):
    @extend_schema(responses={200: PrefsSerializer})
    def get(self, request):
        return Response(prefs_payload(services.prefs_for(request.user), request.user))

    @extend_schema(request=PrefsSerializer, responses={200: PrefsSerializer},
                   summary="Update alert preferences (transit & Sade Sati need Pro)")
    def patch(self, request):
        prefs = services.prefs_for(request.user)
        ser = PrefsSerializer(prefs, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        if any(ser.validated_data.get(f) for f in AlertPreference.PRO_FIELDS):
            require_pro(request.user)
        return Response(prefs_payload(ser.save(), request.user))


class ScheduleView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT},
                   summary="Upcoming notifications for the phone to schedule locally")
    def get(self, request):
        days = max(1, min(int(request.query_params.get("days", 7)), 14))
        ctx = resolve(request, profile_required=False)
        return Response({"items": _run(lambda: services.schedule(ctx, days))})
