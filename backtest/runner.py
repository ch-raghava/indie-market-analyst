"""End-to-end backtest orchestrator (imperative)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from . import loaders  # noqa: F401  -- registers loaders
from .engines.equity_engine import BacktestResult, run_equity
from .loaders.registry import load
from .metrics import summary


def run(
    symbol: str, signals: pd.Series, *,
    period: str = "1y", interval: str = "1d",
    initial_capital: float = 1_00_000.0, intraday: bool = False,
    loader: str = "yfinance", out_dir: str | Path = "runs",
) -> dict[str, Any]:
    df = load(loader, symbol=symbol, period=period, interval=interval)
    result: BacktestResult = run_equity(df, signals, initial_capital, intraday=intraday)
    stats = summary(result.equity_curve, result.returns)
    blob = {
        "run_id": str(uuid.uuid4()),
        "symbol": symbol, "period": period, "interval": interval,
        "initial_capital": initial_capital, "intraday": intraday,
        "stats": stats,
        "turnover": result.turnover, "total_costs": result.total_costs,
        "equity_curve_tail": result.equity_curve.tail(20).to_dict(),
    }
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"backtest_{blob['run_id'][:8]}.json"
    path.write_text(json.dumps(blob, default=str, indent=2))
    blob["path"] = str(path)
    return blob
