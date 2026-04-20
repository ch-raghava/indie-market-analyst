"""Deterministic intent router. Maps user text → swarm team name.

Keyword-based to keep cost near zero. The orchestrator agent inside a team can
still reroute via its own handoffs.
"""

from __future__ import annotations

_RULES = [
    (("eod", "end of day", "market report", "daily report", "pdf report"),
     "eod_report_pipeline"),
    (("equity", "stock", "technicals", "rsi", "macd", "sma"),
     "equity_research"),
]

_DEFAULT_TEAM = "equity_research"


def pick_team(text: str) -> str:
    t = text.lower()
    for keywords, team in _RULES:
        if any(k in t for k in keywords):
            return team
    return _DEFAULT_TEAM
