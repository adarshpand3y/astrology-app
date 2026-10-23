from django.contrib import admin

from .models import ComputedResult


@admin.register(ComputedResult)
class ComputedResultAdmin(admin.ModelAdmin):
    list_display = ["profile", "kind", "input_hash", "created_at"]
    list_filter = ["kind"]
    raw_id_fields = ["profile"]
