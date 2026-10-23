from django.conf import settings
from django.db import transaction
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.places.models import Place
from apps.places.serializers import PlaceSerializer
from apps.profiles.models import BirthProfile
from apps.profiles.serializers import BirthProfileSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    current_place = PlaceSerializer(read_only=True)
    current_place_id = serializers.PrimaryKeyRelatedField(
        source="current_place", queryset=Place.objects.all(), write_only=True, required=False, allow_null=True)
    active_profile_id = serializers.PrimaryKeyRelatedField(
        source="active_profile", queryset=BirthProfile.objects.all(), required=False, allow_null=True)
    needs_onboarding = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "is_email_verified", "date_joined",
                  "current_place", "current_place_id", "active_profile_id", "goals", "needs_onboarding"]
        read_only_fields = ["id", "email", "is_email_verified", "date_joined", "goals"]

    def validate_active_profile_id(self, value):
        if value is not None and value.owner_id != self.instance.pk:
            raise serializers.ValidationError("Unknown profile.")
        return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    current_place_id = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all(), required=False, allow_null=True)
    profile = serializers.JSONField(required=False, help_text="Optional birth details: same fields as a profile.")

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        try:
            password_validation.validate_password(
                attrs["password"], User(email=attrs["email"], full_name=attrs.get("full_name", "")))
        except DjangoValidationError as exc:  # keep the message on the password field
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        if attrs.get("profile") is not None:
            data = {"relation": "self", **attrs["profile"]}
            ps = BirthProfileSerializer(data=data)
            if not ps.is_valid():
                raise serializers.ValidationError({"profile": ps.errors})
            self._profile_serializer = ps
        return attrs

    @transaction.atomic
    def create(self, validated):
        validated.pop("profile", None)
        place = validated.pop("current_place_id", None)
        user = User.objects.create_user(**validated, current_place=place)
        ps = getattr(self, "_profile_serializer", None)
        if ps is not None:
            profile = ps.save(owner=user)
            user.active_profile = profile
            if not user.full_name:
                user.full_name = profile.name
            user.save(update_fields=["active_profile", "full_name"])
        return user


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OtpSerializer(EmailSerializer):
    code = serializers.RegexField(r"^\d{6}$")


class PasswordResetConfirmSerializer(OtpSerializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Invalid email or password.",
    }

    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].lower().strip()
        data = super().validate(attrs)
        if settings.REQUIRE_EMAIL_VERIFICATION and not self.user.is_email_verified:
            raise serializers.ValidationError(
                {"detail": "Email not verified."}, code="email_not_verified")
        data["user"] = UserSerializer(self.user).data
        return data


class TokenPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()
