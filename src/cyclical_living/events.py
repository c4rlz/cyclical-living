"""Event engine: deterministic dates, times and zodiac facts. No interpretation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

import astronomy

from .config import TZ
from .zodiac import lahiri_ayanamsa, nakshatra_of, sign_of

SEASONS = {
    "march_equinox": ("mar_equinox", "March Equinox", "Spring Equinox"),
    "june_solstice": ("jun_solstice", "June Solstice", "Summer Solstice"),
    "september_equinox": ("sep_equinox", "September Equinox", "Autumn Equinox"),
    "december_solstice": ("dec_solstice", "December Solstice", "Winter Solstice"),
}

# type: (sun longitude, name, traditional month, traditional day)
CROSS_QUARTERS = {
    "imbolc": (315, "Imbolc", 2, 1),
    "beltane": (45, "Beltane", 5, 1),
    "lughnasadh": (135, "Lughnasadh", 8, 1),
    "samhain": (225, "Samhain", 10, 31),
}

MOONS = {
    "new_moon": (0, "New Moon", "Amavasya"),
    "full_moon": (180, "Full Moon", "Purnima"),
}


@dataclass
class Event:
    type: str
    tier: str
    name: str
    utc: datetime
    details: dict = field(default_factory=dict)

    @property
    def local(self) -> datetime:
        return self.utc.astimezone(TZ)

    @property
    def local_date(self) -> date:
        # Always derived after tz conversion: an early-UTC event belongs to the
        # previous Pacific evening.
        return self.local.date()

    @property
    def id(self) -> str:
        return f"{self.type}-{self.local_date.isoformat()}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "tier": self.tier,
            "name": self.name,
            "utc": self.utc.isoformat(timespec="seconds"),
            "local": self.local.isoformat(timespec="seconds"),
            "local_date": self.local_date.isoformat(),
            **self.details,
        }


def _to_utc(t: astronomy.Time) -> datetime:
    return t.Utc().replace(tzinfo=timezone.utc, microsecond=0)


def _to_time(dt: datetime) -> astronomy.Time:
    u = dt.astimezone(timezone.utc)
    return astronomy.Time.Make(u.year, u.month, u.day, u.hour, u.minute, u.second)


def moon_details(t: astronomy.Time, vedic_name: str) -> dict:
    utc = _to_utc(t)
    tropical = astronomy.EclipticGeoMoon(t).lon % 360
    ayanamsa = lahiri_ayanamsa(utc)
    sidereal = (tropical - ayanamsa) % 360
    number, nakshatra = nakshatra_of(sidereal)
    return {
        "moon_longitude": round(tropical, 2),
        "tropical_sign": sign_of(tropical),
        "tropical_degree": round(tropical % 30, 1),
        "ayanamsa": round(ayanamsa, 3),
        "sidereal_longitude": round(sidereal, 2),
        "sidereal_sign": sign_of(sidereal),
        "sidereal_degree": round(sidereal % 30, 1),
        "nakshatra": nakshatra,
        "nakshatra_number": number,
        "vedic_name": vedic_name,
    }


def _moon_events(start: datetime, end: datetime) -> list[Event]:
    events = []
    for kind, (phase, name, vedic_name) in MOONS.items():
        t = _to_time(start)
        while True:
            found = astronomy.SearchMoonPhase(phase, t, 40)
            if found is None or _to_utc(found) > end:
                break
            events.append(Event(kind, kind, name, _to_utc(found), moon_details(found, vedic_name)))
            t = found.AddDays(1)
    return events


def _anchor_events(start: datetime, end: datetime) -> list[Event]:
    events = []
    for year in range(start.year - 1, end.year + 2):
        seasons = astronomy.Seasons(year)
        for kind, (attr, name, northern_name) in SEASONS.items():
            events.append(Event(kind, "anchor", name, _to_utc(getattr(seasons, attr)),
                                {"northern_name": northern_name}))
        for kind, (sun_lon, name, month, day) in CROSS_QUARTERS.items():
            found = astronomy.SearchSunLongitude(sun_lon, astronomy.Time.Make(year, 1, 1, 0, 0, 0), 366)
            events.append(Event(kind, "anchor", name, _to_utc(found), {
                "sun_longitude": sun_lon,
                "traditional_date": date(year, month, day).isoformat(),
            }))
    return events


def compute_events(start: date, end: date) -> list[Event]:
    """All events whose *local* date falls in [start, end], sorted by time."""
    # Search a day either side in UTC, then filter on the local date.
    lo = datetime.combine(start, time.min, TZ) - timedelta(days=1)
    hi = datetime.combine(end, time.max, TZ) + timedelta(days=1)
    candidates = _moon_events(lo, hi) + _anchor_events(lo, hi)
    found = [e for e in candidates if start <= e.local_date <= end]
    return sorted(found, key=lambda e: e.utc)
