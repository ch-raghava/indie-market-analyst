"""Minimal vectorized daily-bar equity backtester.

Signals: a pandas Series indexed by date with values in {-1, 0, 1}
(short/flat/long). Prices: a DataFrame with a ``close`` column.

Costs are applied per turnover, using the Indian cost model in ``_market_hooks``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ._market_hooks import CostConfig, costs_equity


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    returns: pd.Series
    positions: pd.Series
    turnover: float
    total_costs: float


def run_equity(
    prices: pd.DataFrame,
    signals: pd.Series,
    initial_capital: float = 1_00_000.0,
    intraday: bool = False,
    cost_cfg: CostConfig | None = None,
) -> BacktestResult:
    if "close" not in prices.columns:
        raise ValueError("prices DataFrame must have a 'close' column")
    close = prices["close"].astype(float)
    pos = signals.reindex(close.index).fillna(0.0)

    gross_ret = pos.shift(1).fillna(0.0) * close.pct_change().fillna(0.0)
    trade_value = close * pos.diff().abs().fillna(0.0) * initial_capital / close.iloc[0]
    # Cost per trade: split turnover into equal buy+sell notional approximations
    per_side = trade_value / 2.0
    costs = [
        costs_equity(v, v, intraday=intraday, cfg=cost_cfg)["total"] if v > 0 else 0.0
        for v in per_side
    ]
    cost_series = pd.Series(costs, index=close.index)
    net_ret = gross_ret - (cost_series / initial_capital)

    equity = (1.0 + net_ret).cumprod() * initial_capital
    return BacktestResult(
        equity_curve=equity, returns=net_ret, positions=pos,
        turnover=float(pos.diff().abs().sum()),
        total_costs=float(cost_series.sum()),
    )
