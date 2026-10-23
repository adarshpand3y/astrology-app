from django.urls import path

from . import views

app_name = "alerts"

urlpatterns = [
    path("prefs/", views.PrefsView.as_view(), name="prefs"),
    path("schedule/", views.ScheduleView.as_view(), name="schedule"),
]
