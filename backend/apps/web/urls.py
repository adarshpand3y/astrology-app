from django.urls import path
from django.views.generic import TemplateView

app_name = "web"


def page(template):
    return TemplateView.as_view(template_name=f"web/{template}.html")


urlpatterns = [
    path("", page("login"), name="login"),
    path("profiles/", page("profiles"), name="profiles"),
    path("profiles/<uuid:pk>/", page("profile_detail"), name="profile-detail"),
    path("panchang/", page("panchang"), name="panchang"),
]
