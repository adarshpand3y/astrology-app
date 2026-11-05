"""Engine tests (no database). Reference: India independence chart,
1947-08-15 00:00 IST, New Delhi (28.6139 N, 77.2090 E), Lahiri, mean node.
"""
from datetime import datetime, timedelta, timezone

import pytest

from apps.vedic.engine import BirthInput, ChartContext, compute_chart, compute_strengths
from apps.vedic.engine.ayanamsa import lahiri
from apps.vedic.engine.dasha.vimshottari import Vimshottari
from apps.vedic.engine.houses import bhava_of, sripati_bhavas
from apps.vedic.engine.panchang import karana_name, tithi_name
from apps.vedic.engine.strength.shadbala import drishti
from apps.vedic.engine.vargas import varga_sign

IST = timezone(timedelta(hours=5, minutes=30))
INDIA = BirthInput(dt=datetime(1947, 8, 15, 0, 0, tzinfo=IST), lat=28.6139, lon=77.2090,
                   tz_name="Asia/Kolkata")


def dms_to_deg(sign: int, d: int, m: int) -> float:
    return sign * 30 + d + m / 60


@pytest.fixture(scope="module")
def chart():
    return compute_chart(INDIA)


@pytest.fixture(scope="module")
def strengths():
    return compute_strengths(INDIA)


# --- ayanamsa -------------------------------------------------------------------------

def test_lahiri_reference_values():
    assert lahiri(2451545.0) == pytest.approx(23.857, abs=0.002)        # J2000
    assert lahiri(2433282.5) == pytest.approx(23.15, abs=0.02)          # 1950-01-01


# --- positions --------------------------------------------------------------------------

@pytest.mark.parametrize("code,expected", [
    ("Su", dms_to_deg(3, 27, 59)), ("Mo", dms_to_deg(3, 3, 59)), ("Ma", dms_to_deg(2, 7, 27)),
    ("Me", dms_to_deg(3, 13, 41)), ("Ju", dms_to_deg(6, 25, 52)), ("Ve", dms_to_deg(3, 22, 33)),
    ("Sa", dms_to_deg(3, 20, 27)),
])
def test_planet_longitudes(chart, code, expected):
    planet = next(p for p in chart["planets"] if p["code"] == code)
    assert planet["longitude"] == pytest.approx(expected, abs=3 / 60)


def test_lagna_and_nodes(chart):
    assert chart["lagna"]["sign"] == "Taurus"
    assert 7 < chart["lagna"]["degree"] < 8
    rahu = next(p for p in chart["planets"] if p["code"] == "Ra")
    ketu = next(p for p in chart["planets"] if p["code"] == "Ke")
    assert rahu["sign"] == "Taurus"
    assert (ketu["longitude"] - rahu["longitude"]) % 360 == pytest.approx(180)


def test_planet_attributes(chart):
    by = {p["code"]: p for p in chart["planets"]}
    assert by["Mo"]["dignity"] == "own"           # Moon in Cancer
    assert by["Ra"]["retrograde"] is True
    assert by["Ve"]["combust"] is True            # 5 deg from the Sun
    assert by["Ju"]["combust"] is False


def test_houses_whole_sign(chart):
    assert chart["houses"][0]["sign"] == "Taurus"
    assert set(chart["houses"][2]["occupants"]) == {"Su", "Mo", "Me", "Ve", "Sa"}


# --- panchang & avakhada ----------------------------------------------------------------

def test_panchang(chart):
    p = chart["panchang"]
    assert p["vara"]["name"] == "Thursday"        # before sunrise of the civil Friday
    assert p["is_day_birth"] is False
    assert p["tithi"]["paksha"] == "Krishna"
    assert p["nakshatra"]["name"] == "Pushya"
    assert p["tithi"]["start"] < p["tithi"]["end"]
    assert p["lunar_month"]["amanta"] == "Shravana"


def test_avakhada(chart):
    a = chart["avakhada"]
    assert (a["rashi"], a["nakshatra"], a["gana"], a["nadi"], a["yoni"]) == \
        ("Cancer", "Pushya", "Deva", "Madhya", "Sheep")


def test_names():
    assert tithi_name(14) == "Purnima" and tithi_name(29) == "Amavasya"
    assert karana_name(0) == "Kimstughna" and karana_name(1) == "Bava" and karana_name(59) == "Naga"


# --- vargas -----------------------------------------------------------------------------

@pytest.mark.parametrize("lon,code,sign", [
    (0.5, "D9", 0), (30.5, "D9", 9), (60.5, "D9", 6), (95, "D9", 4),
    (5, "D2", 4), (20, "D2", 3), (35, "D2", 3), (50, "D2", 4),
    (15, "D3", 4), (25, "D3", 8),
    (2, "D30", 0), (7, "D30", 10), (32, "D30", 1),
    (1, "D10", 0), (31, "D10", 9),
    (0.1, "D60", 0), (29.9, "D60", 11),
])
def test_varga_rules(lon, code, sign):
    assert varga_sign(lon, code) == sign


def test_all_sixteen_vargas(chart):
    assert len(chart["vargas"]) == 16
    assert chart["vargas"]["D1"]["ascendant"]["sign"] == "Taurus"


def test_node_marks_in_every_varga(chart):
    """Rahu/Ketu carry the retrograde star in every chart, and arrows when exalted/debilitated."""
    by = {p["code"]: p for p in chart["planets"]}
    assert by["Ra"]["dignity"] == "exalted"       # Rahu in Taurus
    assert by["Ke"]["dignity"] == "exalted"       # Ketu in Scorpio
    exalt = {"Ra": "Taurus", "Ke": "Scorpio"}
    debil = {"Ra": "Scorpio", "Ke": "Taurus"}
    for code, varga in chart["vargas"].items():
        for p in (x for x in varga["planets"] if x["code"] in ("Ra", "Ke")):
            assert p["retrograde"] is True, (code, p)
            expected = "exalted" if p["sign"] == exalt[p["code"]] else "debilitated" if p["sign"] == debil[p["code"]] else None
            assert p["dignity"] == expected, (code, p)


# --- houses -----------------------------------------------------------------------------

def test_sripati_bhavas():
    b = sripati_bhavas(asc=10.0, mc=280.0)
    assert b["madhya"][0] == pytest.approx(10.0)
    assert b["madhya"][9] == pytest.approx(280.0)
    assert b["madhya"][3] == pytest.approx(100.0)
    assert bhava_of(10.0, b["sandhi"]) == 1
    assert bhava_of(100.0, b["sandhi"]) == 4


# --- dasha ------------------------------------------------------------------------------

def test_vimshottari_structure():
    birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
    v = Vimshottari(moon_lon=0.0, birth=birth)          # start of Ashwini: full Ketu
    assert v.first_lord == "Ke"
    mds = v.mahadashas()
    assert [p.lord for p in mds] == ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
    assert mds[0].start == birth
    assert (mds[-1].end - mds[0].start).days == pytest.approx(120 * 365.2425, abs=1)

    ve = mds[1]
    ads = v.children(ve)
    assert ads[0].lord == "Ve" and ads[0].start == ve.start
    assert abs((ads[-1].end - ve.end).total_seconds()) < 1


def test_vimshottari_drill_and_current():
    birth = datetime(1990, 6, 1, tzinfo=timezone.utc)
    v = Vimshottari(moon_lon=123.4, birth=birth)
    chain = v.current(datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert [p.level for p in chain] == [1, 2, 3, 4, 5]
    for parent, child in zip(chain, chain[1:]):
        assert parent.start <= child.start < child.end <= parent.end + timedelta(seconds=1)
    resolved = v.resolve(list(chain[-1].path))
    assert resolved.start == chain[-1].start
    assert v.children(resolved) == []
    with pytest.raises(ValueError):
        v.resolve(["Xx"])


def test_dasha_balance(chart):
    b = chart["dasha_balance"]
    assert b["lord"] == "Sa"                      # Pushya is ruled by Saturn
    assert 0 < b["total_years"] <= 19


# --- strengths --------------------------------------------------------------------------

def test_drishti_values():
    assert drishti("Su", 0, 180) == 60
    assert drishti("Su", 0, 10) == 0
    assert drishti("Su", 0, 90) == 45
    assert drishti("Sa", 0, 75) > drishti("Su", 0, 75)
    assert drishti("Ju", 0, 130) > drishti("Su", 0, 130)


def test_shadbala_consistency(strengths):
    planets = strengths["shadbala"]["planets"]
    assert set(planets) == {"Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"}
    for code, r in planets.items():
        assert 0 <= r["sthana"]["uchcha"] <= 60
        assert 0 <= r["dig"] <= 60
        assert 0 <= r["chesta"] <= 60
        assert sum(r["totals"].values()) == pytest.approx(r["total_virupas"], abs=1e-3)
        assert r["total_rupas"] == pytest.approx(r["total_virupas"] / 60, abs=1e-4)
        assert 3 < r["total_rupas"] < 12, code
    assert sorted(r["rank"] for r in planets.values()) == list(range(1, 8))
    lords = strengths["shadbala"]["kala_lords"]
    assert lords["vara"] == "Ju"


def test_bhavabala(strengths):
    bhavas = strengths["bhavabala"]
    assert [b["bhava"] for b in bhavas] == list(range(1, 13))
    for b in bhavas:
        assert sum(b["components"].values()) == pytest.approx(b["total_virupas"], abs=1e-3)


def test_true_node_option():
    ctx = ChartContext(BirthInput(**{**INDIA.__dict__, "node_mode": "true"}))
    mean = ChartContext(INDIA)
    diff = abs(ctx.snap.bodies["Ra"].lon - mean.snap.bodies["Ra"].lon)
    assert 0 < diff < 2.0


def test_sky_now_retrograde_and_combust():
    from apps.vedic.engine.transits import sky_now

    utc = timezone.utc
    # 1 Mar 2026: Mercury retrograde (25 Feb - 20 Mar) and Jupiter retrograde (until ~11 Mar).
    march = {p["planet"]: p for p in sky_now(datetime(2026, 3, 1, 12, tzinfo=utc))}
    assert march["Me"]["retrograde"] and march["Ju"]["retrograde"]
    assert datetime(2026, 3, 15, tzinfo=utc) < march["Me"]["retrograde_until"] < datetime(2026, 3, 25, tzinfo=utc)
    assert march["Su"]["retrograde"] is False and march["Su"]["combust"] is False
    # 26 Oct 2026: Venus retrograde near its inferior conjunction, so also combust.
    october = {p["planet"]: p for p in sky_now(datetime(2026, 10, 26, 12, tzinfo=utc))}
    assert october["Ve"]["retrograde"] and october["Ve"]["combust"]
    assert october["Ve"]["combust_until"] < october["Ve"]["retrograde_until"]
    # Rahu and Ketu always move backwards: never flagged.
    assert not any(october[k]["retrograde"] or october[k]["combust"] for k in ("Ra", "Ke"))


def test_sky_guides_cover_every_condition():
    """Every graha has do / avoid guidance for each condition it can be in, in both languages."""
    from apps.vedic.content.sky import guide

    can = {"retrograde": "Ma Me Ju Ve Sa Ra Ke", "combust": "Mo Ma Me Ju Ve Sa",
           "exalted": "Su Mo Ma Me Ju Ve Sa Ra Ke", "debilitated": "Su Mo Ma Me Ju Ve Sa Ra Ke"}
    for cond, planets in can.items():
        for planet in planets.split():
            for lang in ("en", "hi"):
                g = guide(planet, cond, 10, lang)
                assert g and g["note"] and len(g["do"]) >= 2 and len(g["avoid"]) >= 2, (planet, cond, lang)
    assert guide("Su", "retrograde", 1, "en") is None  # the Sun never retrogrades
    assert "10th" in guide("Me", "retrograde", 10, "en")["note"]


def test_gandmool_guide_names_the_nakshatra_and_its_lord():
    from apps.vedic.content.sky import guide
    from apps.vedic.engine.constants import GANDMOOL_NAKSHATRAS, NAKSHATRAS

    assert sorted(NAKSHATRAS[i] for i in GANDMOOL_NAKSHATRAS) == [
        "Ashlesha", "Ashwini", "Jyeshtha", "Magha", "Mula", "Revati"]
    for planet in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"):
        for nak in GANDMOOL_NAKSHATRAS:
            for lang in ("en", "hi"):
                g = guide(planet, "gandmool", 4, lang, nakshatra=nak)
                assert g["note"] and len(g["do"]) >= 2 and len(g["avoid"]) >= 2
                assert "{" not in g["note"] + "".join(g["do"] + g["avoid"])
    moon = guide("Mo", "gandmool", 7, "en", nakshatra=8)  # Ashlesha, ruled by Budh
    assert "Ashlesha" in moon["note"] and "7th" in moon["note"]
    assert "Pray to Vishnu" in moon["do"] and "Chant the Budh beej mantra" in moon["do"]
    assert "Pray to Ganesha" in guide("Sa", "gandmool", 1, "en", nakshatra=18)["do"]  # Mula, ruled by Ketu
    assert guide("Mo", "gandmool", 1, "en") is None  # needs the nakshatra


# --- Vrat & festival calendar ----------------------------------------------------------

@pytest.fixture(scope="module")
def varanasi_2026_days():
    from zoneinfo import ZoneInfo

    from apps.vedic.engine.calendar import month_calendar

    return [d for month in range(1, 13)
            for d in month_calendar(2026, month, 25.3176, 82.9739, ZoneInfo("Asia/Kolkata"))]


@pytest.fixture(scope="module")
def varanasi_2026(varanasi_2026_days):
    """Observance key -> dates, for Varanasi through 2026."""
    found: dict[str, list] = {}
    for d in varanasi_2026_days:
        for o in d["observances"]:
            found.setdefault(o["key"], []).append(d["date"].isoformat())
    return found


@pytest.mark.parametrize("key,day", [
    ("makar_sankranti", "2026-01-14"),
    ("holi", "2026-03-04"),               # Pratipada at sunrise, the day after Holika Dahan's Purnima
    ("chaitra_navratri", "2026-03-19"),   # Pratipada is kshaya: the day it begins, in the new month
    ("vat_savitri", "2026-05-16"),
    ("hariyali_teej", "2026-08-15"),
    ("hartalika_teej", "2026-09-14"),
    ("govardhan_puja", "2026-11-10"),
    ("bhai_dooj", "2026-11-11"),
    ("kartik_purnima", "2026-11-24"),
    ("vasant_panchami", "2026-01-23"),
    ("maha_shivaratri", "2026-02-15"),   # Chaturdashi at midnight
    ("ram_navami", "2026-03-26"),        # Navami at midday, not at sunrise (27th)
    ("janmashtami", "2026-09-04"),       # Ashtami at midnight
    ("ganesh_chaturthi", "2026-09-14"),
    ("navratri", "2026-10-11"),
    ("dussehra", "2026-10-20"),          # Dashami in the afternoon
    ("karva_chauth", "2026-10-29"),      # Krishna Chaturthi at moonrise
    ("dhanteras", "2026-11-06"),
    ("diwali", "2026-11-08"),            # Amavasya at sunset
    ("chhath", "2026-11-15"),
])
def test_festival_dates(varanasi_2026, key, day):
    assert day in varanasi_2026.get(key, []), varanasi_2026.get(key)


def test_only_ekadashis_and_festivals(varanasi_2026):
    from apps.vedic.content.vrat import KEYS

    assert set(varanasi_2026) <= set(KEYS)
    assert len(varanasi_2026["ekadashi_shukla"]) + len(varanasi_2026["ekadashi_krishna"]) in (24, 25, 26)
    assert varanasi_2026["makar_sankranti"] == ["2026-01-14"]  # the only Sankranti listed


def test_ekadashi_names(varanasi_2026_days):
    """Named from the amanta month and paksha; in 2026's Adhika Jyeshtha they are Padmini and Parama."""
    from apps.vedic.content.vrat import observance

    names = {d["date"].isoformat(): observance(o["key"], "en", o["month"], o["is_adhika"])["name"]
             for d in varanasi_2026_days for o in d["observances"] if o["key"].startswith("ekadashi")}
    assert names["2026-11-05"] == "Rama Ekadashi"
    assert names["2026-11-21"] == "Devutthana Ekadashi"
    assert names["2026-06-25"] == "Nirjala Ekadashi"
    assert {names["2026-05-27"], names["2026-06-11"]} == {"Padmini Ekadashi", "Parama Ekadashi"}
    assert all(n != "Ekadashi" for n in names.values())  # every one has its name
    nirjala = observance("ekadashi_shukla", "hi", "Jyeshtha", False)
    assert nirjala["name"] == "निर्जला एकादशी" and len(nirjala["steps"]) == 5  # its own note added


def test_every_observance_says_what_to_do():
    from apps.vedic.content.vrat import KEYS, observance

    for key in KEYS:
        for lang in ("en", "hi"):
            o = observance(key, lang, "Kartika", False)
            assert o["name"] and o["how"] and len(o["steps"]) >= 3 and all(o["steps"]), (key, lang)


def test_tithi_day_rules():
    """Vriddhi (the tithi at two moments) counts on the first day; kshaya (at none) on the day it begins."""
    from apps.vedic.engine.calendar import _days_of

    assert _days_of([9, 10, 11], 10) == [1]
    assert _days_of([9, 10, 10, 11], 10) == [1]      # vriddhi
    assert _days_of([8, 9, 11, 12], 10) == [1]       # kshaya: Ekadashi began after day 1's sunrise
    assert _days_of([28, 0, 1], 29) == []            # skipped on the lookbehind day: not this window's
    assert _days_of([27, 28, 0, 1], 29) == [1]       # Amavasya skipped between days 1 and 2
    assert _days_of([10, 11, 12], 10) == []          # already in force on the lookbehind day
