"""Minimal signal demo."""

import pandas as pd

from ashare_ma_strategy import MarketRegime, detect_buy_signal, infer_market_regime

stock = pd.read_csv("examples/data/sample_stock.csv")
index = pd.read_csv("examples/data/sample_index.csv")
regime = infer_market_regime(index)

print("market regime:", regime.value)
print(detect_buy_signal(stock, market_regime=MarketRegime.UNKNOWN))
