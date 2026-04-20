"""Naive inverse-volatility risk parity."""

from __future__ import annotations

import numpy as np
import pandas as pd


def optimize_risk_parity(returns: pd.DataFrame) -> pd.Series:
    vol = returns.std().replace(0.0, np.nan)
    inv = 1.0 / vol
    inv = inv.fillna(0.0)
    total = inv.sum()
    return inv / total if total else pd.Series(1.0 / len(returns.columns),
                                                index=returns.columns)
