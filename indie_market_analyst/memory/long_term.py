"""Thin semantic-ish layer over ``observations``.

No vector DB yet — retrieval is tag + recency. Good enough for single-user dev;
swap to pgvector/Chroma later without touching callers.
"""

from __future__ import annotations

from typing import Any

from .store import get_store


def remember(text: str, tag: str | None = None, session_id: str | None = None,
             meta: dict[str, Any] | None = None) -> str:
    return get_store().add_observation(text=text, tag=tag, session_id=session_id, meta=meta)


def recall(tag: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    return get_store().recent_observations(tag=tag, limit=limit)
