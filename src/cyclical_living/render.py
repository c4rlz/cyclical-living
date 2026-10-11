"""Turn a brief dict into readable text."""

SECTIONS = [
    ("lore", "Lore"),
    ("why_it_matters", "Why it matters"),
    ("reflection_prompt", "Reflection"),
    ("ritual", "Small ritual"),
    ("outside", "Outside"),
    ("go_deeper", "Go deeper"),
]


def to_markdown(brief: dict) -> str:
    parts = [f"# {brief['title']}", f"**{brief['when_line']}**", f"*{brief['systems_line']}*"]
    for key, heading in SECTIONS:
        if brief.get(key):
            parts.append(f"## {heading}\n\n{brief[key]}")
    if brief.get("tradition_used"):
        parts.append(f"*Tradition: {brief['tradition_used']}*")
    return "\n\n".join(parts) + "\n"
