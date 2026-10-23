from django.urls import path

from . import views

app_name = "journal"

urlpatterns = [
    path("trends/", views.TrendsView.as_view(), name="trends"),
    path("<str:day>/", views.JournalDayView.as_view(), name="day"),
]
