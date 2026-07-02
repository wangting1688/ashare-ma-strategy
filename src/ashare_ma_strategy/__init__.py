"""A-share dynamic moving-average strategy toolkit."""

from .signals import (
    MarketRegime,
    StrategyConfig,
    add_indicators,
    detect_buy_signal,
    detect_sell_signal,
    infer_market_regime,
)
from .backtest import BacktestConfig, Trade, run_backtest

__all__ = [
    "MarketRegime",
    "StrategyConfig",
    "BacktestConfig",
    "Trade",
    "add_indicators",
    "detect_buy_signal",
    "detect_sell_signal",
    "infer_market_regime",
    "run_backtest",
]
