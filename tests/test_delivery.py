import io
import json
import urllib.error

import pytest

from cyclical_living import delivery, render

BRIEF = {
    "title": "Full Moon in Taurus",
    "when_line": "Sunday Oct 25 · 9:12 pm PT",
    "systems_line": "Tropical: Taurus · Sidereal: Aries, Ashwini · Purnima",
    "lore": "First paragraph.\n\nSecond <paragraph> & more.",
    "why_it_matters": "Why.",
    "reflection_prompt": "What?",
    "ritual": "Light a candle.",
    "outside": "Visit a creek.",
    "go_deeper": None,
    "tradition_used": "European folk",
}


def test_html_escapes_and_splits_paragraphs():
    html = render.to_html(BRIEF)
    assert "Second &lt;paragraph&gt; &amp; more." in html
    assert html.count("<p style") >= 4
    assert "Go deeper" not in html  # null fields are left out


def test_text_and_markdown_skip_empty_sections():
    for text in (render.to_text(BRIEF), render.to_markdown(BRIEF)):
        assert "Ashwini" in text
        assert "Go deeper".upper() not in text.upper()


def test_fallback_brief_renders_facts_only():
    fallback = {**{k: BRIEF[k] for k in ("title", "when_line", "systems_line")}, "fallback": True}
    for text in (render.to_html(fallback), render.to_text(fallback), render.to_markdown(fallback)):
        assert "just the facts" in text
        assert "full moon in taurus" in text.lower()


def test_subject():
    assert render.subject(BRIEF) == "Full Moon in Taurus · Sunday Oct 25 · 9:12 pm PT"


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return b'{"id": "abc"}'


def test_resend_payload(monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout):
        sent["url"] = request.full_url
        sent["auth"] = request.get_header("Authorization")
        sent["body"] = json.loads(request.data)
        return FakeResponse()

    monkeypatch.setattr(delivery.urllib.request, "urlopen", fake_urlopen)
    delivery.ResendEmail("re_key", "Moon <moon@example.com>", "me@example.com").send(BRIEF)
    assert sent["url"] == "https://api.resend.com/emails"
    assert sent["auth"] == "Bearer re_key"
    assert sent["body"]["to"] == ["me@example.com"]
    assert sent["body"]["subject"].startswith("Full Moon in Taurus")
    assert "<html>" in sent["body"]["html"] and "LORE" in sent["body"]["text"]


def test_resend_error_raises(monkeypatch):
    def failing(request, timeout):
        body = io.BytesIO(b'{"message": "The from domain is not verified"}')
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, body)

    monkeypatch.setattr(delivery.urllib.request, "urlopen", failing)
    with pytest.raises(RuntimeError, match="403.*not verified"):
        delivery.ResendEmail("k", "f@example.com", "t@example.com").send(BRIEF)


def test_from_env_requires_all_vars(monkeypatch):
    for key in ("RESEND_API_KEY", "FROM_EMAIL", "TO_EMAIL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("RESEND_API_KEY", "k")
    with pytest.raises(SystemExit, match="FROM_EMAIL, TO_EMAIL"):
        delivery.from_env()
