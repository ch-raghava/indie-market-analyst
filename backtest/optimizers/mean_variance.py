"""Mean-variance optimizer (closed-form, long-only simplex projection)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def optimize_mv(returns: pd.DataFrame, risk_aversion: float = 5.0) -> pd.Series:
    mu = returns.mean().values
    cov = returns.cov().values
    inv = np.linalg.pinv(cov)
    w = inv @ mu / risk_aversion
    w = np.clip(w, 0, None)
    if w.sum() == 0:
        w = np.ones_like(w) / len(w)
    else:
        w = w / w.sum()
    return pd.Series(w, index=returns.columns)
