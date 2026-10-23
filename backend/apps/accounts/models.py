import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, is_email_verified=True)
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    # "Where you live now" — drives daily timings.
    current_place = models.ForeignKey("places.Place", null=True, blank=True, on_delete=models.SET_NULL,
                                      related_name="+")
    # Whose chart the app reads (one of the user's birth profiles).
    active_profile = models.ForeignKey("profiles.BirthProfile", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="+")
    # Life goals picked at onboarding (keys of apps.vedic.content.goals) — drive remedy suggestions.
    goals = models.JSONField(default=list, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def needs_onboarding(self) -> bool:
        return self.active_profile_id is None or not self.goals


class EmailOTP(models.Model):
    class Purpose(models.TextChoices):
        VERIFY_EMAIL = "verify_email", "Verify email"
        PASSWORD_RESET = "password_reset", "Password reset"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    code_hash = models.CharField(max_length=256)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "purpose", "-created_at"])]

    @property
    def is_usable(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()
