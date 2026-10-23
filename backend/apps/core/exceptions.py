"""Uniform error envelope: {"error": {"code", "message", "details"}}."""
import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ServiceError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "service_error"
    default_detail = "The request could not be processed."


class ServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "service_unavailable"
    default_detail = "Service temporarily unavailable."


def _first_message(detail):
    if isinstance(detail, list) and detail:
        return _first_message(detail[0])
    if isinstance(detail, dict) and detail:
        key, value = next(iter(detail.items()))
        msg = _first_message(value)
        return msg if key in ("detail", "non_field_errors") else f"{key}: {msg}"
    return str(detail)


def _first_code(codes):
    """Specific code for errors raised as {"detail": ...} / non-field errors."""
    if isinstance(codes, str):
        return codes
    if isinstance(codes, list) and len(codes) == 1:
        return _first_code(codes[0])
    if isinstance(codes, dict) and len(codes) == 1:
        key, value = next(iter(codes.items()))
        if key in ("detail", "non_field_errors"):
            return _first_code(value)
    return None


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
    elif isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        return Response(
            {"error": {"code": "server_error", "message": "Internal server error.", "details": None}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data
    if isinstance(exc, exceptions.APIException):
        code = _first_code(exc.get_codes())
        if code in (None, "invalid") and isinstance(exc, exceptions.ValidationError):
            code = "validation_error"
        code = code or exc.default_code
    else:
        code = "error"
    details = detail if isinstance(exc, exceptions.ValidationError) else None
    response.data = {"error": {"code": code, "message": _first_message(detail), "details": details}}
    return response
