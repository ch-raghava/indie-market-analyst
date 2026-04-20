"""yfinance-backed quote/history tools.

NSE symbols need the ``.NS`` suffix (e.g. ``RELIANCE.NS``); BSE needs ``.BO``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

import yfinance as yf
from agents import function_tool
from pydantic import BaseModel

Exchange = Literal["NSE", "BSE"]


def _yf_symbol(symbol: str, exchange: Exchange) -> str:
    if symbol.endswith((".NS", ".BO")):
        return symbol
    return f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"


class Quote(BaseModel):
    symbol: str
    exchange: Exchange
    price: float
    change_pct: float | None
    day_high: float | None
    day_low: float | None
    prev_close: float | None
    volume: int | None
    as_of_utc: str
    source: str = "yfinance"


class OhlcBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class History(BaseModel):
    symbol: str
    exchange: Exchange
    period: str
    interval: str
    bars: list[OhlcBar]
    source: str = "yfinance"


@function_tool
def get_quote(symbol: str, exchange: Exchange = "NSE") -> Quote:
    """Fetch the latest quote for an Indian listed ticker via yfinance.

    Args:
        symbol: Ticker without suffix (e.g. ``RELIANCE``). ``.NS``/``.BO`` is added.
        exchange: ``NSE`` (default) or ``BSE``.
    """
    t = yf.Ticker(_yf_symbol(symbol, exchange))
    info = t.fast_info
    price = float(info.last_price) if info.last_price is not None else float("nan")
    prev = float(info.previous_close) if info.previous_close is not None else None
    change_pct = ((price - prev) / prev * 100.0) if (prev and prev != 0) else None
    return Quote(
        symbol=symbol.upper(),
        exchange=exchange,
        price=price,
        change_pct=change_pct,
        day_high=float(info.day_high) if info.day_high is not None else None,
        day_low=float(info.day_low) if info.day_low is not None else None,
        prev_close=prev,
        volume=int(info.last_volume) if info.last_volume is not None else None,
        as_of_utc=datetime.now(UTC).isoformat(),
    )


@function_tool
def get_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
    exchange: Exchange = "NSE",
) -> History:
    """Fetch OHLCV history. ``period`` e.g. ``1mo``, ``3mo``, ``1y``; ``interval``
    ``1d``, ``1h``, ``15m``."""
    t = yf.Ticker(_yf_symbol(symbol, exchange))
    df = t.history(period=period, interval=interval, auto_adjust=False)
    bars = [
        OhlcBar(
            date=str(idx.date() if hasattr(idx, "date") else idx),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]) if row["Volume"] == row["Volume"] else 0,
        )
        for idx, row in df.iterrows()
    ]
    return History(
        symbol=symbol.upper(), exchange=exchange, period=period, interval=interval, bars=bars,
    )


TOOLS = [get_quote, get_history]
