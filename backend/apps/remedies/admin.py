from django.contrib import admin

from .models import RemedyLog, UserRemedy

admin.site.register(UserRemedy, list_display=["user", "planet", "kind", "reminder", "created_at"])
admin.site.register(RemedyLog, list_display=["remedy", "date", "count", "completed"])
