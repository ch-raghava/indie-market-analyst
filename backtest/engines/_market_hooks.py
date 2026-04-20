"""Indian equity cost model.

Stamp duty, STT, exchange txn charges, SEBI fee, GST, and a default
Zerodha-style brokerage. Rates reflect 2026 slabs and will change; centralize
edits here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostConfig:
    # All rates are fractions (e.g. 0.001 = 0.1%)
    stt_delivery: float = 0.001            # 0.1% buy + sell
    stt_intraday_sell: float = 0.00025     # 0.025% on sell side
    stamp_duty_buy: float = 0.00015        # 0.015% on buy (delivery)
    stamp_duty_intra_buy: float = 0.00003  # 0.003% on buy (intraday)
    exch_txn: float = 0.0000325            # NSE equity
    sebi: float = 0.000001                 # ₹10/crore
    gst: float = 0.18                      # on brokerage + exch + sebi
    brokerage_intraday: float = 0.0003     # 0.03% or ₹20/side (cap applied below)
    brokerage_delivery: float = 0.0         # Zerodha delivery = 0
    brokerage_cap_per_side: float = 20.0


def costs_equity(
    buy_value: float, sell_value: float, *, intraday: bool = False,
    cfg: CostConfig | None = None,
) -> dict[str, float]:
    cfg = cfg or CostConfig()

    if intraday:
        brokerage = min(buy_value * cfg.brokerage_intraday, cfg.brokerage_cap_per_side) \
            + min(sell_value * cfg.brokerage_intraday, cfg.brokerage_cap_per_side)
        stt = sell_value * cfg.stt_intraday_sell
        stamp = buy_value * cfg.stamp_duty_intra_buy
    else:
        brokerage = buy_value * cfg.brokerage_delivery + sell_value * cfg.brokerage_delivery
        stt = (buy_value + sell_value) * cfg.stt_delivery
        stamp = buy_value * cfg.stamp_duty_buy

    exch = (buy_value + sell_value) * cfg.exch_txn
    sebi = (buy_value + sell_value) * cfg.sebi
    gst = (brokerage + exch + sebi) * cfg.gst

    total = brokerage + stt + stamp + exch + sebi + gst
    return {
        "brokerage": brokerage, "stt": stt, "stamp": stamp, "exch": exch,
        "sebi": sebi, "gst": gst, "total": total,
    }
