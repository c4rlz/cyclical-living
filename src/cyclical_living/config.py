"""Settings that are meant to be tweaked live here."""
from zoneinfo import ZoneInfo, reset_tzpath

# Use the pinned `tzdata` package rather than the OS database, so a runner with
# stale tz data still knows BC stays on UTC-7 year-round from November 2026.
reset_tzpath(to=[])

TZ = ZoneInfo("America/Vancouver")

# How many days before an event its brief goes out, by tier.
LEAD_DAYS = {
    "anchor": 7,
    "full_moon": 2,
    "new_moon": 1,
}
