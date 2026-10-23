from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.vedic.engine import ephemeris


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def health(request):
    checks = {}
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:  # pragma: no cover
        checks["database"] = "error"
    checks["ephemeris"] = "ok" if ephemeris.is_available() else "missing"
    healthy = all(v == "ok" for v in checks.values())
    return Response({"status": "ok" if healthy else "degraded", "checks": checks},
                    status=200 if healthy else 503)
