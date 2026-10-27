import hashlib
import hmac
import json
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.models import RazorpayPayment
from apps.billing.services import apply_pending_payments, subscription_for

pytestmark = pytest.mark.django_db

URL = "/api/v1/billing/webhooks/razorpay/"
SECRET = "whsec-test"
MONTHLY, ANNUAL = 29900, 249900


@pytest.fixture(autouse=True)
def razorpay_settings(settings):
    settings.RAZORPAY_WEBHOOK_SECRET = SECRET
    settings.RAZORPAY_PLANS = {MONTHLY: 30, ANNUAL: 365}
    settings.PRO_CURRENCY = "INR"


def _post(body: dict, secret: str = SECRET):
    raw = json.dumps(body).encode()
    sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return APIClient().generic("POST", URL, raw, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE=sig)


def captured(pid="pay_1", email="asha@example.com", amount=MONTHLY, notes=None):
    return {"event": "payment.captured", "payload": {"payment": {"entity": {
        "id": pid, "amount": amount, "currency": "INR", "email": email, "notes": notes or [], "status": "captured"}}}}


def refunded(pid="pay_1", amount=MONTHLY):
    return {"event": "refund.processed", "payload": {
        "refund": {"entity": {"id": "rfnd_1", "payment_id": pid, "amount": amount}},
        "payment": {"entity": {"id": pid, "amount": amount, "amount_refunded": amount}}}}


@pytest.fixture
def user():
    return User.objects.create_user("asha@example.com", "Str0ng-pass-123", is_email_verified=True)


def _days_left(u):
    # Rounded: Windows' clock can return the same instant twice, so .days flips between 29 and 30.
    return round((subscription_for(u).pro_until - timezone.now()).total_seconds() / 86400)


def test_rejects_bad_signature_and_unconfigured(settings, user):
    assert _post(captured(), secret="wrong").status_code == 400
    settings.RAZORPAY_WEBHOOK_SECRET = ""
    assert _post(captured()).status_code == 503
    assert not subscription_for(user).is_pro


def test_payment_grants_pro_once(user):
    assert _post(captured()).status_code == 200
    assert subscription_for(user).is_pro and subscription_for(user).source == "razorpay"
    assert _days_left(user) == 30
    assert _post(captured()).status_code == 200  # Razorpay retry: no second month
    assert _days_left(user) == 30


def test_second_payment_extends_remaining_time(user):
    _post(captured("pay_1"))
    _post(captured("pay_2", amount=ANNUAL))
    assert _days_left(user) == 30 + 365


def test_lifetime_grant_stays_lifetime(user):
    sub = subscription_for(user)
    sub.plan, sub.pro_until = "pro", None
    sub.save()
    _post(captured())
    assert subscription_for(user).pro_until is None


def test_unknown_amount_is_recorded_not_applied(user):
    assert _post(captured(amount=12345)).status_code == 200
    p = RazorpayPayment.objects.get(payment_id="pay_1")
    assert p.days == 0 and p.applied_at is None
    assert not subscription_for(user).is_pro


def test_app_email_note_wins_over_checkout_email(user):
    _post(captured(email="someone-else@example.com", notes={"app_email": "Asha@Example.com"}))
    assert subscription_for(user).is_pro


def test_held_until_the_email_is_verified():
    _post(captured(email="new@example.com"))
    assert RazorpayPayment.objects.get().applied_at is None
    u = User.objects.create_user("new@example.com", "Str0ng-pass-123", is_email_verified=False)
    assert apply_pending_payments(u) == 0  # not proven to own the mailbox yet
    u.is_email_verified = True
    u.save()
    assert apply_pending_payments(u) == 1
    assert subscription_for(u).is_pro
    assert apply_pending_payments(u) == 0


def test_full_refund_takes_the_days_back(user):
    _post(captured("pay_1"))
    _post(captured("pay_2", amount=ANNUAL))
    assert _post(refunded("pay_2", ANNUAL)).status_code == 200
    assert _days_left(user) == 30
    _post(refunded("pay_2", ANNUAL))  # retry: no double revoke
    assert _days_left(user) == 30


def test_partial_refund_leaves_pro(user):
    _post(captured())
    body = refunded(amount=MONTHLY)
    body["payload"]["payment"]["entity"]["amount_refunded"] = 10000
    _post(body)
    assert _days_left(user) == 30
    assert RazorpayPayment.objects.get().refunded_at is None


def test_refund_before_apply_stops_a_held_payment():
    _post(captured(email="later@example.com"))
    _post(refunded())
    u = User.objects.create_user("later@example.com", "Str0ng-pass-123", is_email_verified=True)
    assert apply_pending_payments(u) == 0


@override_settings(MIN_APP_VERSION="9.0.0", MIN_APP_VERSIONS={"android": "", "ios": ""})
def test_webhook_skips_the_app_version_gate(user):
    assert _post(captured()).status_code == 200
    assert subscription_for(user).is_pro
    assert timezone.now() + timedelta(days=28) < subscription_for(user).pro_until
