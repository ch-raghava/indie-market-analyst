"""yfinance OHLCV loader."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from .registry import register


def load_yfinance(symbol: str, period: str = "1y", interval: str = "1d",
                  exchange: str = "NSE") -> pd.DataFrame:
    yf_symbol = symbol if symbol.endswith((".NS", ".BO")) else (
        f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    )
    df = yf.Ticker(yf_symbol).history(period=period, interval=interval, auto_adjust=False)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    df["source"] = "yfinance"
    return df


register("yfinance", load_yfinance)
