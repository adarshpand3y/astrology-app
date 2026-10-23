from django.apps import AppConfig


class VedicConfig(AppConfig):
    name = "apps.vedic"
    label = "vedic"

    def ready(self):
        from django.conf import settings

        from .engine import ephemeris

        ephemeris.configure(settings.EPHEMERIS_PATH)
