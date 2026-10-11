"""Daily runner: send any brief that's due and not already sent."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Callable

from . import archive
from .config import LEAD_DAYS
from .events import Event, compute_events
from .render import to_markdown
from .writer import write_brief

log = logging.getLogger(__name__)


def due_events(today: date) -> list[Event]:
    """Events whose send window includes today.

    The window runs from the lead-time day up to the event's own local date, so
    a skipped or failed run catches up the next day instead of losing the brief.
    The archive check in run() keeps it to one send per event.
    """
    horizon = today + timedelta(days=max(LEAD_DAYS.values()))
    return [e for e in compute_events(today, horizon)
            if e.local_date - timedelta(days=LEAD_DAYS[e.tier]) <= today]


def run(today: date, dry_run: bool = False, deliver: Callable[[dict], None] | None = None,
        writer: Callable[[Event, list[str]], dict] = write_brief) -> int:
    """Returns the number of events that failed or went out as facts only."""
    due = [e for e in due_events(today) if not archive.is_sent(e)]
    if not due:
        print(f"{today}: nothing due.")
        return 0
    failures = 0
    for event in due:
        try:
            brief = writer(event, archive.recent_traditions())
            markdown = to_markdown(brief)
            if dry_run:
                print(f"--- {event.id} (dry run: not sent, not archived) ---\n{markdown}")
                continue
            if deliver is None:
                raise RuntimeError("no delivery channel configured")
            deliver(brief)
            path = archive.write(event, markdown, brief)
            print(f"{event.id}: sent, archived to {path}")
            if brief.get("fallback"):
                log.error("%s was sent as facts only: the writer failed", event.id)
                failures += 1
        except Exception:
            log.exception("failed to send %s", event.id)
            failures += 1
    return failures
