"""Deterministic display strings: everything with a date, time or sign in it."""
from datetime import date

from .events import Event


def title(event: Event) -> str:
    d = event.details
    if event.tier in ("full_moon", "new_moon"):
        return f"{event.name} in {d['tropical_sign']}"
    return d.get("northern_name", event.name)


def when_line(event: Event) -> str:
    local = event.local
    hour = local.strftime("%-I:%M %p").lower()
    return f"{local:%A %b} {local.day} · {hour} PT"


def systems_line(event: Event) -> str:
    d = event.details
    if "nakshatra" in d:
        return (f"Tropical: {d['tropical_sign']} · Sidereal: {d['sidereal_sign']}, "
                f"{d['nakshatra']} · {d['vedic_name']}")
    if "traditional_date" in d:
        trad = date.fromisoformat(d["traditional_date"])
        return f"Astronomical midpoint (Sun at {d['sun_longitude']}°) · Traditionally {trad:%b} {trad.day}"
    return f"{event.name} · Sun enters {_sun_sign(event)}"


def _sun_sign(event: Event) -> str:
    return {"march_equinox": "Aries", "june_solstice": "Cancer",
            "september_equinox": "Libra", "december_solstice": "Capricorn"}[event.type]
