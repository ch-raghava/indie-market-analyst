"""Lightweight technical-indicator tools built on pandas-ta."""

from __future__ import annotations

from typing import Literal

import pandas as pd
import pandas_ta as ta
import yfinance as yf
from agents import function_tool
from pydantic import BaseModel

Exchange = Literal["NSE", "BSE"]


def _history_df(symbol: str, exchange: Exchange, period: str, interval: str) -> pd.DataFrame:
    yf_symbol = symbol if symbol.endswith((".NS", ".BO")) else (
        f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    )
    return yf.Ticker(yf_symbol).history(period=period, interval=interval, auto_adjust=False)


class IndicatorResult(BaseModel):
    symbol: str
    name: str
    values_tail: list[float]
    last: float
    period: str
    interval: str
    source: str = "pandas-ta@yfinance"


def _tail_floats(series: pd.Series, n: int = 10) -> list[float]:
    s = series.dropna().tail(n)
    return [float(v) for v in s.tolist()]


@function_tool
def rsi(
    symbol: str, length: int = 14,
    period: str = "3mo", interval: str = "1d", exchange: Exchange = "NSE",
) -> IndicatorResult:
    """Relative Strength Index."""
    df = _history_df(symbol, exchange, period, interval)
    series = ta.rsi(df["Close"], length=length)
    return IndicatorResult(
        symbol=symbol.upper(), name=f"RSI_{length}",
        values_tail=_tail_floats(series), last=float(series.dropna().iloc[-1]),
        period=period, interval=interval,
    )


@function_tool
def sma(
    symbol: str, length: int = 50,
    period: str = "6mo", interval: str = "1d", exchange: Exchange = "NSE",
) -> IndicatorResult:
    """Simple Moving Average on Close."""
    df = _history_df(symbol, exchange, period, interval)
    series = ta.sma(df["Close"], length=length)
    return IndicatorResult(
        symbol=symbol.upper(), name=f"SMA_{length}",
        values_tail=_tail_floats(series), last=float(series.dropna().iloc[-1]),
        period=period, interval=interval,
    )


class MacdResult(BaseModel):
    symbol: str
    macd_last: float
    signal_last: float
    hist_last: float
    period: str
    interval: str
    source: str = "pandas-ta@yfinance"


@function_tool
def macd(
    symbol: str, fast: int = 12, slow: int = 26, signal: int = 9,
    period: str = "6mo", interval: str = "1d", exchange: Exchange = "NSE",
) -> MacdResult:
    """MACD (fast, slow, signal) on Close."""
    df = _history_df(symbol, exchange, period, interval)
    out = ta.macd(df["Close"], fast=fast, slow=slow, signal=signal).dropna()
    last = out.iloc[-1]
    return MacdResult(
        symbol=symbol.upper(),
        macd_last=float(last[f"MACD_{fast}_{slow}_{signal}"]),
        signal_last=float(last[f"MACDs_{fast}_{slow}_{signal}"]),
        hist_last=float(last[f"MACDh_{fast}_{slow}_{signal}"]),
        period=period, interval=interval,
    )


TOOLS = [rsi, sma, macd]
