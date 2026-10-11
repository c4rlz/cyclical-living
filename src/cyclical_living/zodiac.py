"""Signs, ayanamsa and nakshatras. Pure functions of an ecliptic longitude."""
from datetime import datetime

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_SPAN = 360 / 27


def lahiri_ayanamsa(when: datetime) -> float:
    """Lahiri ayanamsa in degrees.

    Linear approximation, good to about an arcminute this century. Swap this
    one function for pyswisseph's swe.get_ayanamsa_ut() if exactness matters.
    """
    year_start = when.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    year_len = year_start.replace(year=when.year + 1) - year_start
    decimal_year = when.year + (when - year_start) / year_len
    return 23.853 + (decimal_year - 2000) * 0.013969


def sign_of(longitude: float) -> str:
    return SIGNS[int(longitude % 360 // 30)]


def nakshatra_of(sidereal_longitude: float) -> tuple[int, str]:
    """1-based nakshatra number and name."""
    index = int(sidereal_longitude % 360 // NAKSHATRA_SPAN)
    return index + 1, NAKSHATRAS[index]
