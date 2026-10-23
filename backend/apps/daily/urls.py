from django.urls import path

from . import views

app_name = "daily"

urlpatterns = [
    path("home/", views.HomeView.as_view(), name="home"),
    path("timeline/", views.TimelineView.as_view(), name="timeline"),
    path("panchang/", views.PanchangView.as_view(), name="panchang"),
    path("decision/", views.DecisionView.as_view(), name="decision"),
    path("transits/", views.TransitsView.as_view(), name="transits"),
]
