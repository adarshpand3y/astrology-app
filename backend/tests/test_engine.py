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
