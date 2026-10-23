from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ServiceError

from .services import subscription_for

FEATURES = [  # (key, free?)
    ("daily_insight", True), ("muhurta", True), ("panchang", True), ("decision", False),
    ("dasha_full", False), ("vargas", False), ("remedies", False), ("transit_alerts", False),
]


def billing_payload(user) -> dict:
    sub = subscription_for(user)
    return {
        "plan": sub.plan,
        "is_pro": sub.is_pro,
        "on_trial": sub.on_trial,
        "trial_available": sub.trial_available,
        "trial_ends_at": sub.trial_ends_at,
        "pro_until": sub.pro_until,
        "trial_days": settings.PRO_TRIAL_DAYS,
        "prices": {
            "currency": settings.PRO_CURRENCY,
            "monthly": settings.PRO_PRICE_MONTHLY,
            "annual": settings.PRO_PRICE_ANNUAL,
        },
        "features": [{"key": k, "free": free} for k, free in FEATURES],
    }


class BillingView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="Current plan, trial and prices")
    def get(self, request):
        return Response(billing_payload(request.user))


class StartTrialView(APIView):
    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT}, summary="Start the free Pro trial (once)")
    def post(self, request):
        sub = subscription_for(request.user)
        if not sub.trial_available:
            raise ServiceError("The free trial has already been used.", code="trial_used")
        sub.start_trial(settings.PRO_TRIAL_DAYS)
        return Response(billing_payload(request.user))
