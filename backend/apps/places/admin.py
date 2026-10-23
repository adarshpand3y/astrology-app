from django.contrib import admin

from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ["name", "admin1", "country_code", "latitude", "longitude", "timezone", "population"]
    search_fields = ["name", "ascii_name"]
    list_filter = ["country_code"]
