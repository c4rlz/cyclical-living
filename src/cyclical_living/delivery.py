"""Delivery channels. Anything with a send(brief) method will do, so ntfy or
Telegram can be added later as another class here."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol

from . import render


class Channel(Protocol):
    def send(self, brief: dict) -> None: ...


class ResendEmail:
    URL = "https://api.resend.com/emails"

    def __init__(self, api_key: str, from_email: str, to_email: str):
        self.api_key = api_key
        self.from_email = from_email
        self.to_email = to_email

    def send(self, brief: dict) -> None:
        payload = {
            "from": self.from_email,
            "to": [self.to_email],
            "subject": render.subject(brief),
            "html": render.to_html(brief),
            "text": render.to_text(brief),
        }
        request = urllib.request.Request(
            self.URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "cyclical-living/0.1",
            },
        )
        # urlopen raises HTTPError on any non-2xx response, so a failed send
        # never reaches the archive.
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()


def from_env() -> Channel:
    missing = [k for k in ("RESEND_API_KEY", "FROM_EMAIL", "TO_EMAIL") if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")
    return ResendEmail(os.environ["RESEND_API_KEY"], os.environ["FROM_EMAIL"], os.environ["TO_EMAIL"])
