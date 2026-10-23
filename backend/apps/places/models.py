from django.db import models


class Place(models.Model):
    """A populated place from the GeoNames dataset."""
    geonames_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=200)
    ascii_name = models.CharField(max_length=200, db_index=True)
    admin1 = models.CharField(max_length=200, blank=True)
    country_code = models.CharField(max_length=2, db_index=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone = models.CharField(max_length=64)
    population = models.PositiveBigIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["-population"]
        indexes = [models.Index(fields=["ascii_name", "-population"])]

    def __str__(self):
        return self.label

    @property
    def label(self) -> str:
        return ", ".join(p for p in (self.ascii_name or self.name, self.admin1, self.country or self.country_code) if p)
