import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions, status

from .models import RazorpayPayment, Subscription

logger = logging.getLogger(__name__)


class ProRequired(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "pro_required"
    default_detail = "This feature is part of Pro."


def subscription_for(user) -> Subscription:
    sub, _ = Subscription.objects.get_or_create(user=user)
    return sub


def is_pro(user) -> bool:
    return bool(user and user.is_authenticated and subscription_for(user).is_pro)


def require_pro(user) -> None:
    if not is_pro(user):
        raise ProRequired()


# --- Website payments (Razorpay) ----------------------------------------------------------------

def plan_days(amount_paise: int, currency: str) -> int:
    """Pro days bought by a payment, by amount alone (never by anything the customer typed); 0 = no plan."""
    if currency.upper() != settings.PRO_CURRENCY.upper():
        return 0
    return settings.RAZORPAY_PLANS.get(amount_paise, 0)


def _can_receive(user) -> bool:
    # Only an account that proved it owns the email gets what was paid for with it.
    return user.is_active and (user.is_email_verified or not settings.REQUIRE_EMAIL_VERIFICATION)


def extend_pro(user, days: int, source: str) -> Subscription:
    """Add `days` of paid Pro after any paid time already left (a lifetime grant stays lifetime)."""
    sub = Subscription.objects.select_for_update().get(pk=subscription_for(user).pk)
    if sub.plan == Subscription.Plan.PRO and sub.pro_until is None:
        return sub
    now = timezone.now()
    start = max(now, sub.pro_until) if sub.plan == Subscription.Plan.PRO and sub.pro_until else now
    sub.plan = Subscription.Plan.PRO
    sub.pro_until = start + timedelta(days=days)
    sub.source = source
    sub.save()
    return sub


def _apply(payment: RazorpayPayment, user) -> None:
    extend_pro(user, payment.days, "razorpay")
    payment.user = user
    payment.applied_at = timezone.now()
    payment.save(update_fields=["user", "applied_at"])
    logger.info("Razorpay %s: %s days of Pro for %s", payment.payment_id, payment.days, user.email)


@transaction.atomic
def record_razorpay_payment(entity: dict, payload: dict) -> RazorpayPayment:
    """Store a captured payment once (Razorpay retries webhooks) and grant Pro if the account exists."""
    notes = entity.get("notes")
    notes = notes if isinstance(notes, dict) else {}
    # A Payment Page field named "app_email" lets buyers give the email they sign in with, if it differs.
    email = (notes.get("app_email") or notes.get("email") or entity.get("email") or "").strip().lower()
    amount, currency = entity.get("amount") or 0, entity.get("currency") or ""
    payment, created = RazorpayPayment.objects.select_for_update().get_or_create(
        payment_id=entity["id"],
        defaults={"email": email, "amount": amount, "currency": currency,
                  "days": plan_days(amount, currency), "payload": payload},
    )
    if not created or payment.applied_at or payment.refunded_at:
        return payment
    if not payment.days:
        logger.warning("Razorpay %s: %s %s matches no plan; not applied", payment.payment_id, amount, currency)
        return payment
    from apps.accounts.models import User
    user = User.objects.filter(email__iexact=email).first() if email else None
    if user and _can_receive(user):
        _apply(payment, user)
    else:
        logger.info("Razorpay %s: no verified account for %r yet; held", payment.payment_id, email)
    return payment


@transaction.atomic
def refund_razorpay_payment(payment_id: str, refunded_paise: int) -> RazorpayPayment | None:
    """A full refund takes the payment's Pro days back; partial refunds are left to the admin."""
    payment = RazorpayPayment.objects.select_for_update().filter(payment_id=payment_id).first()
    if not payment or payment.refunded_at:
        return payment
    if refunded_paise < payment.amount:
        logger.warning("Razorpay %s: partial refund (%s of %s); Pro unchanged", payment_id, refunded_paise, payment.amount)
        return payment
    payment.refunded_at = timezone.now()
    payment.save(update_fields=["refunded_at"])
    if payment.applied_at and payment.user:
        sub = Subscription.objects.select_for_update().get(pk=subscription_for(payment.user).pk)
        if sub.plan == Subscription.Plan.PRO and sub.pro_until:
            sub.pro_until = max(timezone.now(), sub.pro_until - timedelta(days=payment.days))
            sub.save()
    return payment


@transaction.atomic
def apply_pending_payments(user) -> int:
    """Grant website purchases made before this email had a verified account. Returns how many."""
    if not _can_receive(user):
        return 0
    pending = list(RazorpayPayment.objects.select_for_update().filter(
        email__iexact=user.email, applied_at__isnull=True, refunded_at__isnull=True, days__gt=0))
    for payment in pending:
        _apply(payment, user)
    return len(pending)
