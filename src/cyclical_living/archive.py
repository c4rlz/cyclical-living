"""The archive is both the almanac and the state: a brief's markdown file is
written only after successful delivery, so "already sent" means "file exists".
"""
from __future__ import annotations

import json
from pathlib import Path

from .events import Event

ROOT = Path(__file__).resolve().parents[2] / "archive"


def path_for(event: Event, root: Path | None = None) -> Path:
    d = event.local_date
    return (root or ROOT) / str(d.year) / f"{d.isoformat()}-{event.type.replace('_', '-')}.md"


def is_sent(event: Event, root: Path | None = None) -> bool:
    return path_for(event, root).exists()


def _front_matter(path: Path) -> dict:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        return {}
    meta = {}
    for line in lines[1:]:
        if line == "---":
            break
        key, _, value = line.partition(": ")
        meta[key] = json.loads(value) if value else ""
    return meta


def recent_traditions(n: int = 4, root: Path | None = None) -> list[str]:
    """tradition_used from the newest n briefs, newest first."""
    files = sorted((root or ROOT).glob("*/*.md"), reverse=True)
    traditions = (_front_matter(f).get("tradition_used") for f in files)
    return [t for t in traditions if t][:n]


def write(event: Event, markdown_body: str, brief: dict, root: Path | None = None) -> Path:
    path = path_for(event, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"id": event.id, "type": event.type, "local": event.local.isoformat(),
            "tradition_used": brief.get("tradition_used")}
    head = "\n".join(f"{k}: {json.dumps(v)}" for k, v in meta.items())
    path.write_text(f"---\n{head}\n---\n\n{markdown_body}")
    return path
