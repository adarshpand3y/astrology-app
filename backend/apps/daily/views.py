from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import require_pro
from apps.core.throttles import ComputeRateThrottle
from apps.vedic.content.activities import ACTIVITIES, RANGES
from apps.vedic.services import _run

from . import services
from .context import resolve

DAY_PARAMS = [
    OpenApiParameter("date", str, description="YYYY-MM-DD (local). Default: today"),
    OpenApiParameter("profile", str, description="Profile id. Default: active profile"),
    OpenApiParameter("place_id", int, description="Override location. Default: user's current place"),
    OpenApiParameter("lang", str, description="en | hi (or Accept-Language)"),
]


class _DailyView(APIView):
    throttle_classes = [ComputeRateThrottle]


class HomeView(_DailyView):
    @extend_schema(parameters=DAY_PARAMS, responses={200: OpenApiTypes.OBJECT},
                   summary="Home: insight, current period, live transit, today's windows")
    def get(self, request):
        ctx = resolve(request)
        return Response(_run(lambda: services.home(ctx)))


class TimelineView(_DailyView):
    @extend_schema(parameters=DAY_PARAMS, responses={200: OpenApiTypes.OBJECT},
                   summary="Day timeline: choghadiya, Rahu Kaal, Yamaganda, Gulika, Abhijit")
    def get(self, request):
        ctx = resolve(request, profile_required=False)
        return Response(_run(lambda: services.timeline(ctx)))


class PanchangView(_DailyView):
    @extend_schema(parameters=DAY_PARAMS, responses={200: OpenApiTypes.OBJECT},
                   summary="Panchang for the day at the user's location, with interpretation")
    def get(self, request):
        ctx = resolve(request, profile_required=False)
        return Response(_run(lambda: services.panchang(ctx)))


class DecisionSerializer(serializers.Serializer):
    activity = serializers.ChoiceField(choices=list(ACTIVITIES))
    range = serializers.ChoiceField(choices=list(RANGES), default="week")


class DecisionView(_DailyView):
    @extend_schema(request=DecisionSerializer, parameters=DAY_PARAMS, responses={200: OpenApiTypes.OBJECT},
                   summary="Best time to…: ranked windows for an activity (Pro)")
    def post(self, request):
        require_pro(request.user)
        ser = DecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ctx = resolve(request)
        return Response(_run(lambda: services.decision(ctx, ser.validated_data["activity"],
                                                       ser.validated_data["range"])))


class TransitsView(_DailyView):
    @extend_schema(parameters=DAY_PARAMS, responses={200: OpenApiTypes.OBJECT},
                   summary="Current transits against the natal chart, with Sade Sati status")
    def get(self, request):
        ctx = resolve(request)
        return Response(_run(lambda: services.transits(ctx)))
