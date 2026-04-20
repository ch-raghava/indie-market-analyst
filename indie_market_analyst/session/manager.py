"""Session lifecycle + per-session concurrency lock.

One asyncio lock per session prevents two parallel user requests on the same
session from corrupting each other's short-term scratchpad.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from ..memory.store import get_store


@dataclass
class Session:
    id: str
    meta: dict[str, Any] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


_sessions: dict[str, Session] = {}


def new_session(meta: dict[str, Any] | None = None) -> Session:
    sid = get_store().create_session(meta or {})
    s = Session(id=sid, meta=meta or {})
    _sessions[sid] = s
    return s


def get_session(session_id: str) -> Session:
    s = _sessions.get(session_id)
    if s:
        return s
    # Rehydrate from persistent store if we don't have it in memory yet.
    if not get_store().session_exists(session_id):
        raise KeyError(f"unknown session {session_id}")
    s = Session(id=session_id)
    _sessions[session_id] = s
    return s
