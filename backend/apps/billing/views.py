import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ServiceError

from . import emails
from .services import record_razorpay_payment, refund_razorpay_payment, subscription_for

logger = logging.getLogger(__name__)

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


def _error(status: int, code: str, message: str) -> JsonResponse:
    return JsonResponse({"error": {"code": code, "message": message, "details": None}}, status=status)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Razorpay -> Pro. In Dashboard -> Webhooks, point a webhook here with the events payment.captured
    and refund.processed, and the same secret as RAZORPAY_WEBHOOK_SECRET.

    Answers 200 to anything correctly signed (even events it ignores) so Razorpay stops retrying."""
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        return _error(503, "not_configured", "Razorpay webhook is not configured.")
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get("X-Razorpay-Signature", "")):
        return _error(400, "invalid_signature", "Invalid signature.")
    try:
        body = json.loads(request.body)
        event = body.get("event")
        payload = body.get("payload") or {}
        if event == "payment.captured":
            record_razorpay_payment(payload["payment"]["entity"], body)
        elif event == "refund.processed":
            refund = payload["refund"]["entity"]
            payment = (payload.get("payment") or {}).get("entity") or {}
            # amount_refunded adds up several partial refunds that together cover the full price.
            refund_razorpay_payment(refund["payment_id"], payment.get("amount_refunded") or refund.get("amount") or 0)
    except (ValueError, KeyError, TypeError) as e:
        logger.warning("Razorpay webhook: malformed payload (%s)", e)
        return _error(400, "malformed", "Malformed payload.")
    return JsonResponse({"ok": True})


def _page(title: str, body: str) -> HttpResponse:
    return HttpResponse(
        f"<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)}</title><body style='font-family:system-ui,sans-serif;background:#F1ECE2;color:#2B2118;"
        f"display:flex;justify-content:center;padding:48px 16px'><div style='max-width:420px;background:#fff;"
        f"border-radius:16px;padding:28px 32px'><h1 style='font-size:20px;margin:0 0 10px'>{escape(title)}</h1>{body}</div>")


@csrf_exempt  # mail providers POST here for one-click unsubscribe (RFC 8058); the signed token is the proof
@require_http_methods(["GET", "POST"])
def premium_unsubscribe(request, token: str):
    """GET shows a confirm button (link scanners only GET, so they can't unsubscribe anyone); POST unsubscribes."""
    user = emails.user_for_token(token)
    if not user:
        return _page("Link not valid", "<p>This unsubscribe link is broken or out of date.</p>")
    if request.method == "POST":
        emails.unsubscribe(user)
        return _page("You're unsubscribed",
                     f"<p>We won't send {escape(user.email)} any more offers. Account emails, like sign-in codes, still arrive.</p>")
    return _page(f"Stop {escape(settings.APP_NAME)} offers?",
                 f"<p>{escape(user.email)} won't get any more emails about Pro.</p>"
                 "<form method='post'><button style='margin-top:12px;padding:12px 22px;border:0;border-radius:10px;"
                 f"background:{settings.EMAIL_ACCENT_COLOR};color:#fff;font-size:15px'>Unsubscribe</button></form>")
