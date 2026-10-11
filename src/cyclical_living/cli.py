import argparse
import logging
import sys
from datetime import date, datetime, timedelta

from .config import LEAD_DAYS, TZ
from .events import compute_events
from .runner import run


def print_events(start: date, days: int) -> None:
    for e in compute_events(start, start + timedelta(days=days)):
        d = e.details
        when = e.local.strftime("%a %b %d · %-I:%M %p PT")
        send = e.local_date - timedelta(days=LEAD_DAYS[e.tier])
        line = f"{when:<26} {e.name:<18}"
        if "nakshatra" in d:
            line += f" {d['tropical_sign']} · sidereal {d['sidereal_sign']}, {d['nakshatra']} · {d['vedic_name']}"
        elif "traditional_date" in d:
            line += f" (traditional {date.fromisoformat(d['traditional_date']):%b %d})"
        elif "northern_name" in d:
            line += f" ({d['northern_name']})"
        print(f"{line}\n{'':<27}id {e.id} · brief sends {send:%a %b %d}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="cyclical-living")
    sub = parser.add_subparsers(dest="command", required=True)
    ev = sub.add_parser("events", help="list upcoming events")
    ev.add_argument("--from", dest="start", type=date.fromisoformat, default=None)
    ev.add_argument("--days", type=int, default=92)
    rn = sub.add_parser("run", help="send any brief that's due today")
    rn.add_argument("--date", type=date.fromisoformat, help="simulate this day (YYYY-MM-DD)")
    rn.add_argument("--dry-run", action="store_true", help="print the brief instead of sending")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "events":
        print_events(args.start or datetime.now(TZ).date(), args.days)
    elif args.command == "run":
        today = args.date or datetime.now(TZ).date()
        sys.exit(1 if run(today, dry_run=args.dry_run) else 0)
