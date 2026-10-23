from rest_framework.throttling import SimpleRateThrottle


class _ScopedThrottle(SimpleRateThrottle):
    """Rate limit per user (or per IP when anonymous) for a fixed scope."""

    def get_cache_key(self, request, view):
        user = request.user
        ident = user.pk if user and user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AuthRateThrottle(_ScopedThrottle):
    scope = "auth"


class OtpRateThrottle(_ScopedThrottle):
    scope = "otp"


class ComputeRateThrottle(_ScopedThrottle):
    scope = "compute"


class PlacesRateThrottle(_ScopedThrottle):
    scope = "places"
