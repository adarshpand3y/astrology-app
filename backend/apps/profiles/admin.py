from django.contrib import admin

from .models import BirthProfile


@admin.register(BirthProfile)
class BirthProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "birth_date", "birth_time", "place_label", "tz_name", "created_at"]
    search_fields = ["name", "owner__email", "place_label"]
    raw_id_fields = ["owner", "place"]
    readonly_fields = ["birth_utc", "utc_offset_minutes"]
