"""Deterministic intent router. Maps user text → swarm team name.

Keyword-based to keep cost near zero. The orchestrator agent inside a team can
still reroute via its own handoffs.

Rule order matters — first match wins. The default is the lightweight
`general_qa` team so vague messages (greetings, capability questions) never
get forced into a stock-research schema.
"""

from __future__ import annotations

import re

_RULES: list[tuple[tuple[str, ...], str]] = [
    (("eod", "end of day", "market report", "daily report", "pdf report"),
     "eod_report_pipeline"),
    (("news", "headline", "headlines", "sentiment", "what's happening",
      "whats happening", "what is happening", "latest updates", "buzz",
      "story", "stories", "press release", "announcement", "announcements",
      "deep dive", "full article", "full story", "read the article",
      "article body", "article details"),
     "news_pulse"),
    (("top mover", "top movers", "gainer", "gainers", "loser", "losers",
      "most active", "market today", "how is the market", "breadth",
      "advance decline", "advance/decline", "nifty", "sensex", "bank nifty",
      "index snapshot"),
     "market_pulse"),
    (("rsi", "macd", "sma", "ema", "technicals", "technical analysis",
      "chart", "setup", "breakout"),
     "equity_research"),
]

_DEFAULT_TEAM = "general_qa"

_TICKER_RE = re.compile(r"\b[A-Z]{3,10}(?:\.NS|\.BO)?\b")
_TICKER_STOPWORDS = {
    "NSE", "BSE", "NIFTY", "SENSEX", "RSI", "MACD", "SMA", "EMA", "EOD",
    "PDF", "BANK", "INDIA", "USD", "INR", "UTC", "IST", "API", "URL",
}


def _looks_like_ticker_query(text: str) -> bool:
    """True iff the user message contains a plausible ticker symbol and
    at least one equity-ish verb ("price", "quote", "stock", "share")."""
    equity_verb = re.search(
        r"\b(price|quote|stock|share|ticker|equity)\b", text, re.IGNORECASE,
    )
    if not equity_verb:
        return False
    for m in _TICKER_RE.finditer(text):
        if m.group(0) not in _TICKER_STOPWORDS:
            return True
    return False


def pick_team(text: str) -> str:
    t = text.lower()
    for keywords, team in _RULES:
        if any(k in t for k in keywords):
            return team
    if _looks_like_ticker_query(text):
        return "equity_research"
    return _DEFAULT_TEAM
