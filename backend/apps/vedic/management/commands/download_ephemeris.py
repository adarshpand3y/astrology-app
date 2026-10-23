import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.vedic.engine.ephemeris import EPHEMERIS_FILE

URL = f"https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/{EPHEMERIS_FILE}"


class Command(BaseCommand):
    help = "Download the JPL DE440s ephemeris (1849-2150) used by the Vedic engine."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-download even if present.")

    def handle(self, *args, force=False, **opts):
        path = Path(settings.EPHEMERIS_PATH)
        target = path if path.suffix == ".bsp" else path / EPHEMERIS_FILE
        if target.exists() and not force:
            self.stdout.write(self.style.SUCCESS(f"Ephemeris already present at {target}"))
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".part")
        self.stdout.write(f"Downloading {URL} ...")
        urllib.request.urlretrieve(URL, tmp)
        tmp.replace(target)
        self.stdout.write(self.style.SUCCESS(f"Saved {target} ({target.stat().st_size // 1_000_000} MB)"))
