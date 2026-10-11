"""Turn a brief dict into markdown (archive), plain text and HTML (email)."""
from html import escape

SECTIONS = [
    ("lore", "Lore"),
    ("why_it_matters", "Why it matters"),
    ("reflection_prompt", "Reflection"),
    ("ritual", "Small ritual"),
    ("outside", "Outside"),
    ("go_deeper", "Go deeper"),
]

FALLBACK_NOTE = "The writer couldn't produce a brief this time, so here are just the facts."


def subject(brief: dict) -> str:
    return f"{brief['title']} · {brief['when_line']}"


def _sections(brief: dict):
    return [(heading, brief[key]) for key, heading in SECTIONS if brief.get(key)]


def to_markdown(brief: dict) -> str:
    parts = [f"# {brief['title']}", f"**{brief['when_line']}**", f"*{brief['systems_line']}*"]
    if brief.get("fallback"):
        parts.append(FALLBACK_NOTE)
    parts += [f"## {heading}\n\n{body}" for heading, body in _sections(brief)]
    if brief.get("tradition_used"):
        parts.append(f"*Tradition: {brief['tradition_used']}*")
    return "\n\n".join(parts) + "\n"


def to_text(brief: dict) -> str:
    parts = [brief["title"].upper(), brief["when_line"], brief["systems_line"]]
    if brief.get("fallback"):
        parts.append(FALLBACK_NOTE)
    parts += [f"{heading.upper()}\n{body}" for heading, body in _sections(brief)]
    if brief.get("tradition_used"):
        parts.append(f"Tradition: {brief['tradition_used']}")
    return "\n\n".join(parts) + "\n"


# Calm palette, inline styles only: email clients ignore most <style> blocks.
PAGE = "#f6f3ee"
CARD = "#fffdf9"
INK = "#2b2a28"
MUTED = "#77726a"
ACCENT = "#5b6f63"
SERIF = "Georgia, 'Iowan Old Style', 'Times New Roman', serif"


def _paragraphs(text: str) -> str:
    return "".join(
        f'<p style="margin:0 0 12px;line-height:1.6;">{escape(p.strip())}</p>'
        for p in text.split("\n\n") if p.strip()
    )


def to_html(brief: dict) -> str:
    body = [
        f'<h1 style="margin:0 0 6px;font-size:26px;font-weight:normal;color:{INK};">{escape(brief["title"])}</h1>',
        f'<p style="margin:0 0 4px;font-size:16px;color:{INK};">{escape(brief["when_line"])}</p>',
        f'<p style="margin:0 0 24px;font-size:14px;font-style:italic;color:{MUTED};">{escape(brief["systems_line"])}</p>',
    ]
    if brief.get("fallback"):
        body.append(f'<p style="margin:0 0 12px;color:{MUTED};">{escape(FALLBACK_NOTE)}</p>')
    for heading, text in _sections(brief):
        body.append(
            f'<h2 style="margin:24px 0 8px;font-size:13px;font-weight:normal;letter-spacing:0.12em;'
            f'text-transform:uppercase;color:{ACCENT};">{escape(heading)}</h2>{_paragraphs(text)}'
        )
    if brief.get("tradition_used"):
        body.append(f'<p style="margin:28px 0 0;font-size:13px;color:{MUTED};">'
                    f'Tradition: {escape(brief["tradition_used"])}</p>')
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{PAGE};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE};"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:{CARD};border-radius:6px;">
<tr><td style="padding:32px 28px;font-family:{SERIF};font-size:17px;color:{INK};">
{''.join(body)}
</td></tr></table>
</td></tr></table>
</body></html>
"""
