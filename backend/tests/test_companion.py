"""Daily companion features: signup + onboarding (profile, goals), home, timeline, panchang,
decision assistant, strength report, remedies, journal, alerts and Pro gating."""
import re
from datetime import date, timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.services import subscription_for
from apps.places.models import Place

pytestmark = pytest.mark.django_db
PASSWORD = "Str0ng-pass-123"


@pytest.fixture
def places():
    blr = Place.objects.create(geonames_id=1277333, name="Bengaluru", ascii_name="Bengaluru", admin1="Karnataka",
                               country_code="IN", country="India", latitude=12.97194, longitude=77.59369,
                               timezone="Asia/Kolkata", population=8443675)
    pnq = Place.objects.create(geonames_id=1259229, name="Pune", ascii_name="Pune", admin1="Maharashtra",
                               country_code="IN", country="India", latitude=18.51957, longitude=73.85535,
                               timezone="Asia/Kolkata", population=2935744)
    return blr, pnq


def signup(email):
    """Register with just email + password and verify; returns an authenticated client."""
    c = APIClient()
    r = c.post("/api/v1/auth/register/", {"email": email, "password": PASSWORD}, format="json")
    assert r.status_code == 201, r.data
    code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
    r = c.post("/api/v1/auth/verify-email/", {"email": email, "code": code}, format="json")
    assert r.data["user"]["needs_onboarding"] is True
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return c


@pytest.fixture
def client(places):
    """A verified user who finished onboarding: birth profile, current place, then goals."""
    blr, pnq = places
    c = signup("ananya@example.com")
    r = c.post("/api/v1/profiles/", {"name": "Ananya Rao", "relation": "self", "birth_date": "1994-08-14",
                                     "birth_time": "03:42", "place_id": blr.id}, format="json")
    assert r.status_code == 201, r.data
    r = c.patch("/api/v1/auth/me/", {"full_name": "Ananya Rao", "current_place_id": pnq.id}, format="json")
    assert r.data["needs_onboarding"] is True
    r = c.put("/api/v1/remedies/goals/", {"goals": ["marriage"]}, format="json")
    assert r.status_code == 200, r.data
    return c


def make_pro(c):
    user = User.objects.get(email="ananya@example.com")
    sub = subscription_for(user)
    sub.plan = "pro"
    sub.save()


def test_onboarding_creates_active_profile_and_current_place(client, places):
    me = client.get("/api/v1/auth/me/").data
    assert me["current_place"]["name"] == "Pune"
    assert me["active_profile_id"] and me["goals"] == ["marriage"]
    assert me["needs_onboarding"] is False
    assert me["full_name"] == "Ananya Rao"
    profiles = client.get("/api/v1/profiles/").data["results"]
    assert profiles[0]["relation"] == "self" and profiles[0]["tz_name"] == "Asia/Kolkata"


def test_signup_validates_profile(places):
    r = APIClient().post("/api/v1/auth/register/", {
        "email": "x@example.com", "password": PASSWORD, "profile": {"name": "X", "birth_date": "1994-08-14"},
    }, format="json")
    assert r.status_code == 400 and "profile" in r.data["error"]["details"]
    assert not User.objects.filter(email="x@example.com").exists()


@pytest.mark.parametrize("lang", ["en", "hi"])
def test_home(client, lang):
    r = client.get("/api/v1/daily/home/", HTTP_ACCEPT_LANGUAGE=lang)
    assert r.status_code == 200, r.data
    d = r.data
    assert d["name"] == "Ananya" and d["location"]["city"] == "Pune"
    assert d["insight"]["text"] and d["insight"]["why"] and len(d["insight"]["chips"]) == 2
    assert 0 <= d["period"]["antardasha"]["progress"] <= 1
    assert d["transit"]["title"] and d["transit"]["kind"] in ("good", "bad")
    assert [w["key"] for w in d["windows"]][:2] == ["abhijit", "rahu_kaal"]
    if lang == "hi":
        assert any("ऀ" <= ch <= "ॿ" for ch in d["insight"]["text"])


def test_timeline_and_panchang(client):
    r = client.get("/api/v1/daily/timeline/", {"date": "2026-10-19"})
    assert r.status_code == 200
    keys = [b["key"] for b in r.data["blocks"]]
    assert {"sunrise", "sunset", "rahu_kaal", "yamaganda", "gulika", "abhijit"} <= set(keys)
    assert sum(k.startswith("choghadiya.") for k in keys) == 16
    starts = [b["start"] for b in r.data["blocks"]]
    assert starts == sorted(starts)

    r = client.get("/api/v1/daily/panchang/", {"date": "2026-10-19"})
    assert r.status_code == 200
    assert [row["key"] for row in r.data["rows"]] == ["tithi", "vara", "nakshatra", "yoga", "karana"]
    assert r.data["shaka_year"] == 1948 and r.data["note"]
    assert r.data["rows"][1]["name"] == "Monday"


def test_decision_requires_pro_then_ranks(client):
    r = client.post("/api/v1/daily/decision/", {"activity": "travel", "range": "week"}, format="json")
    assert r.status_code == 403 and r.data["error"]["code"] == "pro_required"
    make_pro(client)
    r = client.post("/api/v1/daily/decision/", {"activity": "travel", "range": "week"}, format="json")
    assert r.status_code == 200, r.data
    scores = [x["score"] for x in r.data["results"]]
    assert scores == sorted(scores, reverse=True) and 0 < len(scores) <= 6
    assert all(x["reason"] for x in r.data["results"])


def test_trial(client):
    assert client.get("/api/v1/billing/").data["trial_available"] is True
    r = client.post("/api/v1/billing/trial/")
    assert r.data["is_pro"] and r.data["on_trial"]
    assert client.post("/api/v1/billing/trial/").status_code == 400


def test_pro_gating_on_chart_and_dasha(client):
    pid = client.get("/api/v1/auth/me/").data["active_profile_id"]
    chart = client.get(f"/api/v1/profiles/{pid}/chart/").data
    assert list(chart["vargas"]) == ["D1"] and chart["vargas_locked"]
    assert client.get(f"/api/v1/profiles/{pid}/vargas/D9/").status_code == 403
    assert client.get(f"/api/v1/profiles/{pid}/dashas/drill/", {"path": "Me"}).status_code == 200
    assert client.get(f"/api/v1/profiles/{pid}/dashas/drill/", {"path": "Me/Ve"}).status_code == 403
    make_pro(client)
    assert len(client.get(f"/api/v1/profiles/{pid}/chart/").data["vargas"]) == 16
    assert client.get(f"/api/v1/profiles/{pid}/dashas/drill/", {"path": "Me/Ve/Su/Mo"}).status_code == 200


def test_strength_report(client):
    pid = client.get("/api/v1/auth/me/").data["active_profile_id"]
    r = client.get(f"/api/v1/profiles/{pid}/strength-report/")
    assert r.status_code == 200
    planets = r.data["planets"]
    assert len(planets) == 7 and [p["ratio"] for p in planets] == sorted([p["ratio"] for p in planets], reverse=True)
    assert len(planets[0]["sources"]) == 6 and planets[0]["advice"]["items"]
    assert len(r.data["houses"]) == 12 and r.data["houses"][0]["advice"]
    assert r.data["summary"]["dasha_note"]


def test_goals_seed_remedies(client):
    r = client.get("/api/v1/remedies/goals/")
    assert r.data["goals"] == ["marriage"] and len(r.data["catalogue"]) == 10
    make_pro(client)
    assert client.get("/api/v1/remedies/goals/").data["max"] == 3
    assert client.put("/api/v1/remedies/goals/", {"goals": ["marriage", "career"]}, format="json").status_code == 200
    r = client.get("/api/v1/remedies/")
    assert [g["key"] for g in r.data["goals"]] == ["marriage", "career"]
    remedies = r.data["remedies"]
    assert {x["goal"] for x in remedies} == {"marriage", "career"}
    assert {x["goal_short"] for x in remedies} == {"Marriage", "Career"}
    assert "gem" not in {x["kind"] for x in remedies}
    keys = [(x["planet"], x["kind"]) for x in remedies]
    assert len(keys) == len(set(keys))
    assert any(x["goal"] == "marriage" and x["kind"] == "fast" for x in remedies)


def test_free_plan_has_one_goal(client):
    r = client.get("/api/v1/remedies/goals/")
    assert r.data["max"] == 1 and r.data["pro_max"] == 3 and r.data["is_pro"] is False
    r = client.put("/api/v1/remedies/goals/", {"goals": ["marriage", "career"]}, format="json")
    assert r.status_code == 403 and r.data["error"]["code"] == "pro_required"
    assert client.get("/api/v1/auth/me/").data["goals"] == ["marriage"]
    assert client.put("/api/v1/remedies/goals/", {"goals": ["career"]}, format="json").status_code == 200


def test_goals_validation(client):
    make_pro(client)
    assert client.put("/api/v1/remedies/goals/", {"goals": []}, format="json").status_code == 400
    assert client.put("/api/v1/remedies/goals/", {"goals": ["marriage", "career", "wealth", "health"]},
                      format="json").status_code == 400
    assert client.put("/api/v1/remedies/goals/", {"goals": ["fame"]}, format="json").status_code == 400


def test_changing_goals_keeps_edited_and_logged(client):
    career = client.put("/api/v1/remedies/goals/", {"goals": ["career"]}, format="json").data["remedies"]
    career = [x for x in career if x["goal"] == "career"]
    assert len(career) >= 3
    edited, logged, *untouched = career
    make_pro(client)  # editing is Pro
    assert client.patch(f"/api/v1/remedies/{edited['id']}/", {"title": "My version"}, format="json").status_code == 200
    client.post(f"/api/v1/remedies/{logged['id']}/progress/", {"completed": True}, format="json")
    r = client.put("/api/v1/remedies/goals/", {"goals": ["foreign"]}, format="json")
    kept = {x["id"]: x for x in r.data["remedies"]}
    assert edited["id"] in kept and logged["id"] in kept
    # Untouched career suggestions are gone, unless the new goal suggests the same remedy.
    assert all(kept[x["id"]]["goal"] == "foreign" for x in untouched if x["id"] in kept)
    assert any(x["id"] not in kept for x in untouched)
    assert client.get("/api/v1/auth/me/").data["goals"] == ["foreign"]


def test_remedies_free_core_and_pro_extras(client):
    r = client.get("/api/v1/remedies/")
    assert r.status_code == 200 and r.data["locked"] is True
    mantra = next(x for x in r.data["remedies"] if x["kind"] == "mantra")
    today = date.today().isoformat()
    # Marking done is free.
    r = client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"count": 72, "today": today}, format="json")
    assert r.status_code == 200 and r.data["remedy"]["today"] == {"count": 72, "completed": False}
    r = client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"completed": True, "today": today}, format="json")
    assert r.data["remedy"]["today"]["completed"] and r.data["streak"]["current"] == 1
    r = client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"completed": False, "count": 0, "today": today},
                    format="json")  # undo
    assert r.data["remedy"]["today"] == {"count": 0, "completed": False} and r.data["streak"]["current"] == 0
    r = client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"completed": True, "today": today}, format="json")
    assert r.data["remedy"]["today"]["completed"]
    # Editing (fields, reminder, reset) and adding remedies are Pro; removing stays free.
    for patch in ({"reminder": False}, {"title": "Mine"}, {"target": 11}, {"reset": True}):
        r = client.patch(f"/api/v1/remedies/{mantra['id']}/", patch, format="json")
        assert r.status_code == 403 and r.data["error"]["code"] == "pro_required"
    assert client.post("/api/v1/remedies/", {"planet": "Sa"}, format="json").status_code == 403
    assert client.post("/api/v1/remedies/", {"title": "Walk"}, format="json").status_code == 403

    make_pro(client)
    r = client.patch(f"/api/v1/remedies/{mantra['id']}/", {"reminder": False}, format="json")
    assert r.data["reminder"] is False
    r = client.post("/api/v1/remedies/", {"planet": "Sa", "kinds": ["gem"]}, format="json")
    assert r.status_code == 201 and len(r.data["remedies"]) == 1
    assert client.post("/api/v1/remedies/", {"text": "no title"}, format="json").status_code == 400
    r = client.post("/api/v1/remedies/", {"title": "Feed birds", "weekdays": [6]}, format="json")
    assert r.status_code == 201
    custom = r.data["remedies"][0]
    assert custom["kind"] == "custom" and custom["weekdays"] == [6] and custom["target"] == 1
    subscription_for(User.objects.get(email="ananya@example.com")).delete()  # back to free
    assert client.delete(f"/api/v1/remedies/{custom['id']}/").status_code == 204


def test_edit_overrides_target_and_days(client):
    make_pro(client)
    remedies = client.get("/api/v1/remedies/").data["remedies"]
    mantra = next(x for x in remedies if x["kind"] == "mantra")
    today = date.today()
    other = (today.weekday() + 2) % 7  # tomorrow, Sunday = 0
    r = client.patch(f"/api/v1/remedies/{mantra['id']}/",
                     {"title": "Short japa", "target": 11, "weekdays": [other]}, format="json")
    assert r.status_code == 200, r.data
    assert r.data["title"] == "Short japa" and r.data["target"] == 11 and r.data["edited"]
    assert r.data["due_today"] is False and r.data["cadence"].startswith("11×")
    r = client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"count": 11, "today": today.isoformat()},
                    format="json")
    assert r.data["remedy"]["today"]["completed"] is True
    r = client.patch(f"/api/v1/remedies/{mantra['id']}/", {"reset": True}, format="json")
    assert r.data["target"] == 108 and r.data["weekdays"] is None and not r.data["edited"]
    assert client.patch(f"/api/v1/remedies/{mantra['id']}/", {"target": 0}, format="json").status_code == 400
    assert client.patch(f"/api/v1/remedies/{mantra['id']}/", {"weekdays": [7]}, format="json").status_code == 400


def test_remove_keeps_history(client):
    today = date.today()
    remedies = client.get("/api/v1/remedies/").data["remedies"]
    mantra = next(x for x in remedies if x["kind"] == "mantra")
    for i in (0, 1, 3):
        d = (today - timedelta(days=i)).isoformat()
        client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"completed": True, "today": d}, format="json")
    assert client.delete(f"/api/v1/remedies/{mantra['id']}/").status_code == 204
    assert client.get(f"/api/v1/remedies/{mantra['id']}/").status_code == 404
    assert mantra["id"] not in {x["id"] for x in client.get("/api/v1/remedies/").data["remedies"]}

    r = client.get("/api/v1/remedies/history/", {"today": today.isoformat()})
    assert r.status_code == 200
    days = r.data["days"]
    assert len(days) == 365 and days[-1]["date"] == today.isoformat()
    by_date = {d["date"]: d for d in days}
    assert by_date[today.isoformat()]["done"] == 1
    assert by_date[(today - timedelta(days=2)).isoformat()]["done"] == 0
    assert all(d["done"] <= d["due"] for d in days)
    assert r.data["totals"] == {"active_days": 3, "completions": 3, "best_streak": 2}


def test_journal_and_trends(client):
    today = date.today()
    for i, rating in enumerate([3, 4, 2, 5, 4, 3]):
        d = (today - timedelta(days=i)).isoformat()
        r = client.put(f"/api/v1/journal/{d}/", {"rating": rating, "tags": ["Work"], "note": "ok"},
                       format="json", QUERY_STRING=f"today={today.isoformat()}")
        assert r.status_code == 200, r.data
    r = client.get(f"/api/v1/journal/{today.isoformat()}/")
    assert r.data["entry"]["rating"] == 3
    r = client.get("/api/v1/journal/trends/", {"today": today.isoformat()})
    assert len(r.data["bars"]) == 14 and r.data["count"] == 6
    assert r.data["insights"]
    future = (today + timedelta(days=2)).isoformat()
    assert client.put(f"/api/v1/journal/{future}/", {"rating": 3}, format="json",
                      QUERY_STRING=f"today={today.isoformat()}").status_code == 400


def test_alerts(client):
    prefs = client.get("/api/v1/alerts/prefs/").data
    assert prefs["rahu"] and prefs["daily"] and not prefs["is_pro"]
    assert client.patch("/api/v1/alerts/prefs/", {"sade_sati": True}, format="json").status_code == 403
    assert client.patch("/api/v1/alerts/prefs/", {"rahu": False}, format="json").data["rahu"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    assert items and all(i["category"] != "rahu" for i in items)
    assert {i["category"] for i in items} <= {"daily", "dasha", "period"}

    periods = [i for i in items if i["category"] == "period"]
    assert periods and periods[0]["title"].startswith("Now: ") and "Choghadiya" in periods[0]["title"]
    assert periods[0]["body"].startswith("Until ")
    assert len({i["at"][:10] for i in periods}) <= 3  # only the next few days, to stay under the phone's cap
    assert all(p["kind"] in ("good", "neutral", "bad") for p in periods)
    assert client.patch("/api/v1/alerts/prefs/", {"periods": False}, format="json").data["periods"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    assert all(i["category"] != "period" for i in items)


def test_place_search_is_public_for_signup(places):
    r = APIClient().get("/api/v1/places/search/", {"q": "pun"})
    assert r.status_code == 200 and r.data["results"][0]["name"] == "Pune"


def test_seed_demo_command(places):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    call_command("seed_demo", "--email", "seed@example.com", "--days", "45")
    with pytest.raises(CommandError):
        call_command("seed_demo", "--email", "seed@example.com")  # exists, no --reset
    with pytest.raises(CommandError):
        call_command("seed_demo", "--email", "x@example.com", "--goals", "marriage,career")  # free: one goal
    call_command("seed_demo", "--email", "seed@example.com", "--reset", "--pro", "--goals", "marriage,career")

    c = APIClient()
    r = c.post("/api/v1/auth/login/", {"email": "seed@example.com", "password": "Demo-pass-123"}, format="json")
    assert r.status_code == 200 and r.data["user"]["needs_onboarding"] is False
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    today = c.get("/api/v1/remedies/history/").data["end"]
    h = c.get("/api/v1/remedies/history/", {"today": today, "days": 45}).data
    assert h["totals"]["active_days"] >= 30 and all(d["due"] > 0 for d in h["days"])
    assert all(d["done"] <= d["due"] for d in h["days"])
    remedies = c.get("/api/v1/remedies/", {"today": today}).data
    assert remedies["locked"] is False and remedies["streak"]["current"] >= 7
    assert any(x["edited"] for x in remedies["remedies"])
    assert c.get("/api/v1/journal/trends/", {"today": today}).data["count"] > 0


def test_seed_demo_clear(places, settings, monkeypatch):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    from apps.profiles.models import BirthProfile
    from apps.remedies.models import RemedyLog

    call_command("seed_demo", "--email", "a@example.com", "--days", "10")
    call_command("seed_demo", "--email", "b@example.com", "--days", "10")
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG=True"):
        call_command("seed_demo", "--clear", "--noinput")
    assert User.objects.count() == 2

    settings.DEBUG = True
    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    with pytest.raises(CommandError, match="Cancelled"):
        call_command("seed_demo", "--clear")
    assert User.objects.count() == 2

    monkeypatch.setattr("builtins.input", lambda prompt: "yes")
    call_command("seed_demo", "--clear")
    assert not User.objects.exists() and not BirthProfile.objects.exists() and not RemedyLog.objects.exists()
    assert Place.objects.count() == 2  # reference data is kept


def test_trends_include_remedies_and_practice_insight(client):
    from apps.remedies.models import UserRemedy

    today = date.today()
    remedies = client.get("/api/v1/remedies/", {"today": today.isoformat()}).data["remedies"]
    mantra = next(x for x in remedies if x["kind"] == "mantra")  # due every day
    UserRemedy.objects.filter(pk=mantra["id"]).update(created_at=timezone.now() - timedelta(days=30))
    q = f"today={today.isoformat()}"
    for i in range(10):
        d = (today - timedelta(days=i)).isoformat()
        practised = i % 2 == 0
        if practised:
            client.post(f"/api/v1/remedies/{mantra['id']}/progress/", {"completed": True, "today": d}, format="json")
        client.put(f"/api/v1/journal/{d}/", {"rating": 5 if practised else 2}, format="json", QUERY_STRING=q)

    r = client.get("/api/v1/journal/trends/", {"today": today.isoformat(), "days": 90})
    assert r.status_code == 200 and len(r.data["bars"]) == 90 and r.data["days"] == 90
    last = r.data["bars"][-1]
    assert last["date"] == today.isoformat() and last["rating"] == 5 and last["remedies"]["done"] >= 1
    assert last["remedies"]["due"] >= last["remedies"]["done"]
    first = r.data["insights"][0]
    assert first["glyph"] == "✦" and "5.0" in first["text"] and "2.0" in first["text"]
    assert client.get("/api/v1/journal/trends/", {"days": "abc"}).data["days"] == 14


def test_practice_insight_needs_brighter_practice_days(client):
    today = date.today()
    q = f"today={today.isoformat()}"
    for i in range(8):  # moods logged, but no remedies ever done
        client.put(f"/api/v1/journal/{(today - timedelta(days=i)).isoformat()}/", {"rating": 3}, format="json", QUERY_STRING=q)
    insights = client.get("/api/v1/journal/trends/", {"today": today.isoformat()}).data["insights"]
    assert all(i["glyph"] != "✦" for i in insights)
