import re
from unittest import mock

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.services import subscription_for
from apps.places.models import Place
from apps.vedic.models import ComputedResult

pytestmark = pytest.mark.django_db

PASSWORD = "Str0ng-pass-123"


def _code() -> str:
    return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    u = User.objects.create_user("asha@example.com", PASSWORD, is_email_verified=True)
    sub = subscription_for(u)  # these tests exercise calculations; Pro gating is covered in test_companion
    sub.plan = "pro"
    sub.save()
    return u


@pytest.fixture
def authed(client, user):
    r = client.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return client


@pytest.fixture
def delhi():
    return Place.objects.create(geonames_id=1273294, name="Delhi", ascii_name="Delhi", admin1="Delhi",
                                country_code="IN", country="India", latitude=28.65195,
                                longitude=77.23149, timezone="Asia/Kolkata", population=10927986)


@pytest.fixture
def profile(authed, delhi):
    r = authed.post("/api/v1/profiles/", {
        "name": "India", "birth_date": "1947-08-15", "birth_time": "00:00:00", "place_id": delhi.id,
    }, format="json")
    assert r.status_code == 201, r.data
    return r.data


# --- auth -------------------------------------------------------------------------------

def test_register_verify_login_refresh_logout(client):
    r = client.post("/api/v1/auth/register/", {"email": "New@Example.com", "password": PASSWORD,
                                                "full_name": "New"}, format="json")
    assert r.status_code == 201
    assert r.data["user"]["email"] == "new@example.com"

    r = client.post("/api/v1/auth/login/", {"email": "new@example.com", "password": PASSWORD}, format="json")
    assert r.status_code == 400
    assert r.data["error"]["code"] == "email_not_verified"

    r = client.post("/api/v1/auth/verify-email/", {"email": "new@example.com", "code": "000000"}, format="json")
    assert r.status_code == 400 or _code() == "000000"

    r = client.post("/api/v1/auth/verify-email/", {"email": "new@example.com", "code": _code()}, format="json")
    assert r.status_code == 200 and r.data["access"]

    r = client.post("/api/v1/auth/login/", {"email": "new@example.com", "password": PASSWORD}, format="json")
    assert r.status_code == 200
    refresh = r.data["refresh"]

    r = client.post("/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json")
    assert r.status_code == 200
    new_refresh = r.data["refresh"]
    # rotated token is blacklisted
    assert client.post("/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json").status_code == 401

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    assert client.post("/api/v1/auth/logout/", {"refresh": new_refresh}, format="json").status_code == 205
    assert client.post("/api/v1/auth/token/refresh/", {"refresh": new_refresh}, format="json").status_code == 401


def test_register_rejects_weak_and_duplicate(client, user):
    r = client.post("/api/v1/auth/register/", {"email": user.email, "password": PASSWORD}, format="json")
    assert r.status_code == 400 and r.data["error"]["code"] == "validation_error"
    r = client.post("/api/v1/auth/register/", {"email": "x@example.com", "password": "123"}, format="json")
    assert r.status_code == 400
    r = client.post("/api/v1/auth/register/", {"email": "someone2026x@example.com", "password": "someone2026x"},
                    format="json")
    assert r.status_code == 400 and "password" in r.data["error"]["details"]  # shown under the field


def test_register_email_failure_lets_user_retry(client):
    body = {"email": "new@example.com", "password": PASSWORD}
    with mock.patch("apps.accounts.services.send_mail", side_effect=OSError("mail down")):
        r = client.post("/api/v1/auth/register/", body, format="json")
    assert r.status_code == 503 and r.data["error"]["code"] == "email_failed"
    assert not User.objects.filter(email="new@example.com").exists()
    assert client.post("/api/v1/auth/register/", body, format="json").status_code == 201


def test_password_reset(client, user):
    r = client.post("/api/v1/auth/password-reset/request/", {"email": user.email}, format="json")
    assert r.status_code == 200
    r = client.post("/api/v1/auth/password-reset/confirm/", {
        "email": user.email, "code": _code(), "new_password": "An0ther-pass-456"}, format="json")
    assert r.status_code == 200
    r = client.post("/api/v1/auth/login/", {"email": user.email, "password": "An0ther-pass-456"}, format="json")
    assert r.status_code == 200
    # unknown emails get the same response (no enumeration)
    r = client.post("/api/v1/auth/password-reset/request/", {"email": "nobody@example.com"}, format="json")
    assert r.status_code == 200


def test_me_and_change_password(authed):
    r = authed.get("/api/v1/auth/me/")
    assert r.status_code == 200 and r.data["email"] == "asha@example.com"
    r = authed.patch("/api/v1/auth/me/", {"full_name": "Asha"}, format="json")
    assert r.data["full_name"] == "Asha"
    r = authed.post("/api/v1/auth/change-password/", {"old_password": "wrong", "new_password": "Xx-123456789"},
                    format="json")
    assert r.status_code == 400
    r = authed.post("/api/v1/auth/change-password/", {"old_password": PASSWORD, "new_password": "Xx-123456789"},
                    format="json")
    assert r.status_code == 200 and r.data["access"]


def test_requires_auth(client):
    r = client.get("/api/v1/profiles/")
    assert r.status_code == 401
    assert r.data["error"]["code"] == "not_authenticated"


# --- places & profiles --------------------------------------------------------------------

def test_place_search(authed, delhi):
    r = authed.get("/api/v1/places/search/", {"q": "del"})
    assert r.status_code == 200 and r.data["results"][0]["label"] == "Delhi, Delhi, India"
    assert authed.get("/api/v1/places/search/", {"q": "d"}).status_code == 400
    r = authed.get("/api/v1/places/timezone/", {"lat": 40.7, "lon": -74.0})
    assert r.data["timezone"] == "America/New_York"


def test_profile_derived_fields(profile):
    assert profile["tz_name"] == "Asia/Kolkata"
    assert profile["utc_offset_minutes"] == 330
    assert profile["birth_utc"].startswith("1947-08-14T18:30:00")
    assert profile["place_label"] == "Delhi, Delhi, India"


def test_profile_coordinates_only_and_historical_dst(authed):
    r = authed.post("/api/v1/profiles/", {
        "name": "NYC", "birth_date": "1975-07-04", "birth_time": "09:00", "latitude": 40.7128, "longitude": -74.006,
    }, format="json")
    assert r.status_code == 201, r.data
    assert r.data["tz_name"] == "America/New_York" and r.data["utc_offset_minutes"] == -240


def test_profile_unknown_time_and_validation(authed):
    r = authed.post("/api/v1/profiles/", {"name": "U", "birth_date": "1990-01-01", "time_known": False,
                                          "latitude": 10, "longitude": 76}, format="json")
    assert r.status_code == 201 and r.data["birth_time"] == "12:00:00"
    r = authed.post("/api/v1/profiles/", {"name": "U", "birth_date": "1990-01-01", "latitude": 10,
                                          "longitude": 76}, format="json")
    assert r.status_code == 400
    r = authed.post("/api/v1/profiles/", {"name": "U", "birth_date": "1700-01-01", "birth_time": "10:00",
                                          "latitude": 10, "longitude": 76}, format="json")
    assert r.status_code == 400


def test_profile_isolation(profile, client):
    other = User.objects.create_user("other@example.com", PASSWORD, is_email_verified=True)
    r = client.post("/api/v1/auth/login/", {"email": other.email, "password": PASSWORD}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    assert client.get(f"/api/v1/profiles/{profile['id']}/").status_code == 404
    assert client.get(f"/api/v1/profiles/{profile['id']}/chart/").status_code == 404
    assert client.get("/api/v1/profiles/").data["count"] == 0


# --- vedic --------------------------------------------------------------------------------

def test_chart_and_cache_invalidation(authed, profile):
    url = f"/api/v1/profiles/{profile['id']}/chart/"
    r = authed.get(url)
    assert r.status_code == 200
    assert r.data["lagna"]["sign"] == "Taurus"
    assert ComputedResult.objects.filter(profile_id=profile["id"], kind="chart").count() == 1

    r = authed.get(url, {"vargas": "D9,d10"})
    assert set(r.data["vargas"]) == {"D9", "D10"}
    assert authed.get(url, {"vargas": "D99"}).status_code == 400
    assert authed.get(f"/api/v1/profiles/{profile['id']}/vargas/D9/").data["code"] == "D9"

    authed.patch(f"/api/v1/profiles/{profile['id']}/", {"birth_time": "12:00:00"}, format="json")
    r = authed.get(url)
    assert r.data["lagna"]["sign"] != "Taurus"
    assert ComputedResult.objects.filter(profile_id=profile["id"], kind="chart").count() == 1


def test_dashas(authed, profile):
    base = f"/api/v1/profiles/{profile['id']}/dashas/"
    r = authed.get(base, {"depth": 2})
    assert len(r.data["periods"]) == 9
    assert len(r.data["periods"][0]["children"]) == 9
    assert "children" not in r.data["periods"][0]["children"][0]

    r = authed.get(base + "drill/", {"path": "Sa/Sa/Sa/Sa"})
    assert r.status_code == 200 and len(r.data["periods"]) == 9
    assert r.data["periods"][0]["level_name"] == "prana"
    assert authed.get(base + "drill/", {"path": "Sa/Xx"}).status_code == 400

    r = authed.get(base + "current/", {"at": "2000-01-01T00:00:00Z"})
    assert [p["level"] for p in r.data["periods"]] == [1, 2, 3, 4, 5]


def test_strengths(authed, profile):
    r = authed.get(f"/api/v1/profiles/{profile['id']}/shadbala/")
    assert r.status_code == 200 and len(r.data["planets"]) == 7
    r = authed.get(f"/api/v1/profiles/{profile['id']}/bhavabala/")
    assert r.status_code == 200 and len(r.data) == 12


def test_panchang_endpoint(authed, delhi):
    r = authed.post("/api/v1/vedic/panchang/", {"place_id": delhi.id, "date": "2024-01-01", "time": "12:00"},
                    format="json")
    assert r.status_code == 200, r.data
    assert r.data["panchang"]["vara"]["name"] == "Monday"
    assert authed.post("/api/v1/vedic/panchang/", {}, format="json").status_code == 400


def test_health_and_docs(client):
    assert client.get("/healthz").data["checks"] == {"database": "ok", "ephemeris": "ok"}
    assert client.get("/api/schema/").status_code == 200
