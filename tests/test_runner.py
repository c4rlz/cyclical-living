from datetime import date

import pytest

from cyclical_living import archive, runner
from cyclical_living.events import compute_events


def ids(events):
    return [e.id for e in events]


def test_due_on_lead_day():
    # Full moon Sun Oct 25: 2-day lead -> Fri Oct 23.
    assert ids(runner.due_events(date(2026, 10, 23))) == ["full_moon-2026-10-25"]
    assert runner.due_events(date(2026, 10, 22)) == []


def test_anchor_lead_is_seven_days():
    # Samhain Sat Nov 7 -> Sat Oct 31.
    assert "samhain-2026-11-07" in ids(runner.due_events(date(2026, 10, 31)))
    assert "samhain-2026-11-07" not in ids(runner.due_events(date(2026, 10, 30)))


def test_catch_up_until_event_day():
    # If the Oct 23 run was missed, Oct 24 and Oct 25 still pick it up; Oct 26 doesn't.
    assert "full_moon-2026-10-25" in ids(runner.due_events(date(2026, 10, 25)))
    assert "full_moon-2026-10-25" not in ids(runner.due_events(date(2026, 10, 26)))


def test_lead_times_configurable(monkeypatch):
    monkeypatch.setitem(runner.LEAD_DAYS, "full_moon", 3)
    assert ids(runner.due_events(date(2026, 10, 22))) == ["full_moon-2026-10-25"]


@pytest.fixture
def tmp_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "ROOT", tmp_path)
    return tmp_path


def fake_writer(event, recent):
    return {"title": "T", "when_line": "W", "systems_line": "S", "lore": "L",
            "tradition_used": "Norse"}


def test_run_sends_archives_and_is_idempotent(tmp_archive):
    sent = []
    assert runner.run(date(2026, 10, 23), deliver=sent.append, writer=fake_writer) == 0
    assert len(sent) == 1
    path = tmp_archive / "2026" / "2026-10-25-full-moon.md"
    assert path.exists()
    assert archive.recent_traditions() == ["Norse"]
    # Next day is still in the window, but it's already sent.
    assert runner.run(date(2026, 10, 24), deliver=sent.append, writer=fake_writer) == 0
    assert len(sent) == 1


def test_dry_run_neither_sends_nor_archives(tmp_archive, capsys):
    sent = []
    runner.run(date(2026, 10, 23), dry_run=True, deliver=sent.append, writer=fake_writer)
    assert sent == []
    assert not list(tmp_archive.rglob("*.md"))
    assert "dry run" in capsys.readouterr().out


def test_failed_delivery_is_not_recorded(tmp_archive):
    def broken(brief):
        raise ConnectionError("resend down")
    assert runner.run(date(2026, 10, 23), deliver=broken, writer=fake_writer) == 1
    assert not list(tmp_archive.rglob("*.md"))


def test_recent_traditions_newest_first(tmp_archive):
    events = compute_events(date(2026, 10, 1), date(2026, 11, 30))
    for event, tradition in zip(events, ["Vedic", "Celtic", "Greek"]):
        archive.write(event, "body", {"tradition_used": tradition})
    assert archive.recent_traditions(2) == ["Greek", "Celtic"]


def test_facts_only_send_is_archived_but_flagged(tmp_archive):
    sent = []
    facts_only = lambda event, recent: {**fake_writer(event, recent), "fallback": True}
    assert runner.run(date(2026, 10, 23), deliver=sent.append, writer=facts_only) == 1
    assert len(sent) == 1
    assert (tmp_archive / "2026" / "2026-10-25-full-moon.md").exists()
