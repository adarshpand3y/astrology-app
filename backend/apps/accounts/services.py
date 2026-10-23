"""Auth domain logic: OTP issue/verify and token helpers."""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions import ServiceUnavailable

from .models import EmailOTP, User

logger = logging.getLogger(__name__)

# Wording of the one-time-code emails; the layout is in templates/accounts/email/otp.{html,txt}.
_EMAILS = {
    EmailOTP.Purpose.VERIFY_EMAIL: {
        "subject": "{code} is your {app_name} verification code",
        "heading": "Welcome to {app_name}",
        "intro": "Enter this code in the app to verify your email and finish creating your account.",
        "ignore": "If you didn't sign up for {app_name}, you can safely ignore this email.",
    },
    EmailOTP.Purpose.PASSWORD_RESET: {
        "subject": "{code} is your {app_name} password reset code",
        "heading": "Reset your password",
        "intro": "Enter this code in the app to choose a new password.",
        "ignore": "If you didn't ask to reset your password, you can ignore this email; your password won't change.",
    },
}


def _otp_email(purpose: str, code: str) -> tuple[str, str, str]:
    """(subject, text, html) for a one-time-code email."""
    names = {"code": code, "app_name": settings.APP_NAME}
    context = {key: text.format(**names) for key, text in _EMAILS[purpose].items()}
    context.update(names, ttl=settings.OTP_TTL_MINUTES, tagline=settings.APP_TAGLINE,
                   accent=settings.EMAIL_ACCENT_COLOR, preheader=context["intro"])
    return (context["subject"], render_to_string("accounts/email/otp.txt", context).strip(),
            render_to_string("accounts/email/otp.html", context))


def issue_otp(user: User, purpose: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    with transaction.atomic():
        EmailOTP.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(used_at=timezone.now())
        EmailOTP.objects.create(
            user=user, purpose=purpose, code_hash=make_password(code),
            expires_at=timezone.now() + timedelta(minutes=settings.OTP_TTL_MINUTES),
        )
    subject, text, html = _otp_email(purpose, code)
    try:
        send_mail(
            subject=subject,
            message=text,
            html_message=html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:  # any mail backend: API, SMTP, ...
        logger.exception("Could not send the %s code to %s", purpose, user.email)
        raise ServiceUnavailable("We couldn't send the email. Please try again in a minute.",
                                 code="email_failed") from exc
    return code


def verify_otp(user: User, purpose: str, code: str) -> bool:
    otp = (EmailOTP.objects.filter(user=user, purpose=purpose, used_at__isnull=True)
           .order_by("-created_at").first())
    if otp is None or not otp.is_usable or otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False
    otp.attempts += 1
    if check_password(code, otp.code_hash):
        otp.used_at = timezone.now()
        otp.save(update_fields=["attempts", "used_at"])
        return True
    otp.save(update_fields=["attempts"])
    return False


def tokens_for(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def revoke_all_tokens(user: User) -> None:
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
