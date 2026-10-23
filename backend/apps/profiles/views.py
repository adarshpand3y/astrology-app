from rest_framework import viewsets

from .models import BirthProfile
from .serializers import BirthProfileSerializer


class BirthProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BirthProfileSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    queryset = BirthProfile.objects.none()  # schema generation

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BirthProfile.objects.none()
        qs = BirthProfile.objects.filter(owner=self.request.user)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def perform_create(self, serializer):
        profile = serializer.save(owner=self.request.user)
        user = self.request.user
        if user.active_profile_id is None:
            user.active_profile = profile
            user.save(update_fields=["active_profile"])

    def perform_destroy(self, instance):
        user = self.request.user
        was_active = user.active_profile_id == instance.pk
        instance.delete()
        if was_active:
            user.active_profile = BirthProfile.objects.filter(owner=user).order_by("created_at").first()
            user.save(update_fields=["active_profile"])
