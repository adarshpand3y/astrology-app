from django.db import models


class ComputedResult(models.Model):
    """Cached engine output for a profile.

    ``input_hash`` covers the birth data, calculation options and ENGINE_VERSION,
    so editing a profile or upgrading the engine transparently invalidates it.
    """

    class Kind(models.TextChoices):
        CHART = "chart", "Birth chart"
        STRENGTHS = "strengths", "Shadbala & Bhava Bala"
        DASHA_TREE = "dasha_tree", "Vimshottari tree (3 levels)"

    profile = models.ForeignKey("profiles.BirthProfile", on_delete=models.CASCADE, related_name="results")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    input_hash = models.CharField(max_length=64)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "kind", "input_hash"], name="uniq_result_per_input"),
        ]
