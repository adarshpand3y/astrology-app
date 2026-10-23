"""Download and import GeoNames cities (idempotent: upserts by geonames_id)."""
import csv
import io
import urllib.request
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.places.models import Place

BASE_URL = "https://download.geonames.org/export/dump/"
BATCH = 5000


def _fetch(name: str, dest: Path, stdout) -> Path:
    path = dest / name
    if not path.exists():
        stdout.write(f"Downloading {name} ...")
        urllib.request.urlretrieve(BASE_URL + name, path)
    return path


class Command(BaseCommand):
    help = "Import GeoNames populated places (cities500/1000/5000/15000)."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="cities5000",
                            choices=["cities500", "cities1000", "cities5000", "cities15000"])

    def handle(self, *args, dataset, **opts):
        dest = Path(settings.DATA_DIR) / "geonames"
        dest.mkdir(parents=True, exist_ok=True)
        zip_path = _fetch(f"{dataset}.zip", dest, self.stdout)
        admin1_path = _fetch("admin1CodesASCII.txt", dest, self.stdout)
        country_path = _fetch("countryInfo.txt", dest, self.stdout)

        admin1 = {}
        with open(admin1_path, encoding="utf-8") as fh:
            for row in csv.reader(fh, delimiter="\t"):
                if len(row) >= 2:
                    admin1[row[0]] = row[1]
        countries = {}
        with open(country_path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                cols = line.rstrip("\n").split("\t")
                if len(cols) > 4:
                    countries[cols[0]] = cols[4]

        existing = set(Place.objects.values_list("geonames_id", flat=True))
        new, updates, total = [], [], 0
        with zipfile.ZipFile(zip_path) as zf, zf.open(f"{dataset}.txt") as raw:
            for line in io.TextIOWrapper(raw, encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                if len(c) < 18:
                    continue
                place = Place(
                    geonames_id=int(c[0]), name=c[1][:200], ascii_name=(c[2] or c[1])[:200],
                    admin1=admin1.get(f"{c[8]}.{c[10]}", "")[:200], country_code=c[8],
                    country=countries.get(c[8], "")[:100], latitude=float(c[4]),
                    longitude=float(c[5]), timezone=c[17], population=int(c[14] or 0),
                )
                (updates if place.geonames_id in existing else new).append(place)
                total += 1
                if len(new) >= BATCH or len(updates) >= BATCH:
                    self._flush(new, updates)
        self._flush(new, updates)
        self.stdout.write(self.style.SUCCESS(f"Imported {total} places from {dataset}."))

    @staticmethod
    @transaction.atomic
    def _flush(new, updates):
        if new:
            Place.objects.bulk_create(new, batch_size=BATCH)
            new.clear()
        for p in updates:
            Place.objects.filter(geonames_id=p.geonames_id).update(
                name=p.name, ascii_name=p.ascii_name, admin1=p.admin1, country_code=p.country_code,
                country=p.country, latitude=p.latitude, longitude=p.longitude,
                timezone=p.timezone, population=p.population)
        updates.clear()
