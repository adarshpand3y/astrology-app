from django.contrib import admin

from .models import JournalEntry

admin.site.register(JournalEntry, list_display=["user", "date", "rating", "updated_at"])
