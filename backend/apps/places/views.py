from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ServiceError
from apps.core.throttles import PlacesRateThrottle

from .serializers import CoordinatesSerializer, PlaceSerializer, TimezoneSerializer
from .services import resolve_timezone, search_places


class PlaceSearchView(APIView):
    # Public: the sign-up form picks birth and current places before an account exists.
    permission_classes = [AllowAny]
    throttle_classes = [PlacesRateThrottle]

    @extend_schema(
        parameters=[OpenApiParameter("q", str, description="City name, optionally 'City, State/Country'")],
        responses={200: PlaceSerializer(many=True)},
    )
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            raise ServiceError("Query must be at least 2 characters.", code="query_too_short")
        return Response({"results": PlaceSerializer(search_places(q), many=True).data})


class TimezoneLookupView(APIView):
    @extend_schema(parameters=[CoordinatesSerializer], responses={200: TimezoneSerializer})
    def get(self, request):
        ser = CoordinatesSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        return Response({"timezone": resolve_timezone(ser.validated_data["lat"], ser.validated_data["lon"])})
