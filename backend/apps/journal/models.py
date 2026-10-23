from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class JournalEntry(models.Model):
    """One mood check-in per user per local date."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journal")
    date = models.DateField()
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    tags = models.JSONField(default=list, blank=True)
    note = models.TextField(blank=True, max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["user", "date"], name="uniq_journal_day")]
