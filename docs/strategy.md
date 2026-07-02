# Strategy Notes

## Core idea

The strategy combines dynamic market-regime switching, moving-average breakout/repair signals, trend-strength filtering, and a 12% trailing stop.

## Market regime

```text
Shanghai Composite close > MA30  -> Bull market -> V9
Shanghai Composite close <= MA30 -> Bear market -> V5
```

## Buy signal definitions

### V9, bull market

1. Strong golden cross: MA5 crosses above MA10, and MA10 > MA30 or MA10 > MA20 > MA30.
2. Mean-line recovery: MA10 crosses above MA30.
3. Medium rebound: MA10 crosses above MA20, and MA10 > MA20 > MA30.

### V5, bear market

1. MA10 crosses above MA30.
2. MA10 crosses above MA20, and MA10 > MA20 > MA30.

V5 is a stricter subset of V9. It removes the short-term MA5/MA10 signal to reduce false positives in weak markets.

## Trend filter

```text
close >= 20-day high * 0.88
```

This rejects rebounds that are too far below the recent high.

## Sell rules

1. Trailing stop: low <= highest price since buy * 0.88.
2. Dead cross: MA5 crosses below MA10.

When either signal is triggered, the example backtest exits at the current row's open price. Adjust this execution assumption for your own research.

## Research hygiene

- Use adjusted prices consistently.
- Include transaction costs and slippage in production-grade backtests.
- Avoid survivorship bias in index component lists.
- Treat high historical win rates as a hypothesis, not a guarantee.
