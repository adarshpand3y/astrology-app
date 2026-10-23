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
