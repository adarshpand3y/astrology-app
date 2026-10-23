from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.BillingView.as_view(), name="status"),
    path("trial/", views.StartTrialView.as_view(), name="trial"),
]
