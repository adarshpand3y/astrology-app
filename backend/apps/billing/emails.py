"""The "unlock Pro on the website" email sequence for free users.

Emails go out from the server, never from the app, so they can link straight to the website
checkout (PREMIUM_CHECKOUT_URL). The first one goes when the account is verified; later ones on
the day offsets in PREMIUM_EMAIL_DAYS, sent by `manage.py send_premium_emails` (run it hourly).
Off until PREMIUM_CHECKOUT_URL is set. Stops once the user has Pro or unsubscribes.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import PremiumEmailState
from .services import subscription_for

logger = logging.getLogger(__name__)

UNSUBSCRIBE_SALT = "premium-emails-unsubscribe"

# Wording per position in the sequence (the first email, then reminders); the layout is in
# templates/billing/email/premium.{html,txt}.
_COPY = [
    {
        "subject": "Complete your {app_name} registration to unlock Pro",
        "heading": "Your chart is ready. Unlock all of it.",
        "intro": "Complete your registration on our website to unlock premium features. Pro turns on in the app "
                 "as soon as you pay; sign in with this email ({email}).",
        "cta": "Complete registration",
    },
    {
        "subject": "Your full {app_name} reading is waiting",
        "heading": "See every dasha and every divisional chart",
        "intro": "You've started with the free plan. Pro opens the rest of your chart and keeps your remedies "
                 "on track. It unlocks in the app straight away for {email}.",
        "cta": "Unlock Pro",
    },
]
FEATURES = [
    "Every dasha level, down to the smallest sub-period",
    "All divisional charts, D2 to D60",
    "Remedy tracking with edits and custom remedies",
    "The decision assistant and transit alerts",
]


def enabled() -> bool:
    return bool(settings.PREMIUM_CHECKOUT_URL)


def checkout_url(email: str) -> str:
    # The link may carry an {email} placeholder to pre-fill the checkout.
    return settings.PREMIUM_CHECKOUT_URL.replace("{email}", quote(email))


def unsubscribe_url(user) -> str:
    token = signing.dumps(str(user.pk), salt=UNSUBSCRIBE_SALT)
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}{reverse('premium-unsubscribe', args=[token])}"


def user_for_token(token: str):
    from apps.accounts.models import User
    try:
        return User.objects.filter(pk=signing.loads(token, salt=UNSUBSCRIBE_SALT)).first()
    except signing.BadSignature:
        return None


def _eligible(user, state: PremiumEmailState) -> bool:
    verified = user.is_email_verified or not settings.REQUIRE_EMAIL_VERIFICATION
    return user.is_active and verified and not state.unsubscribed_at and not subscription_for(user).is_pro


def _due_step(user, state: PremiumEmailState, now) -> int | None:
    """The latest step that is due and not yet sent; earlier unsent ones are skipped, never sent in a burst."""
    due = [d for d in settings.PREMIUM_EMAIL_DAYS
           if d not in state.steps_sent and user.date_joined + timedelta(days=d) <= now]
    return max(due) if due else None


def _message(user, position: int) -> EmailMultiAlternatives:
    names = {"app_name": settings.APP_NAME, "email": user.email}
    copy = {k: v.format(**names) for k, v in _COPY[min(position, len(_COPY) - 1)].items()}
    unsubscribe = unsubscribe_url(user)
    context = {**copy, **names, "url": checkout_url(user.email), "features": FEATURES, "unsubscribe": unsubscribe,
               "tagline": settings.APP_TAGLINE, "accent": settings.EMAIL_ACCENT_COLOR, "preheader": copy["intro"]}
    msg = EmailMultiAlternatives(
        subject=copy["subject"], body=render_to_string("billing/email/premium.txt", context).strip(),
        from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email],
        # No List-Unsubscribe headers: Nitrosend reserves them (422) and adds its own. The
        # unsubscribe link in the body is ours.
    )
    msg.attach_alternative(render_to_string("billing/email/premium.html", context), "text/html")
    return msg


def send_due(user, now=None) -> bool:
    """Send this user's next due email, if any. Never raises: a failed send is retried on the next run."""
    if not enabled():
        return False
    if not settings.PUBLIC_BASE_URL:
        logger.error("PREMIUM_CHECKOUT_URL is set but PUBLIC_BASE_URL isn't; premium emails need it for unsubscribe links")
        return False
    now = now or timezone.now()
    with transaction.atomic():
        state, _ = PremiumEmailState.objects.select_for_update().get_or_create(user=user)
        step = _due_step(user, state, now)
        if step is None or not _eligible(user, state):
            return False
        position = len([d for d in settings.PREMIUM_EMAIL_DAYS if d < step])
        try:
            _message(user, position).send()
        except Exception:  # any mail backend; the step stays unsent and is tried again later
            logger.exception("Could not send premium email (day %s) to %s", step, user.email)
            return False
        state.steps_sent = sorted({*state.steps_sent, *(d for d in settings.PREMIUM_EMAIL_DAYS if d <= step)})
        state.last_sent_at = now
        state.save()
    logger.info("Premium email (day %s) sent to %s", step, user.email)
    return True


def send_all_due(now=None) -> int:
    """For the scheduled command: every free, verified, subscribed user with a step due."""
    from apps.accounts.models import User
    if not enabled():
        return 0
    now = now or timezone.now()
    first = min(settings.PREMIUM_EMAIL_DAYS, default=0)
    users = (User.objects.filter(is_active=True, date_joined__lte=now - timedelta(days=first))
             .exclude(premium_emails__unsubscribed_at__isnull=False))
    if settings.REQUIRE_EMAIL_VERIFICATION:
        users = users.filter(is_email_verified=True)
    return sum(send_due(u, now) for u in users.iterator())


def unsubscribe(user) -> None:
    state, _ = PremiumEmailState.objects.get_or_create(user=user)
    if not state.unsubscribed_at:
        state.unsubscribed_at = timezone.now()
        state.save(update_fields=["unsubscribed_at"])
