from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class BirthProfile(TimeStampedUUIDModel):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    class Relation(models.TextChoices):
        SELF = "self", "Self"
        FAMILY = "family", "Family"
        FRIEND = "friend", "Friend"
        CLIENT = "client", "Client"
        OTHER = "other", "Other"

    class NodeMode(models.TextChoices):
        MEAN = "mean", "Mean node"
        TRUE = "true", "True node"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="birth_profiles")
    name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    relation = models.CharField(max_length=10, choices=Relation.choices, default=Relation.SELF)

    birth_date = models.DateField()
    birth_time = models.TimeField()
    time_known = models.BooleanField(default=True)

    place = models.ForeignKey("places.Place", null=True, blank=True, on_delete=models.SET_NULL)
    place_label = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    tz_name = models.CharField(max_length=64)

    # Derived on save by the service layer
    utc_offset_minutes = models.IntegerField()
    birth_utc = models.DateTimeField()

    ayanamsa = models.CharField(max_length=20, default="lahiri")
    node_mode = models.CharField(max_length=4, choices=NodeMode.choices, default=NodeMode.MEAN)
    notes = models.TextField(blank=True)

    class Meta(TimeStampedUUIDModel.Meta):
        indexes = [models.Index(fields=["owner", "-created_at"])]

    def __str__(self):
        return f"{self.name} ({self.birth_date})"
