"""Writer: Claude turns computed facts into a short brief. It never decides facts.

Title, when-line and systems-line are built in code (facts.py); the model only
writes the prose fields.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

import anthropic
from pydantic import BaseModel, ValidationError

from . import facts
from .events import Event
from .place import SEASONAL_NOTES

log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5-5"


class Prose(BaseModel):
    lore: str
    why_it_matters: str
    reflection_prompt: str
    ritual: str
    outside: Optional[str] = None
    go_deeper: Optional[str] = None
    tradition_used: str


PROSE_SCHEMA = {
    "type": "object",
    "properties": {
        "lore": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "reflection_prompt": {"type": "string"},
        "ritual": {"type": "string"},
        "outside": {"type": ["string", "null"]},
        "go_deeper": {"type": ["string", "null"]},
        "tradition_used": {"type": "string"},
    },
    "required": ["lore", "why_it_matters", "reflection_prompt", "ritual",
                 "outside", "go_deeper", "tradition_used"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """\
You write short briefs for one person's seasonal and lunar practice. Each brief \
arrives a few days before a new moon, full moon, solstice, equinox or \
cross-quarter day and helps her meet the moment: a little lore, why it is \
meaningful, and a few gentle suggestions. She reads it on her phone and may \
plan around it, so it should feel calm, small and consistent.

The facts you receive (dates, times, signs, nakshatras, Sun positions) were \
computed by code and are correct. Use them as given. Do not restate the date, \
time or signs in a way that changes them, and never introduce dates, times, \
signs or nakshatras of your own.

Tone: warm, grounded, sincere, a little poetic. Never salesy or self-help. No \
hype and no "manifest your best life" language. Write in plain second person.

Frame spiritual and astrological content symbolically and within its \
tradition ("in Vedic tradition...", "symbolically..."). Don't present \
astrological interpretation as objective fact, and don't add scientific \
disclaimers either.

Tradition: draw the lore mainly from one tradition, and choose a different one \
from those listed as recently used. The pool includes Vedic/Hindu, \
Celtic/Gaelic, Greek/Roman, Norse/Germanic, European folk and agricultural, \
the Chinese lunar calendar, and others where the connection is genuine. Only \
use lore that is well documented. If you are unsure of a detail, choose a \
better-known thread rather than inventing one. Report the tradition you drew \
on in `tradition_used` as a short name like "Vedic" or "Celtic".

Do not borrow, describe or invent Indigenous ceremonial practices, including \
those of the Coast Salish and Kwakwaka'wakw peoples whose lands she lives on. \
The `outside` suggestion should come from the land itself instead.

Place: she lives on Vancouver Island, BC. The `outside` field should fit what \
is actually happening there this time of year; a seasonal note is provided. \
Suggest one specific, doable thing.

Rituals take about 15 minutes and use things most homes have (a candle, a \
bowl of water, paper, salt, a cup of tea, a window).

Keep it small: one idea per field, never a list of options. No markdown \
headings or bullet points inside fields.

Brief shape by tier:
- anchor (solstice, equinox, cross-quarter): the fullest brief. Lore is one or \
two short paragraphs (separate paragraphs with a blank line). Every field \
filled; `go_deeper` is one book, practice or idea to explore further, or null.
- full_moon: compact. Lore is 3-5 sentences. Every field filled except \
`go_deeper`, which may be null. Frame around culmination, illumination, \
release and gratitude.
- new_moon: lighter and quieter. Lore is 2-3 sentences. One reflection prompt, \
one small ritual. `outside` and `go_deeper` may be null. Frame around \
beginnings, intention, rest and the dark, inward part of the cycle, including \
Amavasya's traditional associations with ancestors and inner work.
"""

FACT_KEYS = ["id", "type", "tier", "name", "local", "northern_name", "traditional_date",
             "sun_longitude", "tropical_sign", "tropical_degree", "sidereal_sign",
             "sidereal_degree", "nakshatra", "nakshatra_number", "vedic_name"]


def build_user_message(event: Event, recent_traditions: list[str]) -> str:
    data = event.to_dict()
    payload = {
        "event": {k: data[k] for k in FACT_KEYS if k in data},
        "display": {"title": facts.title(event), "when_line": facts.when_line(event),
                    "systems_line": facts.systems_line(event)},
        "month": event.local.strftime("%B"),
        "seasonal_note": SEASONAL_NOTES[event.local.month],
        "recently_used_traditions": recent_traditions,
    }
    return f"Write the brief for this event.\n\n{json.dumps(payload, indent=2)}"


def _ask(client: anthropic.Anthropic, model: str, user_message: str) -> Prose:
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_config={"format": {"type": "json_schema", "schema": PROSE_SCHEMA}},
    )
    if response.stop_reason != "end_turn":
        raise ValueError(f"unexpected stop_reason {response.stop_reason!r}")
    text = next(b.text for b in response.content if b.type == "text")
    return Prose.model_validate_json(text)


def fallback_brief(event: Event) -> dict:
    """Facts only, for when the writer fails twice."""
    return {**header(event), "lore": None, "why_it_matters": None,
            "reflection_prompt": None, "ritual": None, "outside": None,
            "go_deeper": None, "tradition_used": None, "fallback": True}


def header(event: Event) -> dict:
    return {"title": facts.title(event), "when_line": facts.when_line(event),
            "systems_line": facts.systems_line(event)}


def write_brief(event: Event, recent_traditions: list[str],
                client: Optional[anthropic.Anthropic] = None) -> dict:
    model = os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)
    user_message = build_user_message(event, recent_traditions)
    client = client or anthropic.Anthropic()
    for attempt in (1, 2):
        try:
            prose = _ask(client, model, user_message)
        except (ValidationError, ValueError, StopIteration) as exc:
            log.warning("writer attempt %d failed for %s: %s", attempt, event.id, exc)
            continue
        if event.tier != "new_moon" and not prose.outside:
            log.warning("writer attempt %d for %s left out `outside`", attempt, event.id)
            continue
        return {**header(event), **prose.model_dump()}
    return fallback_brief(event)
