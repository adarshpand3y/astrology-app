from datetime import time

from django.conf import settings
from django.db import models


class AlertPreference(models.Model):
    """Which reminders the phone should schedule for this user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_prefs")
    dasha = models.BooleanField(default=True)
    transit = models.BooleanField(default=True)       # Pro
    rahu = models.BooleanField(default=True)
    sade_sati = models.BooleanField(default=False)    # Pro
    daily = models.BooleanField(default=True)
    daily_time = models.TimeField(default=time(8, 0))
    rahu_lead_minutes = models.PositiveSmallIntegerField(default=15)
    periods = models.BooleanField(default=True)        # each daytime choghadiya as it begins
    periods_night = models.BooleanField(default=True)  # each night choghadiya (silent on the phone)
    remedies = models.BooleanField(default=True)       # one daily reminder listing the remedies due
    remedy_time = models.TimeField(default=time(7, 0))
    updated_at = models.DateTimeField(auto_now=True)

    PRO_FIELDS = ("transit", "sade_sati")
