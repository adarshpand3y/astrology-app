"""Reject API calls from app builds older than the configured minimum version."""
import re

from django.conf import settings
from django.http import JsonResponse

VERSION_HEADER = "HTTP_X_APP_VERSION"
PLATFORM_HEADER = "HTTP_X_APP_PLATFORM"
EXEMPT_PLATFORMS = {"web"}  # the browser test UI and Expo web always run the latest code
EXEMPT_PREFIXES = ("/api/v1/billing/webhooks/",)  # called by payment providers, not the app


def parse_version(value: str) -> tuple[int, ...] | None:
    """'1.4.2' -> (1, 4, 2); anything that isn't dot-separated numbers -> None."""
    if not value or not re.fullmatch(r"\d+(\.\d+)*", value.strip()):
        return None
    parts = [int(p) for p in value.strip().split(".")]
    while len(parts) > 1 and parts[-1] == 0:  # 1.4 == 1.4.0
        parts.pop()
    return tuple(parts)


def min_version_for(platform: str) -> str:
    return settings.MIN_APP_VERSIONS.get(platform) or settings.MIN_APP_VERSION


class MinAppVersionMiddleware:
    """Answers 426 with an `update_required` error when X-App-Version is missing or too old.

    Off when no minimum is configured. Only /api/v1/ is gated, so admin, docs and /healthz still work.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.path.startswith("/api/v1/") and request.method != "OPTIONS"
                and not request.path.startswith(EXEMPT_PREFIXES)):
            platform = request.META.get(PLATFORM_HEADER, "").strip().lower()
            minimum = parse_version(min_version_for(platform))
            if minimum and platform not in EXEMPT_PLATFORMS:
                version = parse_version(request.META.get(VERSION_HEADER, ""))
                if version is None or version < minimum:
                    return self._reject(min_version_for(platform))
        return self.get_response(request)

    @staticmethod
    def _reject(minimum: str):
        return JsonResponse({"error": {
            "code": "update_required",
            "message": f"This version of {settings.APP_NAME} is no longer supported. Please update the app.",
            "details": {"min_version": minimum},
        }}, status=426)
