from datetime import date, datetime, timedelta, timezone

import astronomy
import pytest

from cyclical_living.events import compute_events
from cyclical_living.zodiac import lahiri_ayanamsa, nakshatra_of, sign_of

TOLERANCE = timedelta(minutes=2)

# Published values (USNO / timeanddate), UTC.
PUBLISHED = [
    ("march_equinox", datetime(2026, 3, 20, 14, 46)),
    ("june_solstice", datetime(2026, 6, 21, 8, 24)),
    ("september_equinox", datetime(2026, 9, 23, 0, 5)),
    ("december_solstice", datetime(2026, 12, 21, 20, 50)),
    ("full_moon", datetime(2026, 1, 3, 10, 3)),
    ("full_moon", datetime(2026, 3, 3, 11, 38)),
    ("full_moon", datetime(2026, 10, 26, 4, 12)),
    ("full_moon", datetime(2026, 11, 24, 14, 53)),
    ("new_moon", datetime(2026, 2, 17, 12, 1)),
    ("new_moon", datetime(2026, 8, 12, 17, 37)),
    ("new_moon", datetime(2026, 11, 9, 7, 2)),
    ("new_moon", datetime(2026, 12, 9, 0, 52)),
]


@pytest.fixture(scope="module")
def events_2026():
    return compute_events(date(2026, 1, 1), date(2026, 12, 31))


@pytest.mark.parametrize("kind,expected", PUBLISHED)
def test_matches_published_times(events_2026, kind, expected):
    expected = expected.replace(tzinfo=timezone.utc)
    nearest = min((e for e in events_2026 if e.type == kind), key=lambda e: abs(e.utc - expected))
    assert abs(nearest.utc - expected) <= TOLERANCE


def test_counts(events_2026):
    kinds = [e.type for e in events_2026]
    assert kinds.count("full_moon") == 13
    assert kinds.count("new_moon") == 12
    assert len([e for e in events_2026 if e.tier == "anchor"]) == 8


def test_ids_unique_and_sorted(events_2026):
    assert len({e.id for e in events_2026}) == len(events_2026)
    assert events_2026 == sorted(events_2026, key=lambda e: e.utc)


# --- timezone edge cases ---

def by_id(events, event_id):
    return next(e for e in events if e.id == event_id)


def test_early_utc_event_belongs_to_previous_pacific_evening(events_2026):
    # 2026-10-26 04:12 UTC is the evening of Oct 25 in Vancouver.
    full = by_id(events_2026, "full_moon-2026-10-25")
    assert full.utc.date() == date(2026, 10, 26)
    assert full.local.strftime("%Y-%m-%d %H:%M") == "2026-10-25 21:12"
    assert not any(e.id == "full_moon-2026-10-26" for e in events_2026)


def test_equinox_just_after_utc_midnight(events_2026):
    eq = by_id(events_2026, "september_equinox-2026-09-22")
    assert eq.local.strftime("%Y-%m-%d %H:%M") == "2026-09-22 17:05"


def test_bc_stays_on_utc_minus_7_after_november_2026(events_2026):
    # BC's permanent daylight time: no fall-back on 2026-11-01.
    nm = by_id(events_2026, "new_moon-2026-12-08")
    assert nm.local.utcoffset() == timedelta(hours=-7)
    assert nm.local.strftime("%H:%M") == "17:52"


def test_range_filters_on_local_date():
    assert [e.id for e in compute_events(date(2026, 10, 25), date(2026, 10, 25))] == ["full_moon-2026-10-25"]
    assert compute_events(date(2026, 10, 26), date(2026, 10, 26)) == []


# --- moon details ---

def test_moon_details(events_2026):
    d = by_id(events_2026, "full_moon-2026-10-25").details
    # Cross-checked against Swiss Ephemeris (Lahiri).
    assert d["tropical_sign"] == "Taurus"
    assert d["sidereal_sign"] == "Aries"
    assert d["nakshatra"] == "Ashwini"
    assert d["nakshatra_number"] == 1
    assert d["vedic_name"] == "Purnima"
    assert by_id(events_2026, "new_moon-2026-11-09").details["vedic_name"] == "Amavasya"


def test_cross_quarters(events_2026):
    samhain = next(e for e in events_2026 if e.type == "samhain")
    assert samhain.details["traditional_date"] == "2026-10-31"
    assert samhain.local_date == date(2026, 11, 7)
    sun = astronomy.SunPosition(astronomy.Time.Make(*samhain.utc.timetuple()[:6]))
    assert sun.elon == pytest.approx(225, abs=0.01)
    traditional = {e.type: e.details["traditional_date"] for e in events_2026 if "traditional_date" in e.details}
    assert traditional == {"imbolc": "2026-02-01", "beltane": "2026-05-01",
                           "lughnasadh": "2026-08-01", "samhain": "2026-10-31"}


# --- zodiac primitives ---

def test_sign_boundaries():
    assert sign_of(0) == "Aries"
    assert sign_of(29.999) == "Aries"
    assert sign_of(30) == "Taurus"
    assert sign_of(359.9) == "Pisces"
    assert sign_of(360) == "Aries"


def test_nakshatra_boundaries():
    assert nakshatra_of(0) == (1, "Ashwini")
    assert nakshatra_of(13.34) == (2, "Bharani")
    assert nakshatra_of(359.9) == (27, "Revati")


def test_ayanamsa():
    assert lahiri_ayanamsa(datetime(2000, 1, 1)) == pytest.approx(23.853)
    # Swiss Ephemeris Lahiri for mid-2026 is ~24.22.
    assert lahiri_ayanamsa(datetime(2026, 7, 1)) == pytest.approx(24.22, abs=0.02)
