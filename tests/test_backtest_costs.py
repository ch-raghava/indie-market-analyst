from backtest.engines._market_hooks import costs_equity


def test_delivery_costs_positive():
    c = costs_equity(buy_value=100_000, sell_value=110_000, intraday=False)
    assert c["total"] > 0
    # STT delivery is 0.1% on both sides = 210
    assert abs(c["stt"] - (100_000 + 110_000) * 0.001) < 1e-6


def test_intraday_costs_cheaper_stamp():
    intr = costs_equity(1_00_000, 1_00_000, intraday=True)
    deliv = costs_equity(1_00_000, 1_00_000, intraday=False)
    assert intr["stamp"] < deliv["stamp"]


def test_brokerage_cap_intraday():
    # Very large trade: intraday brokerage should cap at ₹20/side = ₹40 total
    c = costs_equity(buy_value=1e9, sell_value=1e9, intraday=True)
    assert c["brokerage"] == 40.0
