import json
from datetime import date
from types import SimpleNamespace

import pytest

from cyclical_living import writer
from cyclical_living.events import compute_events


def event(event_id):
    return next(e for e in compute_events(date(2026, 10, 1), date(2027, 1, 31)) if e.id == event_id)


GOOD = {"lore": "Hunter's Moon lore.", "why_it_matters": "Why.", "reflection_prompt": "What?",
        "ritual": "Light a candle.", "outside": "Visit a creek.", "go_deeper": None,
        "tradition_used": "European folk"}


class FakeClient:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        text = reply if isinstance(reply, str) else json.dumps(reply)
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text=text)])


def test_facts_come_from_code_not_model():
    client = FakeClient({**GOOD})
    brief = writer.write_brief(event("full_moon-2026-10-25"), [], client=client)
    assert brief["title"] == "Full Moon in Taurus"
    assert brief["when_line"] == "Sunday Oct 25 · 9:12 pm PT"
    assert brief["systems_line"] == "Tropical: Taurus · Sidereal: Aries, Ashwini · Purnima"
    assert brief["tradition_used"] == "European folk"


def test_prompt_carries_facts_season_and_recent_traditions():
    client = FakeClient(GOOD)
    writer.write_brief(event("full_moon-2026-10-25"), ["Vedic", "Celtic"], client=client)
    payload = client.calls[0]["messages"][0]["content"]
    assert '"nakshatra": "Ashwini"' in payload
    assert "chum salmon" in payload.lower()
    assert '"Vedic"' in payload and '"Celtic"' in payload
    assert client.calls[0]["model"] == "claude-sonnet-5-5"


def test_model_env_var(monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL", "claude-opus-5-5")
    client = FakeClient(GOOD)
    writer.write_brief(event("full_moon-2026-10-25"), [], client=client)
    assert client.calls[0]["model"] == "claude-opus-5-5"


def test_retries_once_on_bad_json():
    client = FakeClient("not json", GOOD)
    brief = writer.write_brief(event("full_moon-2026-10-25"), [], client=client)
    assert brief["lore"] == GOOD["lore"]
    assert len(client.calls) == 2


def test_falls_back_to_facts_after_two_failures():
    client = FakeClient("not json", {"lore": "missing fields"})
    brief = writer.write_brief(event("full_moon-2026-10-25"), [], client=client)
    assert brief["fallback"] is True
    assert brief["title"] == "Full Moon in Taurus"
    assert brief["lore"] is None


def test_outside_optional_only_for_new_moons():
    no_outside = {**GOOD, "outside": None}
    assert writer.write_brief(event("new_moon-2026-11-09"), [], client=FakeClient(no_outside))["ritual"]
    assert writer.write_brief(event("full_moon-2026-10-25"), [], client=FakeClient(no_outside, no_outside))["fallback"]


@pytest.mark.parametrize("event_id,systems", [
    ("samhain-2026-11-07", "Astronomical midpoint (Sun at 225°) · Traditionally Oct 31"),
    ("december_solstice-2026-12-21", "December Solstice · Sun enters Capricorn"),
])
def test_anchor_headers(event_id, systems):
    assert writer.header(event(event_id))["systems_line"] == systems
