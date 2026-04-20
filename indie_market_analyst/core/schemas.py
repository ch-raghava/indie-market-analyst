"""Universal Pydantic schemas passed between agents in the swarm.

Every specialist agent declares one of these (or a subclass) as its `output_type`
so handoffs carry typed data, not free prose.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


# ---------- shared primitives ----------

class DataPoint(_Strict):
    """A single verified fact pulled from a tool call."""
    symbol: str
    field: str                        # e.g. "close", "volume", "oi", "iv"
    value: float
    as_of: datetime
    source: str                       # "yfinance" | "nse_bhavcopy" | "google_finance" | ...
    exchange: Literal["NSE", "BSE", "NFO", "BFO", "OTHER"] = "NSE"
    unit: str = "INR"


class ToolCallTrace(_Strict):
    tool: str
    args: dict[str, Any]
    ok: bool
    error: str | None = None
    at: datetime


# ---------- agent IO contracts ----------

class CollectorOutput(_Strict):
    """Raw, verified data scraped by the Collector agent."""
    session_id: str
    universe: list[str]               # symbols touched this run
    points: list[DataPoint]
    traces: list[ToolCallTrace] = Field(default_factory=list)


class VerifiedFacts(_Strict):
    """Collector output after the Verifier cross-checks sources."""
    session_id: str
    points: list[DataPoint]
    rejected: list[DataPoint] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Calculation(_Strict):
    name: str                         # "nifty_daily_return", "adv_decline_ratio", etc.
    value: float
    unit: str = ""
    inputs: list[str] = Field(default_factory=list)  # references to DataPoint ids


class CalculationBundle(_Strict):
    session_id: str
    calculations: list[Calculation]
    warnings: list[str] = Field(default_factory=list)


class ReportDraft(_Strict):
    """What the Report Writer hands back to the orchestrator."""
    session_id: str
    title: str
    markdown: str
    pdf_path: str | None = None


class AnalystTurn(_Strict):
    """Final user-facing response envelope."""
    session_id: str
    run_id: str
    message_markdown: str
    artifacts: list[str] = Field(default_factory=list)  # file paths
    used_tools: list[str] = Field(default_factory=list)


class EquityResearchNote(_Strict):
    """Structured output for the equity_researcher agent.

    Constrains the agent to return typed fields so it cannot emit free-form
    reasoning as the user-facing answer. A small formatter converts this to
    markdown downstream.
    """
    symbol: str
    exchange: Literal["NSE", "BSE", "NFO", "BFO", "OTHER"] = "NSE"
    as_of: datetime
    last_price: DataPoint
    technicals: list[DataPoint] = Field(default_factory=list)
    setup: str                              # short, plain-prose setup description
    invalidation: str                       # short, plain-prose invalidation level
    sources: list[str] = Field(default_factory=list)
    message_markdown: str | None = None     # optional pre-rendered markdown
