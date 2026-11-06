"""Daily companion features: signup + onboarding (profile, goals), home, timeline, panchang,
decision assistant, strength report, remedies, journal, alerts and Pro gating."""
import re
from datetime import date, datetime, timedelta

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
    # The festival glimpse: a month always holds an Ekadashi; nearest first, at most three.
    fest = d["festivals"]
    assert 1 <= len(fest) <= 3 and all(f["name"] and f["how"] and f["glyph"] for f in fest)
    assert [f["days_away"] for f in fest] == sorted(f["days_away"] for f in fest) and 0 <= fest[0]["days_away"] <= 30
    assert any(f["key"].startswith("ekadashi") for f in fest) or fest[-1]["days_away"] <= 16
    sky = d["sky"]
    # The transit chart: each graha's sign, the chart's own lagna and the lagna rising now.
    assert all(1 <= p["sign_index"] <= 12 for p in sky["planets"])
    natal_l, now_l = sky["lagna"]["natal"], sky["lagna"]["now"]
    assert 1 <= natal_l["sign_index"] <= 12 and 0 <= natal_l["degree"] < 30  # birth time known
    assert 1 <= now_l["sign_index"] <= 12 and 0 <= now_l["degree"] < 30
    assert all(p["house"] == (p["sign_index"] - natal_l["sign_index"]) % 12 + 1 for p in sky["planets"])
    assert [p["planet"] for p in sky["planets"]] == ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    assert all(0 <= p["degree"] < 30 for p in sky["planets"])  # degree within the sign
    by = {p["planet"]: p for p in sky["planets"]}
    assert by["Ra"]["retrograde"] and by["Ke"]["retrograde"]  # the nodes always move backwards
    for pl in sky["planets"]:  # one guide per condition the graha is in, each with do and avoid
        active = {c for c in ("retrograde", "combust", "gandmool") if pl[c]} | ({pl["dignity"]} if pl["dignity"] else set())
        assert {g["condition"] for g in pl["guide"]} == active
        assert all(g["note"] and g["do"] and g["avoid"] and g["label"] for g in pl["guide"])
        assert all("{house}" not in g["note"] for g in pl["guide"])
    assert all(1 <= p["house"] <= 12 and 1 <= p["pada"] <= 4 and p["nakshatra"] and p["sign_sanskrit"]
               for p in sky["planets"])
    assert all(p["dignity"] in (None, "exalted", "debilitated") for p in sky["planets"])
    assert sky["reference"] == {"basis": "lagna", "sign": sky["reference"]["sign"], "ayanamsa": "lahiri"}
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
    goal_remedies = [x for x in remedies if x["goal"]]
    assert {x["goal"] for x in goal_remedies} == {"marriage", "career"}
    assert {x["goal_short"] for x in goal_remedies} == {"Marriage", "Career"}
    assert "gem" not in {x["kind"] for x in remedies}
    keys = [(x["planet"], x["kind"]) for x in remedies]
    assert len(keys) == len(set(keys))
    assert any(x["goal"] == "marriage" and x["kind"] == "fast" for x in remedies)


def test_chart_remedies(client):
    """Lagna lord, Chandra, Mahadasha and Antardasha lords get a mantra whatever the goals."""
    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs
    from apps.remedies.models import UserRemedy
    from apps.vedic import services as vedic

    remedies = client.get("/api/v1/remedies/").data["remedies"]
    # This chart has grahas born in Gandmool nakshatras, so gau seva joins the mantras.
    assert rs.gandmool_birth_planets(BirthProfile.objects.get(owner__email="ananya@example.com"))
    seva = [x for x in remedies if x["kind"] == "seva"]
    assert len(seva) == 1 and seva[0]["basis"] == ["gandmool_birth"]
    # Birth time known: the lagna element's practice too.
    assert [x["element"] for x in remedies if x["kind"] == "element"] == [rs.lagna_element(
        BirthProfile.objects.get(owner__email="ananya@example.com")).lower()]
    chart = [x for x in remedies if x["basis"] and x["planet"]]
    assert {b for x in chart for b in x["basis"]} == {"lagna", "moon", "mahadasha", "antardasha"}
    assert all(x["kind"] == "mantra" for x in chart)
    assert len({x["planet"] for x in chart}) == len(chart)  # one mantra per graha, reasons merged
    moon = next(x for x in chart if x["planet"] == "Mo")
    assert "moon" in moon["basis"] and moon["basis_label"]
    pure = [x for x in chart if not x["goal"]]
    assert pure and all(x["goal_short"] in ("Lagna", "Chandra", "Mahadasha", "Antardasha") for x in pure)

    # Removed by the user: not added back for the same reason.
    assert client.delete(f"/api/v1/remedies/{moon['id']}/").status_code == 204
    remedies = client.get("/api/v1/remedies/").data["remedies"]
    assert not any(x["planet"] == "Mo" and x["kind"] == "mantra" for x in remedies)

    # The dasha moves on: the next Antardasha lord's mantra appears; a remedy kept only for the
    # old Antardasha is retired (archived, so its history stays).
    user = User.objects.get(email="ananya@example.com")
    profile = BirthProfile.objects.get(owner=user)
    md, ad = vedic._vimshottari(profile).current(timezone.now(), levels=2)[:2]
    later = ad.end + timedelta(days=1)
    nxt = vedic._vimshottari(profile).current(later, levels=2)[1].lord
    before = {(r.planet, tuple(r.basis)) for r in rs.active(profile) if r.basis}
    rs.sync_chart(profile, at=later)
    after = {r.planet: r.basis for r in rs.active(profile) if r.basis}
    assert "antardasha" in after[nxt]
    old_only = [p for p, b in before if b == ("antardasha",) and p != nxt]
    for p in old_only:
        r = UserRemedy.objects.get(user=user, planet=p, kind="mantra")
        assert r.archived_at is not None and r.basis == []


def test_gandmool_moon_adds_the_nakshatra_lords_mantra(client, monkeypatch):
    """Chandra born in a Gandmool nakshatra: that nakshatra's lord (Budh or Ketu) gets a mantra too."""
    import copy

    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs
    from apps.vedic import services as vedic

    user = User.objects.get(email="ananya@example.com")
    profile = BirthProfile.objects.get(owner=user)
    real = vedic.get_chart

    def chart_with_moon_in(index, lord):
        def fake(p):
            chart = copy.deepcopy(real(p))
            moon = next(x for x in chart["planets"] if x["code"] == "Mo")
            moon["nakshatra"] = {**moon["nakshatra"], "index": index, "lord": lord}
            return chart
        return fake

    monkeypatch.setattr(vedic, "get_chart", chart_with_moon_in(9, "Me"))  # Ashlesha
    assert rs.chart_reasons(profile).get("Me", [])[-1] == "gandmool"
    rs.sync_chart(profile)
    budh = client.get("/api/v1/remedies/").data["remedies"]
    budh = next(x for x in budh if x["planet"] == "Me" and x["kind"] == "mantra")
    assert "gandmool" in budh["basis"] and "Gandmool" in budh["basis_label"]

    monkeypatch.setattr(vedic, "get_chart", chart_with_moon_in(4, "Mo"))  # Rohini: not Gandmool
    assert "gandmool" not in {b for reasons in rs.chart_reasons(profile).values() for b in reasons}


def test_gandmool_birth_adds_gau_seva(client, monkeypatch):
    """Any graha born in a Gandmool nakshatra: one daily gau seva remedy (no graha), naming them."""
    import copy

    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs
    from apps.remedies.models import UserRemedy
    from apps.vedic import services as vedic

    user = User.objects.get(email="ananya@example.com")
    profile = BirthProfile.objects.get(owner=user)
    real = vedic.get_chart

    def chart_with(gandmool: dict[str, int]):
        """Every graha moved out of Gandmool nakshatras, then `gandmool` (code -> 1-based index) moved in."""
        def fake(p):
            chart = copy.deepcopy(real(p))
            for x in chart["planets"]:
                x["nakshatra"] = {**x["nakshatra"], "index": gandmool.get(x["code"], 4)}  # 4 = Rohini
            return chart
        return fake

    def seva():
        return [x for x in client.get("/api/v1/remedies/").data["remedies"] if x["kind"] == "seva"]

    monkeypatch.setattr(vedic, "get_chart", chart_with({"Sa": 19, "Ju": 1}))  # Mula, Ashwini
    rs.sync_chart(profile)
    [r] = seva()
    assert r["planet"] == "" and r["basis"] == ["gandmool_birth"] and r["goal_short"] == "Gandmool"
    assert r["due_today"] and r["weekdays"] is None and r["target"] == 1  # daily
    assert "15 minutes near a cow" in r["how"] and "hara chara" in r["title"]
    assert r["basis_label"] == "For grahas born in Gandmool nakshatras: Guru, Shani"  # chart order
    rs.sync_chart(profile)
    assert len(seva()) == 1  # never doubled

    # Removed by the user: not added back.
    assert client.delete(f"/api/v1/remedies/{r['id']}/").status_code == 204
    rs.sync_chart(profile)
    assert not seva()

    # No graha in a Gandmool nakshatra: no seva (and a kept one is retired).
    UserRemedy.objects.filter(user=user, kind="seva").delete()
    rs.sync_chart(profile)
    assert len(seva()) == 1
    monkeypatch.setattr(vedic, "get_chart", chart_with({}))
    rs.sync_chart(profile)
    assert not seva()
    assert UserRemedy.objects.get(user=user, kind="seva").archived_at is not None


def test_gandmool_moon_adds_a_one_time_shanti_puja(client, monkeypatch):
    """Chandra born in a Gandmool nakshatra: the shanti puja, due until the day it is done, then never again."""
    import copy

    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs
    from apps.vedic import services as vedic

    user = User.objects.get(email="ananya@example.com")
    profile = BirthProfile.objects.get(owner=user)
    real = vedic.get_chart

    def fake(p):
        chart = copy.deepcopy(real(p))
        moon = next(x for x in chart["planets"] if x["code"] == "Mo")
        moon["nakshatra"] = {**moon["nakshatra"], "index": 9, "lord": "Me"}  # Ashlesha
        return chart

    monkeypatch.setattr(vedic, "get_chart", fake)
    rs.sync_chart(profile)
    today = date.today()
    tomorrow = (today + timedelta(days=1)).isoformat()

    def puja(day):
        return [x for x in client.get("/api/v1/remedies/", {"today": day}).data["remedies"] if x["kind"] == "puja"]

    [p] = puja(today.isoformat())
    assert p["planet"] == "" and p["basis"] == ["gandmool"] and p["once"] and p["due_today"]
    assert p["done_on"] is None and "shanti puja" in p["title"].lower()
    assert puja(tomorrow)[0]["due_today"]  # not done yet: still due

    r = client.post(f"/api/v1/remedies/{p['id']}/progress/", {"completed": True, "today": today.isoformat()},
                    format="json")
    assert r.status_code == 200
    [p] = puja(today.isoformat())
    assert p["due_today"] and p["today"]["completed"] and p["done_on"] == today.isoformat()  # shows as done today
    [p] = puja(tomorrow)
    assert not p["due_today"] and p["done_on"] == today.isoformat()  # and is never due again
    rs.sync_chart(profile)
    assert len(puja(tomorrow)) == 1

    # The heatmap counts it on the day it was done only.
    days = {d["date"]: d for d in client.get("/api/v1/remedies/history/", {"today": today.isoformat(),
                                                                           "days": 7}).data["days"]}
    assert days[today.isoformat()]["done"] >= 1


def test_lagna_element_practice_on_the_free_plan(client, monkeypatch):
    """A known birth time: one daily practice for the lagna's tattva, free to follow and mark done."""
    import copy

    from apps.billing.services import is_pro
    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs
    from apps.vedic import services as vedic

    user = User.objects.get(email="ananya@example.com")
    profile = BirthProfile.objects.get(owner=user)
    assert not is_pro(user)

    def element_rows():
        return [x for x in client.get("/api/v1/remedies/").data["remedies"] if x["kind"] == "element"]

    [r] = element_rows()
    assert r["planet"] == "" and r["basis"] == ["lagna_element"] and r["goal_short"] == "Lagna tattva"
    assert r["due_today"] and r["weekdays"] is None and r["target"] == 1 and not r["once"]
    r = client.post(f"/api/v1/remedies/{r['id']}/progress/", {"completed": True}, format="json")
    assert r.status_code == 200 and r.data["remedy"]["today"]["completed"]

    real = vedic.get_chart

    def lagna_in(sign_index):
        def fake(p):
            chart = copy.deepcopy(real(p))
            chart["lagna"] = {**chart["lagna"], "sign_index": sign_index}
            return chart
        return fake

    for sign_index, element, title in ((1, "fire", "Surya arghya"), (2, "earth", "barefoot"),
                                       (3, "air", "anulom-vilom"), (4, "water", "tulsi")):
        monkeypatch.setattr(vedic, "get_chart", lagna_in(sign_index))
        [r] = element_rows()
        assert r["element"] == element and title in r["title"], (sign_index, r["title"])
    assert r["basis_label"] == "For your lagna's element: Jal (water)"
    hi = client.get("/api/v1/remedies/", HTTP_ACCEPT_LANGUAGE="hi").data["remedies"]
    assert next(x for x in hi if x["kind"] == "element")["title"].startswith("जल तत्व")

    # No birth time, no lagna: the practice is retired (its history stays).
    profile.time_known = False
    profile.save()
    rs.sync_chart(profile)
    assert not element_rows()


def test_fallback_seed_has_no_gemstone(places):
    """No goals yet: the Mahadasha lord's mantra, fast and charity, but no gemstone."""
    blr, _ = places
    c = signup("nogoals@example.com")
    assert c.post("/api/v1/profiles/", {"name": "Ravi", "relation": "self", "birth_date": "1990-01-05",
                                        "birth_time": "06:10", "place_id": blr.id}, format="json").status_code == 201
    remedies = c.get("/api/v1/remedies/").data["remedies"]
    seeded = {x["kind"] for x in remedies if x["planet"] and not x["goal"]}
    assert {"mantra", "fast", "charity"} <= seeded and "gem" not in seeded


def test_remedy_list_skips_an_unchanged_chart_sync(client, monkeypatch):
    """The chart sync runs again only when the profile, its birth data, the dasha lords or the list change."""
    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs

    calls = []
    real = rs.sync_chart
    monkeypatch.setattr(rs, "sync_chart", lambda *a, **k: calls.append(1) or real(*a, **k))

    remedies = client.get("/api/v1/remedies/").data["remedies"]  # onboarding's goals call already synced
    client.get("/api/v1/alerts/schedule/", {"days": 1})
    assert calls == []

    assert client.delete(f"/api/v1/remedies/{remedies[0]['id']}/").status_code == 204
    client.get("/api/v1/remedies/")
    client.get("/api/v1/remedies/")
    assert len(calls) == 1

    profile = BirthProfile.objects.get(owner__email="ananya@example.com")
    profile.node_mode = "true" if profile.node_mode == "mean" else "mean"  # new birth data hash
    profile.save()
    client.get("/api/v1/remedies/")
    assert len(calls) == 2


def test_right_now_card(client):
    """The Home "Right now" card: the period in force (a kaal over the choghadiya under it) and the next one."""
    from zoneinfo import ZoneInfo

    from apps.daily import services as ds
    from apps.daily.context import DayContext
    from apps.profiles.models import BirthProfile
    from apps.vedic.engine.muhurta import compute_muhurtas, find

    assert client.get("/api/v1/daily/home/").data["now"]["name"]
    user = User.objects.get(email="ananya@example.com")
    place = user.current_place
    tz = ZoneInfo(place.timezone)
    day = date(2026, 10, 24)

    def ctx_at(now):
        return DayContext(user=user, profile=BirthProfile.objects.get(owner=user), lang="en", tz_name=place.timezone,
                          lat=place.latitude, lon=place.longitude, place_label="Pune", place_city="Pune",
                          place_region="", day=now.astimezone(tz).date(), now=now)

    mu = compute_muhurtas(day, place.latitude, place.longitude, tz)
    rk = find(mu, "rahu_kaal")
    card = ds.right_now(ctx_at(rk.start + timedelta(minutes=5)))
    assert card["key"] == "rahu_kaal" and card["kind"] == "bad" and card["glyph"] == "☊"
    assert 0 < card["progress"] < 0.2 and card["end"] == rk.end and card["next"]["start"] >= rk.end

    night = ds.right_now(ctx_at(datetime(2026, 10, 25, 2, 0, tzinfo=tz)))  # before sunrise: yesterday's night
    assert night["key"].startswith("choghadiya.")

    abhijit = find(mu, "abhijit")
    before = ds.right_now(ctx_at(abhijit.start - timedelta(minutes=10)))
    if before["key"].startswith("choghadiya."):  # a kaal may cover it instead, then Abhijit isn't next
        assert before["next"]["name"].startswith("Abhijit") and before["next"]["start"] == abhijit.start


def test_alert_feed_updates_chart_remedies(client):
    """Opening the app fetches the alert feed; that alone brings chart remedies up to date."""
    from apps.remedies import services as rs
    from apps.remedies.models import UserRemedy

    user = User.objects.get(email="ananya@example.com")
    UserRemedy.objects.filter(user=user).exclude(basis=[]).delete()  # as if never synced
    rs.forget_sync(user.active_profile)
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    reasons = {b for r in UserRemedy.objects.filter(user=user, archived_at__isnull=True) for b in r.basis}
    assert reasons == {"lagna", "moon", "mahadasha", "antardasha", "gandmool_birth", "lagna_element"}
    assert any("Chandra beej mantra" in i["body"] for i in items if i["category"] == "remedy")


def test_free_plan_has_one_goal(client):
    r = client.get("/api/v1/remedies/goals/")
    assert r.data["max"] == 1 and r.data["pro_max"] == 3 and r.data["is_pro"] is False
    r = client.put("/api/v1/remedies/goals/", {"goals": ["marriage", "career"]}, format="json")
    assert r.status_code == 403 and r.data["error"]["code"] == "pro_required"
    assert client.get("/api/v1/auth/me/").data["goals"] == ["marriage"]
    assert client.put("/api/v1/remedies/goals/", {"goals": ["career"]}, format="json").status_code == 200


def test_goals_validation(client):
    make_pro(client)
    assert client.put("/api/v1/remedies/goals/", {"goals": ["marriage", "career", "wealth", "health"]},
                      format="json").status_code == 400
    assert client.put("/api/v1/remedies/goals/", {"goals": ["fame"]}, format="json").status_code == 400


def test_goals_and_remedies_are_per_chart(client, places):
    """Each chart has its own goals and remedy list. On the free plan only your own chart takes a goal;
    skipping goals gives a chart its Mahadasha and Antardasha lords' mantra, fast and charity."""
    from apps.profiles.models import BirthProfile
    from apps.remedies import services as rs

    blr, _ = places
    user = User.objects.get(email="ananya@example.com")
    me = BirthProfile.objects.get(owner=user)
    r = client.post("/api/v1/profiles/", {"name": "Ravi Rao", "relation": "family", "birth_date": "1962-03-02",
                                          "birth_time": "18:20", "place_id": blr.id}, format="json")
    assert r.status_code == 201, r.data
    ravi = BirthProfile.objects.get(pk=r.data["id"])
    q = f"?profile={ravi.pk}"

    g = client.get(f"/api/v1/remedies/goals/{q}").data
    assert g["profile"]["name"] == "Ravi Rao" and g["max"] == 0 and g["chosen"] is False and g["goals"] == []
    r = client.put(f"/api/v1/remedies/goals/{q}", {"goals": ["career"]}, format="json")
    assert r.status_code == 403 and r.data["error"]["code"] == "pro_required"  # free: others' charts need Pro

    # Skipped: the dasha lords' remedies, and nothing from (or to) the user's own chart.
    r = client.put(f"/api/v1/remedies/goals/{q}", {"goals": []}, format="json")
    assert r.status_code == 200 and r.data["profile"]["name"] == "Ravi Rao" and r.data["goals"] == []
    md, ad = rs.current_lords(ravi)
    fallback = {(x["planet"], x["kind"]) for x in r.data["remedies"] if not x["goal"] and not x["basis"]}
    assert {(p, k) for p in (md, ad) for k in ("mantra", "fast", "charity")} - {(p, "mantra") for p in (md, ad)} \
        <= fallback
    assert not any(x["goal"] for x in r.data["remedies"])
    ravi.refresh_from_db()
    assert ravi.goals_chosen_at is not None
    mine = client.get("/api/v1/remedies/").data
    assert mine["profile"]["id"] == str(me.pk) and {x["goal"] for x in mine["remedies"] if x["goal"]} == {"marriage"}
    assert not set(x["id"] for x in mine["remedies"]) & set(x["id"] for x in r.data["remedies"])

    # Done on Ravi's chart: his streak, not the user's.
    rid = r.data["remedies"][0]["id"]
    assert client.post(f"/api/v1/remedies/{rid}/progress/", {"completed": True}, format="json").data["streak"]["current"] == 1
    assert client.get("/api/v1/remedies/").data["streak"]["current"] == 0

    # With Pro, Ravi gets goals; untouched fallback remedies make way, the user's own goals stay.
    make_pro(client)
    assert client.get(f"/api/v1/remedies/goals/{q}").data["max"] == 3
    r = client.put(f"/api/v1/remedies/goals/{q}", {"goals": ["career"]}, format="json")
    assert r.status_code == 200 and [x["key"] for x in r.data["goals"]] == ["career"]
    assert {x["goal"] for x in r.data["remedies"] if x["goal"]} == {"career"}
    assert any(x["id"] == rid for x in r.data["remedies"])  # logged, so kept
    assert client.get("/api/v1/auth/me/").data["goals"] == ["marriage"]  # the active chart's
    me.refresh_from_db()
    assert me.goals == ["marriage"]

    # Switching charts switches the Remedies tab; deleting a chart removes its remedies.
    client.patch("/api/v1/auth/me/", {"active_profile_id": str(ravi.pk)}, format="json")
    assert client.get("/api/v1/remedies/").data["profile"]["name"] == "Ravi Rao"
    assert client.get("/api/v1/auth/me/").data["goals"] == ["career"]
    assert client.delete(f"/api/v1/profiles/{ravi.pk}/").status_code == 204
    assert not rs.owned(user).exclude(profile=me).exists()


def test_reminder_names_each_chart(client, places):
    """The daily remedy reminder covers every chart, naming them when more than one has remedies due."""
    blr, _ = places
    r = client.post("/api/v1/profiles/", {"name": "Ravi Rao", "relation": "family", "birth_date": "1962-03-02",
                                          "birth_time": "18:20", "place_id": blr.id}, format="json")
    client.put(f"/api/v1/remedies/goals/?profile={r.data['id']}", {"goals": []}, format="json")
    items = client.get("/api/v1/alerts/schedule/", {"days": 2}).data["items"]
    bodies = [i["body"] for i in items if i["category"] == "remedy"]
    assert bodies and all("Ananya: " in b and "Ravi: " in b for b in bodies)


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


def test_festival_calendar(client):
    """The month's tithi at each sunrise with its Ekadashis and festivals, at the user's place (Pune)."""
    r = client.get("/api/v1/daily/calendar/", {"month": "2026-11"})
    assert r.status_code == 200, r.data
    days = r.data["days"]
    assert r.data["month"] == "2026-11" and len(days) == 30 and days[0]["date"] == "2026-11-01"
    assert all(1 <= d["tithi"] <= 30 and d["paksha"] in ("Shukla", "Krishna") for d in days)
    by_key = {o["key"]: d["date"] for d in days for o in d["observances"]}
    assert by_key["diwali"] == "2026-11-08"
    diwali = next(o for d in days for o in d["observances"] if o["key"] == "diwali")
    assert diwali["name"] == "Diwali" and diwali["how"] and diwali["glyph"] and diwali["fast"] is False
    assert len(diwali["steps"]) >= 3
    ekadashis = [o for d in days for o in d["observances"] if o["key"].startswith("ekadashi")]
    assert [o["name"] for o in ekadashis] == ["Rama Ekadashi", "Devutthana Ekadashi"] and all(o["fast"] for o in ekadashis)
    assert {"govardhan_puja", "bhai_dooj", "kartik_purnima"} <= set(by_key)
    assert not {"purnima", "amavasya", "sankranti"} & set(by_key)  # only Ekadashi among the monthly vrats

    hi = client.get("/api/v1/daily/calendar/", {"month": "2026-11", "lang": "hi"}).data["days"]
    assert any(o["name"] == "दीपावली" for d in hi for o in d["observances"])
    assert client.get("/api/v1/daily/calendar/").data["month"] == date.today().strftime("%Y-%m")

    for bad in ("2026-13", "nov", "2026-11-05"):
        r = client.get("/api/v1/daily/calendar/", {"month": bad})
        assert r.status_code == 400 and r.data["error"]["code"] == "invalid_month", bad
    far = date.today().year + 5
    assert client.get("/api/v1/daily/calendar/", {"month": f"{far}-01"}).data["error"]["code"] == "month_out_of_range"


def test_vrat_alerts(client):
    """The evening before an Ekadashi or festival, one reminder naming that day's observances."""
    items = client.get("/api/v1/alerts/schedule/", {"days": 14}).data["items"]
    vrats = [i for i in items if i["category"] == "vrat"]
    assert vrats  # two weeks always hold an Ekadashi (they come every ~15 days, from tomorrow on)
    assert all(i["title"].startswith("🌕 Tomorrow: ") and i["body"] for i in vrats)
    assert all(i["at"][11:16] == "19:00" for i in vrats)
    assert len({i["at"][:10] for i in vrats}) == len(vrats)  # one per evening

    assert client.patch("/api/v1/alerts/prefs/", {"vrat": False}, format="json").data["vrat"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 14}).data["items"]
    assert not [i for i in items if i["category"] == "vrat"]


def test_pro_alerts_are_off_on_the_free_plan(client):
    """Transit and Sade Sati alerts read as off for a free account (and none are sent); with Pro the
    stored default comes back on, and it reads as off again once Pro ends."""
    prefs = client.get("/api/v1/alerts/prefs/").data
    assert not prefs["is_pro"] and prefs["transit"] is False and prefs["sade_sati"] is False
    assert client.patch("/api/v1/alerts/prefs/", {"rahu": False}, format="json").data["transit"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 14}).data["items"]
    assert not {"transit", "sade_sati"} & {i["category"] for i in items}

    make_pro(client)
    assert client.get("/api/v1/alerts/prefs/").data["transit"] is True  # the Pro default
    sub = subscription_for(User.objects.get(email="ananya@example.com"))
    sub.plan = "free"
    sub.save()
    assert client.get("/api/v1/alerts/prefs/").data["transit"] is False


def test_alerts(client):
    prefs = client.get("/api/v1/alerts/prefs/").data
    assert prefs["rahu"] and prefs["daily"] and not prefs["is_pro"]
    assert client.patch("/api/v1/alerts/prefs/", {"sade_sati": True}, format="json").status_code == 403
    assert client.patch("/api/v1/alerts/prefs/", {"rahu": False}, format="json").data["rahu"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    assert items and all(i["category"] != "rahu" for i in items)
    assert {i["category"] for i in items} <= {"daily", "dasha", "period", "period_night", "remedy", "vrat"}

    reminders = [i for i in items if i["category"] == "remedy"]
    assert reminders and reminders[0]["title"].startswith("🪔 Today's remedies · ")
    assert "mantra" in reminders[0]["body"].lower()
    assert all(i["at"][11:16] == "07:00" for i in reminders)  # default time, no lead
    assert len({i["at"][:10] for i in reminders}) == len(reminders)  # at most one a day

    periods = [i for i in items if i["category"] == "period"]
    first = periods[0]
    marks = {"good": "🟢 ", "neutral": "🟡 ", "bad": "⚠️ "}
    assert all(i["title"].startswith(marks[i["kind"]]) for i in periods)  # good / neutral / bad at a glance
    # The phone fills {start}/{end} in its own timezone and clock format.
    assert first["title"].endswith(" period, {start}–{end}")
    assert first["body"].startswith(("Suitable for", "Avoid"))
    assert set(first["times"]) == {"start", "end"} and first["times"]["start"] == first["event_at"]
    event, shown = datetime.fromisoformat(first["event_at"]), datetime.fromisoformat(first["at"])
    assert event - shown == timedelta(minutes=15)  # shown ahead, so a late delivery still precedes it
    advice = {i["body"].split()[0] for i in periods}
    assert {"good": "Suitable", "bad": "Avoid"}.get(first["kind"], first["body"].split()[0]) == first["body"].split()[0]
    assert advice <= {"Suitable", "Avoid"}
    assert all(datetime.fromisoformat(i["event_at"]) == datetime.fromisoformat(i["at"]) for i in items
               if i["category"] == "daily")  # the chosen delivery time, not an event
    assert len({i["at"][:10] for i in periods}) <= 3  # only the next few days, to stay under the phone's cap
    assert all(p["kind"] in ("good", "neutral", "bad") for p in periods)
    nights = [i for i in items if i["category"] == "period_night"]
    assert nights and nights[0]["title"].endswith("{start}–{end}")
    assert client.patch("/api/v1/alerts/prefs/", {"periods": False}, format="json").data["periods"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    assert all(i["category"] != "period" for i in items) and any(i["category"] == "period_night" for i in items)
    client.patch("/api/v1/alerts/prefs/", {"periods_night": False}, format="json")
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    assert all(i["category"] not in ("period", "period_night") for i in items)
    assert client.patch("/api/v1/alerts/prefs/", {"remedies": False}, format="json").data["remedies"] is False
    items = client.get("/api/v1/alerts/schedule/", {"days": 3}).data["items"]
    assert all(i["category"] != "remedy" for i in items)


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
