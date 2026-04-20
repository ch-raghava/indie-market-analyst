"""Append a short disclaimer + UTC timestamp to final analyst turns."""

from __future__ import annotations

from datetime import UTC, datetime

DISCLAIMER = (
    "\n\n---\n"
    "_For research and education only. Not investment advice. "
    "Data timestamps are UTC._"
)


def decorate(markdown: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if DISCLAIMER.strip() in markdown:
        return markdown
    return f"{markdown}\n\n_Generated at {stamp}._{DISCLAIMER}"
