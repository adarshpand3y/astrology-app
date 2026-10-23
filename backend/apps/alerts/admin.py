from django.contrib import admin

from .models import AlertPreference

admin.site.register(AlertPreference, list_display=["user", "dasha", "transit", "rahu", "sade_sati", "daily"])
