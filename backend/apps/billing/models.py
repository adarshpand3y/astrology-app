from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    """A user's plan. Store billing (RevenueCat / Play / App Store) can update this later."""

    class Plan(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.FREE)
    pro_until = models.DateTimeField(null=True, blank=True, help_text="Paid Pro access end (null = no end).")
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=30, blank=True, help_text="e.g. admin, trial, play_store")
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def on_trial(self) -> bool:
        return bool(self.trial_ends_at and self.trial_ends_at > timezone.now())

    @property
    def is_pro(self) -> bool:
        if self.on_trial:
            return True
        if self.plan != self.Plan.PRO:
            return False
        return self.pro_until is None or self.pro_until > timezone.now()

    @property
    def trial_available(self) -> bool:
        return self.trial_started_at is None and self.plan == self.Plan.FREE

    def start_trial(self, days: int) -> None:
        now = timezone.now()
        self.trial_started_at = now
        self.trial_ends_at = now + timedelta(days=days)
        self.source = "trial"
        self.save()

    def __str__(self):
        return f"{self.user} · {self.plan}"


class RazorpayPayment(models.Model):
    """One captured Razorpay payment from the website; grants `days` of Pro to the account with `email`.

    Kept even when no account matches yet (applied once that email is verified) and when the amount
    matches no plan (days = 0, for a manual look in the admin)."""

    payment_id = models.CharField(max_length=40, unique=True)
    email = models.EmailField()
    amount = models.PositiveIntegerField(help_text="In paise.")
    currency = models.CharField(max_length=3)
    days = models.PositiveIntegerField(help_text="Pro days this payment buys (0 = amount matched no plan).")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="razorpay_payments")
    applied_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_id} · {self.email} · {self.days}d"


class PremiumEmailState(models.Model):
    """Where a free user is in the "unlock Pro on the website" email sequence."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="premium_emails")
    steps_sent = models.JSONField(default=list, blank=True, help_text="Day offsets already sent (or skipped).")
    last_sent_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} · sent {self.steps_sent}"
