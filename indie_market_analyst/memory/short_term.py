"""Per-session scratchpad the agents can read/write during a single turn.

Kept in-memory (process-local) to avoid hammering SQLite during streaming. A
session's scratchpad is flushed into ``observations`` at end-of-turn if tagged
high-value.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

_buffers: dict[str, list[dict[str, Any]]] = defaultdict(list)
_lock = threading.Lock()


def append(session_id: str, item: dict[str, Any]) -> None:
    with _lock:
        _buffers[session_id].append(item)


def drain(session_id: str) -> list[dict[str, Any]]:
    with _lock:
        items = _buffers.pop(session_id, [])
    return items


def peek(session_id: str) -> list[dict[str, Any]]:
    with _lock:
        return list(_buffers.get(session_id, []))
