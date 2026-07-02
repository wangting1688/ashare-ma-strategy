import pandas as pd

from ashare_ma_strategy import MarketRegime, detect_buy_signal, detect_sell_signal


def _base_frame(n=40):
    rows = []
    price = 10.0
    for i in range(n):
        rows.append({
            "date": f"2026-01-{(i % 28) + 1:02d}",
            "open": price,
            "high": price * 1.02,
            "low": price * 0.98,
            "close": price,
            "volume": 100000,
        })
        price += 0.05
    return pd.DataFrame(rows)


def test_detect_buy_signal_returns_dict():
    df = _base_frame()
    result = detect_buy_signal(df, market_regime=MarketRegime.UNKNOWN)
    assert "triggered" in result
    assert "reason" in result


def test_detect_sell_signal_returns_stop_price():
    df = _base_frame()
    result = detect_sell_signal(df, buy_price=10.0, buy_date="2026-01-01")
    assert "stop_price" in result
    assert "triggered" in result
