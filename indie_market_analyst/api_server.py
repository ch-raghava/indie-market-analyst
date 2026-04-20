"""FastAPI gateway. SSE-streamed chat + run/session read APIs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .agent.orchestrator import run_turn
from .memory.store import get_store

load_dotenv()

app = FastAPI(title="indie-market-analyst", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    team: str | None = None


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def gen():
        async for ev in run_turn(req.message, session_id=req.session_id, team_override=req.team):
            payload: Any = ev.data
            if not isinstance(payload, (str, dict, list, int, float, bool)) and payload is not None:
                payload = str(payload)
            yield {"event": ev.kind, "data": json.dumps(payload, default=str)}
    return EventSourceResponse(gen())


@app.get("/sessions")
def list_sessions(limit: int = 200):
    return get_store().list_sessions(limit=limit)


@app.get("/sessions/search")
def search_sessions(q: str = "", limit: int = 50):
    return get_store().search_messages(q, limit=limit)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    ok = get_store().delete_session(session_id)
    if not ok:
        raise HTTPException(404, "unknown session")
    return {"ok": True, "id": session_id}


@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    store = get_store()
    if not store.session_exists(session_id):
        raise HTTPException(404, "unknown session")
    return store.get_messages(session_id)


@app.get("/runs")
def list_runs(session_id: str | None = None, limit: int = 50):
    return get_store().list_runs(session_id=session_id, limit=limit)


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    r = get_store().get_run(run_id)
    if not r:
        raise HTTPException(404, "unknown run")
    return r


@app.get("/artifacts/{path:path}")
def get_artifact(path: str):
    # Only allow serving from runs/
    safe = Path("runs") / path
    if not safe.resolve().is_file() or "runs" not in str(safe.resolve()):
        raise HTTPException(404, "not found")
    return FileResponse(str(safe))


@app.get("/health")
def health():
    return {"status": "ok"}
