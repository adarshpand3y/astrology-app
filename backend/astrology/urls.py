from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.billing.views import premium_unsubscribe
from apps.core.views import health
from apps.profiles.views import BirthProfileViewSet

router = DefaultRouter(trailing_slash=True)
router.register("profiles", BirthProfileViewSet, basename="profile")

api_v1 = [
    path("auth/", include("apps.accounts.urls")),
    path("places/", include("apps.places.urls")),
    path("daily/", include("apps.daily.urls")),
    path("remedies/", include("apps.remedies.urls")),
    path("journal/", include("apps.journal.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("billing/", include("apps.billing.urls")),
    path("", include("apps.vedic.urls")),
    path("", include(router.urls)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", health, name="health"),
    path("email/unsubscribe/<str:token>/", premium_unsubscribe, name="premium-unsubscribe"),
    path("api/v1/", include((api_v1, "v1"))),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.ENABLE_TEST_UI:
    urlpatterns.append(path("ui/", include("apps.web.urls")))
