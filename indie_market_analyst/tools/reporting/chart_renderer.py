"""Render charts to PNG (base64 inline or file)."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yfinance as yf  # noqa: E402
from agents import function_tool  # noqa: E402
from pydantic import BaseModel  # noqa: E402


class ChartArtifact(BaseModel):
    path: str
    png_base64: str


def _yf_symbol(symbol: str) -> str:
    return symbol if symbol.endswith((".NS", ".BO")) else f"{symbol}.NS"


@function_tool
def render_price_chart(
    symbol: str, period: str = "3mo", interval: str = "1d",
    out_dir: str = "runs",
) -> ChartArtifact:
    """Render a close-price line chart for a symbol and save to ``runs/``."""
    df = yf.Ticker(_yf_symbol(symbol)).history(period=period, interval=interval)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df.index, df["Close"])
    ax.set_title(f"{symbol.upper()}  {period}  {interval}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = str(Path(out_dir) / f"{symbol.upper()}_{period}_{interval}.png")
    fig.savefig(path, dpi=120)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return ChartArtifact(path=path, png_base64=base64.b64encode(buf.getvalue()).decode())


TOOLS = [render_price_chart]
