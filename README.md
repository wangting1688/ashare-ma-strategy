# AShare MA Strategy

A-share V9/V5 dynamic moving-average strategy toolkit.

This repository organizes a personal A-share quantitative strategy into a reusable open-source Python project. It includes signal detection, a simple single-symbol backtest engine, command-line tools, examples, and documentation.

## Strategy

- Market regime:
  - Shanghai Composite close > MA30: bull market, use V9.
  - Shanghai Composite close <= MA30: bear market, use V5.
- V9 buy signals:
  1. MA5 crosses above MA10, and MA10 > MA30 or MA10 > MA20 > MA30.
  2. MA10 crosses above MA30.
  3. MA10 crosses above MA20, and MA10 > MA20 > MA30.
- V5 buy signals:
  1. MA10 crosses above MA30.
  2. MA10 crosses above MA20, and MA10 > MA20 > MA30.
- Trend-strength filter:
  - close >= 20-day high * 0.88.
- Sell signals:
  - Trailing stop: current low touches highest price since buy * 0.88.
  - Dead cross: MA5 crosses below MA10.

## Install

```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev,data]
```

On macOS/Linux:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev,data]
```

## Quick start

Check latest buy signal:

```bash
ashare-ma signal --stock examples/data/sample_stock.csv --index examples/data/sample_index.csv
```

Check latest sell signal:

```bash
ashare-ma sell --stock examples/data/sample_stock.csv --buy-price 10.0 --buy-date 2026-01-05
```

Run a single-symbol backtest:

```bash
ashare-ma backtest --stock examples/data/sample_stock.csv --code sh600000 --regime unknown --output result.json
```

## Python API

```python
import pandas as pd
from ashare_ma_strategy import MarketRegime, detect_buy_signal, run_backtest

stock = pd.read_csv("examples/data/sample_stock.csv")
signal = detect_buy_signal(stock, market_regime=MarketRegime.UNKNOWN)
print(signal)

result = run_backtest(stock, market_regime=MarketRegime.UNKNOWN, code="sh600000")
print(result["summary"])
```

## CSV format

The toolkit supports both English and common Chinese column names:

| Required | English | Chinese |
|---|---|---|
| date | date | 交易日期 |
| open | open | 开盘价 |
| high | high | 最高价 |
| low | low | 最低价 |
| close | close | 收盘价 |
| volume | volume | 成交量 |

## Project structure

```text
ashare-ma-strategy/
├─ src/ashare_ma_strategy/   # package code
├─ examples/                 # runnable examples
├─ examples/data/            # small sample CSV files only
├─ tests/                    # pytest tests
├─ docs/                     # strategy notes
├─ pyproject.toml            # package metadata
└─ README.md
```

## Important disclaimer

This project is for research and education only. It is not investment advice. Backtest results are sensitive to data quality, adjustment method, transaction costs, slippage, survivorship bias, and market regime changes.
