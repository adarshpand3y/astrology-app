from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "pro_until", "trial_ends_at", "source", "updated_at"]
    list_filter = ["plan", "source"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]
