from django.urls import path

from . import views

app_name = "places"

urlpatterns = [
    path("search/", views.PlaceSearchView.as_view(), name="search"),
    path("timezone/", views.TimezoneLookupView.as_view(), name="timezone"),
]
