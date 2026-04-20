import numpy as np
import pandas as pd

from backtest.metrics import max_drawdown, sharpe, summary


def test_sharpe_of_constant_is_zero():
    r = pd.Series([0.001] * 252)
    assert sharpe(r) == 0.0  # std is 0


def test_drawdown_sign():
    eq = pd.Series([100, 110, 90, 95, 120])
    dd = max_drawdown(eq)
    assert dd < 0
    # peak 110 -> trough 90 = -18.18%
    assert abs(dd + (110 - 90) / 110) < 1e-9


def test_summary_keys():
    np.random.seed(0)
    r = pd.Series(np.random.normal(0.0005, 0.01, 252))
    eq = (1 + r).cumprod() * 100
    s = summary(eq, r)
    assert set(s) == {
        "annualized_return", "sharpe", "sortino",
        "max_drawdown", "volatility_annualized",
    }
