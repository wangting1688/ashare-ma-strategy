"""Command line interface for the strategy toolkit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .backtest import run_backtest
from .signals import MarketRegime, add_indicators, detect_buy_signal, detect_sell_signal, infer_market_regime


def _regime(value: str) -> MarketRegime:
    normalized = value.lower()
    if normalized in {"bull", "v9", "牛市"}:
        return MarketRegime.BULL
    if normalized in {"bear", "v5", "熊市"}:
        return MarketRegime.BEAR
    return MarketRegime.UNKNOWN


def cmd_signal(args: argparse.Namespace) -> None:
    stock_df = pd.read_csv(args.stock)
    regime = _regime(args.regime)
    if args.index:
        regime = infer_market_regime(pd.read_csv(args.index))
    result = detect_buy_signal(stock_df, market_regime=regime)
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))


def cmd_sell(args: argparse.Namespace) -> None:
    stock_df = pd.read_csv(args.stock)
    result = detect_sell_signal(stock_df, buy_price=args.buy_price, buy_date=args.buy_date)
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))


def cmd_backtest(args: argparse.Namespace) -> None:
    stock_df = pd.read_csv(args.stock)
    result = run_backtest(stock_df, market_regime=_regime(args.regime), code=args.code)
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A-share V9/V5 moving-average strategy toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_signal = subparsers.add_parser("signal", help="check latest buy signal")
    p_signal.add_argument("--stock", required=True, help="stock OHLCV CSV file")
    p_signal.add_argument("--index", help="Shanghai Composite OHLCV CSV file, optional")
    p_signal.add_argument("--regime", default="unknown", help="bull/bear/unknown")
    p_signal.set_defaults(func=cmd_signal)

    p_sell = subparsers.add_parser("sell", help="check latest sell signal")
    p_sell.add_argument("--stock", required=True, help="stock OHLCV CSV file")
    p_sell.add_argument("--buy-price", required=True, type=float)
    p_sell.add_argument("--buy-date", help="YYYY-MM-DD, optional")
    p_sell.set_defaults(func=cmd_sell)

    p_backtest = subparsers.add_parser("backtest", help="run single-symbol backtest")
    p_backtest.add_argument("--stock", required=True, help="stock OHLCV CSV file")
    p_backtest.add_argument("--code", default="UNKNOWN")
    p_backtest.add_argument("--regime", default="unknown", help="bull/bear/unknown")
    p_backtest.add_argument("--output", help="write full result JSON")
    p_backtest.set_defaults(func=cmd_backtest)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
