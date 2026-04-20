"""Registry of data loaders (symbol → pandas DataFrame)."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

_loaders: dict[str, Callable[..., pd.DataFrame]] = {}


def register(name: str, fn: Callable[..., pd.DataFrame]) -> None:
    _loaders[name] = fn


def available() -> list[str]:
    return sorted(_loaders)


def load(name: str, **kwargs) -> pd.DataFrame:
    if name not in _loaders:
        raise KeyError(f"unknown loader: {name}. Available: {available()}")
    return _loaders[name](**kwargs)
