# Contributing

Thanks for your interest in improving this project.

## Development setup

```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev,data]
```

## Pull request checklist

- Keep strategy logic deterministic and easy to review.
- Add or update tests for signal changes.
- Do not commit private trading records, account data, API keys, or notification tokens.
- Clearly state whether price data is adjusted or unadjusted.
- Document execution assumptions such as buy/sell price, slippage, fees, and rebalancing time.

## Data policy

Small synthetic sample CSV files may be committed under `examples/data/`. Large market datasets should not be committed; place them under `data/` or `ashare_data/`, both ignored by Git.
