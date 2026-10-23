from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import is_pro, require_pro
from apps.core.exceptions import ServiceError
from apps.daily.context import request_lang
from apps.core.throttles import ComputeRateThrottle
from apps.places.services import local_to_utc, resolve_timezone, validate_tz
from apps.profiles.models import BirthProfile

from . import services
from .engine.vargas import VARGA_CODES
from .serializers import (
    ChartQuerySerializer, DashaCurrentQuerySerializer, DashaDrillQuerySerializer,
    DashaTreeQuerySerializer, PanchangRequestSerializer,
)


class ProfileComputeView(APIView):
    throttle_classes = [ComputeRateThrottle]

    def get_profile(self, pk) -> BirthProfile:
        return get_object_or_404(BirthProfile, pk=pk, owner=self.request.user)

    def query(self, serializer_cls):
        ser = serializer_cls(data=self.request.query_params)
        ser.is_valid(raise_exception=True)
        return ser.validated_data


class ChartView(ProfileComputeView):
    @extend_schema(parameters=[ChartQuerySerializer], responses={200: OpenApiTypes.OBJECT},
                   summary="Birth chart: planets, lagna, houses, bhava chalit, vargas, panchang, avakhada")
    def get(self, request, pk):
        params = self.query(ChartQuerySerializer)
        chart = services.get_chart(self.get_profile(pk))
        codes = params.get("vargas") or list(chart["vargas"])
        if not is_pro(request.user):
            codes = [c for c in codes if c == "D1"]  # divisional charts are Pro
        chart = {**chart, "vargas": {c: chart["vargas"][c] for c in codes}, "vargas_locked": not is_pro(request.user)}
        return Response(chart)


class VargaView(ProfileComputeView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="A single divisional chart")
    def get(self, request, pk, code):
        code = code.upper()
        if code not in VARGA_CODES:
            raise ServiceError(f"Unknown varga {code}.", code="unknown_varga")
        if code != "D1":
            require_pro(request.user)
        chart = services.get_chart(self.get_profile(pk))
        return Response(chart["vargas"][code])


class DashaTreeView(ProfileComputeView):
    @extend_schema(parameters=[DashaTreeQuerySerializer], responses={200: OpenApiTypes.OBJECT},
                   summary="Vimshottari periods to the requested depth (1=MD, 2=AD, 3=PD)")
    def get(self, request, pk):
        params = self.query(DashaTreeQuerySerializer)
        return Response(services.get_dasha_tree(self.get_profile(pk), params["depth"]))


class DashaDrillView(ProfileComputeView):
    @extend_schema(parameters=[DashaDrillQuerySerializer], responses={200: OpenApiTypes.OBJECT},
                   summary="Sub-periods of one period (drill down to sookshma and prana)")
    def get(self, request, pk):
        params = self.query(DashaDrillQuerySerializer)
        if len(params["path"].split("/")) >= 2:  # pratyantardasha and deeper are Pro
            require_pro(request.user)
        return Response(services.get_dasha_children(self.get_profile(pk), params["path"].split("/")))


class DashaCurrentView(ProfileComputeView):
    @extend_schema(parameters=[DashaCurrentQuerySerializer], responses={200: OpenApiTypes.OBJECT},
                   summary="Running MD/AD/PD/SD/Prana at a moment")
    def get(self, request, pk):
        params = self.query(DashaCurrentQuerySerializer)
        at = params.get("at") or timezone.now()
        return Response(services.get_current_dasha(self.get_profile(pk), at))


class ShadbalaView(ProfileComputeView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="Shadbala of the seven planets")
    def get(self, request, pk):
        return Response(services.get_strengths(self.get_profile(pk))["shadbala"])


class BhavabalaView(ProfileComputeView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="Bhava Bala of the twelve houses")
    def get(self, request, pk):
        return Response(services.get_strengths(self.get_profile(pk))["bhavabala"])


class PanchangView(APIView):
    throttle_classes = [ComputeRateThrottle]

    @extend_schema(request=PanchangRequestSerializer, responses={200: OpenApiTypes.OBJECT},
                   summary="Panchang for any moment and place")
    def post(self, request):
        ser = PanchangRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        tz_name = d.get("tz_name") or resolve_timezone(d["latitude"], d["longitude"])
        tz = validate_tz(tz_name)
        now_local = timezone.now().astimezone(tz)
        dt_utc, _ = local_to_utc(d.get("date") or now_local.date(),
                                 d.get("time") or now_local.time().replace(microsecond=0), tz_name)
        return Response(services.day_panchang(dt_utc, d["latitude"], d["longitude"], tz_name, d["ayanamsa"]))


class StrengthReportView(ProfileComputeView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT},
                   summary="Shadbala + Bhava Bala with status, six sources and what to do")
    def get(self, request, pk):
        return Response(services.strength_report(self.get_profile(pk), request_lang(request)))
