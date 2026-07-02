"""Core V9/V5 signal logic.

Strategy summary:
- Bull market: Shanghai Composite close > MA30, use V9 signals.
- Bear market: Shanghai Composite close <= MA30, use V5 signals.
- All buy signals must pass the trend-strength filter: close >= high20 * 0.88.
- Sell signal: MA5 crosses below MA10, or trailing stop is touched.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import pandas as pd


class MarketRegime(str, Enum):
    """Market regime used to switch between V9 and V5."""

    BULL = "bull"
    BEAR = "bear"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class StrategyConfig:
    """Parameters for the dynamic moving-average strategy."""

    trend_threshold: float = 0.88
    trailing_stop_ratio: float = 0.88
    min_bars: int = 31


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common Chinese/English OHLCV column names.

    Supported source columns include:
    - 交易日期/date
    - 开盘价/open
    - 最高价/high
    - 最低价/low
    - 收盘价/close
    - 成交量/volume
    """

    mapping = {
        "交易日期": "date",
        "开盘价": "open",
        "最高价": "high",
        "最低价": "low",
        "收盘价": "close",
        "成交量": "volume",
    }
    out = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}).copy()
    required = ["date", "open", "high", "low", "close"]
    missing = [col for col in required if col not in out.columns]
    if missing:
        raise ValueError(f"Missing required OHLC columns: {missing}")

    out["date"] = pd.to_datetime(out["date"])
    for col in ["open", "high", "low", "close"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if "volume" in out.columns:
        out["volume"] = pd.to_numeric(out["volume"], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    return out.sort_values("date").reset_index(drop=True)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add MA5/MA10/MA20/MA30, high20 and trend columns."""

    out = normalize_ohlcv(df)
    for window in [5, 10, 20, 30]:
        out[f"ma{window}"] = out["close"].rolling(window, min_periods=window).mean()
    out["high20"] = out["high"].rolling(20, min_periods=20).max()
    out["trend"] = out["close"] / out["high20"]
    return out


def infer_market_regime(index_df: pd.DataFrame) -> MarketRegime:
    """Infer market regime from an index OHLC dataframe.

    Returns BULL when latest close is above MA30; otherwise BEAR.
    """

    data = add_indicators(index_df)
    if len(data) < 31:
        return MarketRegime.UNKNOWN
    row = data.iloc[-1]
    if pd.isna(row["ma30"]):
        return MarketRegime.UNKNOWN
    return MarketRegime.BULL if float(row["close"]) > float(row["ma30"]) else MarketRegime.BEAR


def _has_nan(*values: Any) -> bool:
    """Return True when any value is missing."""

    return any(pd.isna(v) for v in values)


def buy_v9(data: pd.DataFrame, i: int) -> Tuple[Optional[str], Optional[str]]:
    """Detect V9 buy signal for bull markets."""

    if i < 31:
        return None, None
    prev = data.iloc[i - 1]
    curr = data.iloc[i]
    values = [prev[f"ma{x}"] for x in [5, 10, 20, 30]] + [curr[f"ma{x}"] for x in [5, 10, 20, 30]]
    if _has_nan(*values):
        return None, None

    if prev["ma5"] < prev["ma10"] and curr["ma5"] >= curr["ma10"]:
        if curr["ma10"] > curr["ma30"] or curr["ma10"] > curr["ma20"] > curr["ma30"]:
            return "V9-1", "MA5 crosses above MA10 with medium-term confirmation"

    if prev["ma10"] < prev["ma30"] and curr["ma10"] >= curr["ma30"]:
        return "V9-2", "MA10 crosses above MA30"

    if prev["ma10"] < prev["ma20"] and curr["ma10"] >= curr["ma20"]:
        if curr["ma10"] > curr["ma20"] > curr["ma30"]:
            return "V9-3", "MA10 crosses above MA20 with bullish alignment"

    return None, None


def buy_v5(data: pd.DataFrame, i: int) -> Tuple[Optional[str], Optional[str]]:
    """Detect V5 buy signal for bear markets."""

    if i < 31:
        return None, None
    prev = data.iloc[i - 1]
    curr = data.iloc[i]
    values = [prev[f"ma{x}"] for x in [10, 20, 30]] + [curr[f"ma{x}"] for x in [10, 20, 30]]
    if _has_nan(*values):
        return None, None

    if prev["ma10"] < prev["ma30"] and curr["ma10"] >= curr["ma30"]:
        return "V5-1", "MA10 crosses above MA30"

    if prev["ma10"] < prev["ma20"] and curr["ma10"] >= curr["ma20"]:
        if curr["ma10"] > curr["ma20"] > curr["ma30"]:
            return "V5-2", "MA10 crosses above MA20 with bullish alignment"

    return None, None


def detect_buy_signal(
    data: pd.DataFrame,
    i: Optional[int] = None,
    market_regime: MarketRegime = MarketRegime.UNKNOWN,
    config: StrategyConfig = StrategyConfig(),
) -> Dict[str, Any]:
    """Detect a buy signal at row ``i``.

    ``data`` may be raw OHLCV data or a dataframe already produced by
    :func:`add_indicators`.
    """

    has_indicators = {"ma5", "ma10", "ma20", "ma30", "high20", "trend"}.issubset(data.columns)
    frame = data.copy() if has_indicators else add_indicators(data)
    if i is None:
        i = len(frame) - 1
    if i < config.min_bars or i >= len(frame):
        return {"triggered": False, "signal": None, "reason": "insufficient bars"}

    curr = frame.iloc[i]
    if pd.isna(curr["trend"]) or float(curr["trend"]) < config.trend_threshold:
        return {
            "triggered": False,
            "signal": None,
            "reason": "trend filter failed",
            "trend": None if pd.isna(curr["trend"]) else float(curr["trend"]),
        }

    if market_regime == MarketRegime.BULL:
        signal, reason = buy_v9(frame, i)
    elif market_regime == MarketRegime.BEAR:
        signal, reason = buy_v5(frame, i)
    else:
        signal, reason = buy_v9(frame, i)
        if signal is None:
            signal, reason = buy_v5(frame, i)

    return {
        "triggered": signal is not None,
        "signal": signal,
        "reason": reason,
        "date": curr.get("date"),
        "close": float(curr["close"]),
        "trend": float(curr["trend"]),
        "market_regime": market_regime.value,
    }


def detect_sell_signal(
    data: pd.DataFrame,
    buy_price: float,
    buy_date: Optional[str] = None,
    highest_price: Optional[float] = None,
    config: StrategyConfig = StrategyConfig(),
) -> Dict[str, Any]:
    """Detect sell signal at the latest row.

    Returns a dictionary containing dead-cross and trailing-stop details.
    """

    frame = add_indicators(data)
    if len(frame) < config.min_bars:
        return {"triggered": False, "reason": "insufficient bars"}

    if buy_date:
        since_buy = frame[frame["date"] >= pd.to_datetime(buy_date)]
        if since_buy.empty:
            since_buy = frame
    else:
        since_buy = frame

    prev = frame.iloc[-2]
    curr = frame.iloc[-1]
    high_since_buy = float(highest_price) if highest_price is not None else float(since_buy["high"].max())
    stop_price = high_since_buy * config.trailing_stop_ratio
    dead_cross = prev["ma5"] >= prev["ma10"] and curr["ma5"] < curr["ma10"]
    trailing_stop = float(curr["low"]) <= stop_price

    reason = None
    if trailing_stop:
        reason = "trailing_stop"
    elif dead_cross:
        reason = "dead_cross"

    pnl_pct = (float(curr["close"]) - buy_price) / buy_price if buy_price else None
    return {
        "triggered": trailing_stop or dead_cross,
        "reason": reason,
        "date": curr.get("date"),
        "close": float(curr["close"]),
        "highest_price": high_since_buy,
        "stop_price": stop_price,
        "dead_cross": bool(dead_cross),
        "trailing_stop": bool(trailing_stop),
        "pnl_pct": pnl_pct,
    }
