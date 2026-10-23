from rest_framework import exceptions, status

from .models import Subscription


class ProRequired(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "pro_required"
    default_detail = "This feature is part of Pro."


def subscription_for(user) -> Subscription:
    sub, _ = Subscription.objects.get_or_create(user=user)
    return sub


def is_pro(user) -> bool:
    return bool(user and user.is_authenticated and subscription_for(user).is_pro)


def require_pro(user) -> None:
    if not is_pro(user):
        raise ProRequired()
