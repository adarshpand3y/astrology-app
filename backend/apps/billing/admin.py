from django.contrib import admin

from .models import PremiumEmailState, RazorpayPayment, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "pro_until", "trial_ends_at", "source", "updated_at"]
    list_filter = ["plan", "source"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]


@admin.register(RazorpayPayment)
class RazorpayPaymentAdmin(admin.ModelAdmin):
    list_display = ["payment_id", "email", "amount", "days", "user", "applied_at", "refunded_at", "created_at"]
    list_filter = ["days"]
    search_fields = ["payment_id", "email"]
    raw_id_fields = ["user"]
    readonly_fields = ["payload"]


@admin.register(PremiumEmailState)
class PremiumEmailStateAdmin(admin.ModelAdmin):
    list_display = ["user", "steps_sent", "last_sent_at", "unsubscribed_at"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]
