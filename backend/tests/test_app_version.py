import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.core.middleware import parse_version

pytestmark = pytest.mark.django_db

URL = "/api/v1/places/search/?q=del"


def _get(**headers):
    meta = {f"HTTP_{k.upper().replace('-', '_')}": v for k, v in headers.items()}
    return APIClient().get(URL, **meta)


def test_parse_version():
    assert parse_version("1.4.2") == (1, 4, 2)
    assert parse_version("1.4") == parse_version("1.4.0")
    assert parse_version("1.10.0") > parse_version("1.9.9")
    assert parse_version("") is None
    assert parse_version("1.0-beta") is None


def test_no_minimum_means_no_check():
    assert _get().status_code != 426


@override_settings(MIN_APP_VERSION="1.2.0", MIN_APP_VERSIONS={"android": "", "ios": "1.3.0"})
def test_old_or_missing_version_is_rejected():
    r = _get(**{"X-App-Version": "1.1.9", "X-App-Platform": "android"})
    assert r.status_code == 426
    assert r.json()["error"]["code"] == "update_required"
    assert r.json()["error"]["details"]["min_version"] == "1.2.0"
    assert _get().status_code == 426
    assert _get(**{"X-App-Version": "junk"}).status_code == 426
    # iOS has its own, higher floor.
    assert _get(**{"X-App-Version": "1.2.5", "X-App-Platform": "ios"}).status_code == 426


@override_settings(MIN_APP_VERSION="1.2.0", MIN_APP_VERSIONS={"android": "", "ios": ""})
def test_current_versions_and_exempt_paths_pass():
    assert _get(**{"X-App-Version": "1.2", "X-App-Platform": "android"}).status_code != 426
    assert _get(**{"X-App-Version": "2.0.0"}).status_code != 426
    assert _get(**{"X-App-Platform": "web"}).status_code != 426
    assert APIClient().get("/healthz").status_code != 426
