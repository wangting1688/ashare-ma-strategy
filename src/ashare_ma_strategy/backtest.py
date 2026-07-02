"""Simple reusable backtesting engine for the V9/V5 strategy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import pandas as pd

from .signals import MarketRegime, StrategyConfig, add_indicators, buy_v5, buy_v9


@dataclass(frozen=True)
class BacktestConfig:
    """Backtest parameters."""

    initial_cash_per_trade: float = 1_000_000.0
    trend_threshold: float = 0.88
    trailing_stop_ratio: float = 0.88


@dataclass
class Trade:
    """Single completed trade record."""

    code: str
    buy_date: str
    buy_price: float
    sell_date: str
    sell_price: float
    shares: int
    pnl: float
    pnl_pct: float
    holding_days: int
    sell_reason: str
    signal: str


def summarize_trades(trades: List[Trade]) -> Dict[str, Any]:
    """Return summary statistics for completed trades."""

    total = len(trades)
    pnl = sum(t.pnl for t in trades)
    wins = sum(1 for t in trades if t.pnl > 0)
    return {
        "trades": total,
        "wins": wins,
        "win_rate": wins / total if total else 0.0,
        "total_pnl": pnl,
        "average_pnl": pnl / total if total else 0.0,
    }


def run_backtest(
    df: pd.DataFrame,
    market_regime: MarketRegime = MarketRegime.UNKNOWN,
    code: str = "UNKNOWN",
    config: BacktestConfig = BacktestConfig(),
) -> Dict[str, Any]:
    """Run a single-symbol backtest.

    When market_regime is UNKNOWN, the engine checks V9 first, then V5. For a
    production portfolio backtest, pass a daily market regime series or run this
    function separately by market phase.
    """

    data = add_indicators(df)
    strategy_config = StrategyConfig(
        trend_threshold=config.trend_threshold,
        trailing_stop_ratio=config.trailing_stop_ratio,
    )
    trades: List[Trade] = []
    position = None
    high_since_buy = 0.0

    for i in range(strategy_config.min_bars, len(data)):
        curr = data.iloc[i]
        prev = data.iloc[i - 1]

        if position is not None:
            high_since_buy = max(high_since_buy, float(curr["high"]))
            stop_price = high_since_buy * config.trailing_stop_ratio
            dead_cross = prev["ma5"] >= prev["ma10"] and curr["ma5"] < curr["ma10"]
            trailing_stop = float(curr["low"]) <= stop_price
            if dead_cross or trailing_stop:
                sell_price = float(curr["open"])
                pnl = (sell_price - position["buy_price"]) * position["shares"]
                trades.append(
                    Trade(
                        code=code,
                        buy_date=str(position["buy_date"].date()),
                        buy_price=position["buy_price"],
                        sell_date=str(curr["date"].date()),
                        sell_price=sell_price,
                        shares=position["shares"],
                        pnl=pnl,
                        pnl_pct=(sell_price - position["buy_price"]) / position["buy_price"],
                        holding_days=(curr["date"] - position["buy_date"]).days,
                        sell_reason="dead_cross" if dead_cross else "trailing_stop",
                        signal=position["signal"],
                    )
                )
                position = None
                high_since_buy = 0.0

        if position is None:
            if pd.isna(curr["trend"]) or float(curr["trend"]) < config.trend_threshold:
                continue
            if market_regime == MarketRegime.BULL:
                signal, _ = buy_v9(data, i)
            elif market_regime == MarketRegime.BEAR:
                signal, _ = buy_v5(data, i)
            else:
                signal, _ = buy_v9(data, i)
                if signal is None:
                    signal, _ = buy_v5(data, i)

            if signal:
                buy_price = float(curr["open"])
                shares = int(config.initial_cash_per_trade // buy_price)
                if shares <= 0:
                    continue
                position = {
                    "buy_date": curr["date"],
                    "buy_price": buy_price,
                    "shares": shares,
                    "signal": signal,
                }
                high_since_buy = float(curr["high"])

    trade_rows = [asdict(t) for t in trades]
    return {
        "summary": summarize_trades(trades),
        "trades": trade_rows,
    }
