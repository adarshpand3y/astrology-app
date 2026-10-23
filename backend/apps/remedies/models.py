from django.conf import settings
from django.db import models


class UserRemedy(models.Model):
    """A remedy the user follows: a catalogue remedy for a graha (mantra / fast / charity / gemstone),
    optionally edited by the user, or a custom remedy the user wrote."""

    class Kind(models.TextChoices):
        MANTRA = "mantra", "Mantra"
        FAST = "fast", "Fasting"
        CHARITY = "charity", "Charity"
        GEM = "gem", "Gemstone"
        CUSTOM = "custom", "Custom"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="remedies")
    planet = models.CharField(max_length=2, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    reminder = models.BooleanField(default=True)
    # The goal that suggested this remedy ("" = dasha fallback or added by the user).
    goal = models.CharField(max_length=20, blank=True)
    # User edits; blank / null means "use the catalogue text".
    title = models.CharField(max_length=120, blank=True)
    text = models.CharField(max_length=300, blank=True)
    how = models.TextField(blank=True)
    cadence = models.CharField(max_length=80, blank=True)
    target = models.PositiveIntegerField(null=True, blank=True)
    weekdays = models.JSONField(null=True, blank=True, help_text="Due weekdays, Sunday = 0. Null = catalogue default.")
    # Removed remedies are archived so their history still shows on the heatmap.
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    OVERRIDES = ("title", "text", "how", "cadence", "target", "weekdays")

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [models.UniqueConstraint(
            fields=["user", "planet", "kind"], name="uniq_user_remedy",
            condition=models.Q(archived_at__isnull=True) & ~models.Q(kind="custom"))]

    def __str__(self):
        return f"{self.user} · {self.planet or '-'} {self.kind}"

    @property
    def edited(self) -> bool:
        return any(getattr(self, f) not in ("", None) for f in self.OVERRIDES)


class RemedyLog(models.Model):
    """Progress for one remedy on one local date."""
    remedy = models.ForeignKey(UserRemedy, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["remedy", "date"], name="uniq_remedy_log")]
        indexes = [models.Index(fields=["date"])]
