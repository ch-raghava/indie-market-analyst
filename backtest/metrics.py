"""Institutional-grade metrics on a returns Series."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _annualization(freq: str) -> int:
    return {"D": 252, "W": 52, "M": 12}.get(freq.upper(), 252)


_ZERO_STD_ATOL = 1e-12


def sharpe(returns: pd.Series, rf: float = 0.0, freq: str = "D") -> float:
    r = returns.dropna() - rf / _annualization(freq)
    if r.empty:
        return 0.0
    sd = float(r.std())
    if sd < _ZERO_STD_ATOL:
        return 0.0
    return float(np.sqrt(_annualization(freq)) * r.mean() / sd)


def sortino(returns: pd.Series, rf: float = 0.0, freq: str = "D") -> float:
    r = returns.dropna() - rf / _annualization(freq)
    if r.empty:
        return 0.0
    dn = r[r < 0]
    sd = float(dn.std()) if len(dn) > 1 else 0.0
    if sd < _ZERO_STD_ATOL:
        return 0.0
    return float(np.sqrt(_annualization(freq)) * r.mean() / sd)


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def annualized_return(returns: pd.Series, freq: str = "D") -> float:
    r = returns.dropna()
    if r.empty:
        return 0.0
    return float((1 + r).prod() ** (_annualization(freq) / len(r)) - 1)


def summary(equity: pd.Series, returns: pd.Series, freq: str = "D") -> dict[str, float]:
    return {
        "annualized_return": annualized_return(returns, freq),
        "sharpe": sharpe(returns, freq=freq),
        "sortino": sortino(returns, freq=freq),
        "max_drawdown": max_drawdown(equity),
        "volatility_annualized": float(returns.std() * np.sqrt(_annualization(freq))),
    }
