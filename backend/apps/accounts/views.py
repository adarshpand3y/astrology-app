from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.billing import emails as premium_emails
from apps.billing.services import apply_pending_payments
from apps.core.exceptions import ServiceError, ServiceUnavailable
from apps.core.throttles import AuthRateThrottle, OtpRateThrottle

from . import services
from .models import EmailOTP, User
from .serializers import (
    ChangePasswordSerializer, DeleteAccountSerializer, EmailSerializer, LoginSerializer,
    LogoutSerializer, MessageSerializer, OtpSerializer, PasswordResetConfirmSerializer,
    RegisterSerializer, TokenPairResponseSerializer, UserSerializer,
)

_GENERIC_SENT = "If an account exists for this email, a code has been sent."


def _user_or_none(email: str):
    return User.objects.filter(email__iexact=email.strip(), is_active=True).first()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        body = {"user": UserSerializer(user).data}
        if settings.REQUIRE_EMAIL_VERIFICATION:
            try:
                services.issue_otp(user, EmailOTP.Purpose.VERIFY_EMAIL)
            except ServiceUnavailable:
                user.delete()  # no code was delivered, so let them sign up again with the same email
                raise
            body["detail"] = "Verification code sent to email."
        else:
            apply_pending_payments(user)  # bought Pro on the website before signing up
            premium_emails.send_due(user)
            body.update(services.tokens_for(user))
        return Response(body, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    @extend_schema(request=OtpSerializer, responses={200: TokenPairResponseSerializer})
    def post(self, request):
        ser = OtpSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = _user_or_none(ser.validated_data["email"])
        if not user or not services.verify_otp(user, EmailOTP.Purpose.VERIFY_EMAIL,
                                                ser.validated_data["code"]):
            raise ServiceError("Invalid or expired code.", code="invalid_code")
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        apply_pending_payments(user)  # bought Pro on the website before signing up
        premium_emails.send_due(user)  # the first "unlock Pro" email, if enabled
        return Response({**services.tokens_for(user), "user": UserSerializer(user).data})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    @extend_schema(request=EmailSerializer, responses={200: MessageSerializer})
    def post(self, request):
        ser = EmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = _user_or_none(ser.validated_data["email"])
        if user and not user.is_email_verified:
            services.issue_otp(user, EmailOTP.Purpose.VERIFY_EMAIL)
        return Response({"detail": _GENERIC_SENT})


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [AuthRateThrottle]

    @extend_schema(responses={200: TokenPairResponseSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    throttle_classes = [AuthRateThrottle]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        ser = LogoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            RefreshToken(ser.validated_data["refresh"]).blacklist()
        except TokenError as exc:
            raise ServiceError("Invalid refresh token.", code="invalid_token") from exc
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        return self.request.user

    @extend_schema(request=DeleteAccountSerializer, responses={204: None})
    def delete(self, request):
        ser = DeleteAccountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not request.user.check_password(ser.validated_data["password"]):
            raise ServiceError("Incorrect password.", code="invalid_password")
        services.revoke_all_tokens(request.user)
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=ChangePasswordSerializer, responses={200: TokenPairResponseSerializer})
    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = request.user
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        services.revoke_all_tokens(user)
        return Response({**services.tokens_for(user), "user": UserSerializer(user).data})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    @extend_schema(request=EmailSerializer, responses={200: MessageSerializer})
    def post(self, request):
        ser = EmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = _user_or_none(ser.validated_data["email"])
        if user:
            services.issue_otp(user, EmailOTP.Purpose.PASSWORD_RESET)
        return Response({"detail": _GENERIC_SENT})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: MessageSerializer})
    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        user = _user_or_none(data["email"])
        if not user or not services.verify_otp(user, EmailOTP.Purpose.PASSWORD_RESET, data["code"]):
            raise ServiceError("Invalid or expired code.", code="invalid_code")
        user.set_password(data["new_password"])
        user.is_email_verified = True  # proved control of the mailbox
        user.save(update_fields=["password", "is_email_verified"])
        apply_pending_payments(user)
        services.revoke_all_tokens(user)
        return Response({"detail": "Password has been reset."})
