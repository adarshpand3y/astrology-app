from django.urls import path

from . import views

app_name = "remedies"

urlpatterns = [
    path("", views.RemedyListView.as_view(), name="list"),
    path("goals/", views.GoalsView.as_view(), name="goals"),
    path("history/", views.RemedyHistoryView.as_view(), name="history"),
    path("<int:pk>/", views.RemedyDetailView.as_view(), name="detail"),
    path("<int:pk>/progress/", views.RemedyProgressView.as_view(), name="progress"),
]
