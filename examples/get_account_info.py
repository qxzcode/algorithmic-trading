#!/usr/bin/env python3
"""
Fetch Alpaca account details & balances using the project's `Config`.

Usage:
  1) Copy `.env.example` to `.env` and set ALPACA_API_KEY and ALPACA_SECRET_KEY
     (and ALPACA_TRADING_MODE to 'paper' or 'live').
  2) Install dependencies: pip install alpaca-py python-dotenv
  3) Run: python examples/get_account_info.py

This script prints key account fields and the full account payload.
"""
from typing import Any, Mapping

from trading_framework.config import Config

try:
    # alpaca-py (v1.x) trading client
    from alpaca.trading.client import TradingClient
except Exception as exc:  # pragma: no cover - user will install dependency
    raise SystemExit(
        "Missing dependency 'alpaca-py'. Install with: pip install alpaca-py"
    ) from exc


def format_value(v: Any) -> str:
    if v is None:
        return "None"
    return str(v)


def main() -> None:
    # Load and validate config
    config = Config()
    if not config.validate():
        raise SystemExit("Invalid configuration. See error messages above.")

    paper = config.is_paper_trading()

    client = TradingClient(
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=paper,
    )

    print("Fetching account information...")
    acct = client.get_account()

    # Print important fields if available
    # Note: `acct` is usually a Pydantic model; use getattr to be safe
    print("\nAccount summary")
    print("-----------------")
    print("Account ID:", format_value(getattr(acct, "id", None)))
    print("Status:", format_value(getattr(acct, "status", None)))
    print("Cash:", format_value(getattr(acct, "cash", None)))
    print("Portfolio Value:", format_value(getattr(acct, "portfolio_value", None)))
    print("Equity:", format_value(getattr(acct, "equity", None)))
    print("Buying Power:", format_value(getattr(acct, "buying_power", None)))
    print("Day Trade Count:", format_value(getattr(acct, "daytrade_count", None)))

    # Print full account payload
    print("\nFull account payload")
    print("--------------------")
    try:
        # Pydantic models have .dict(); fall back to vars()
        payload: Mapping[str, Any] = acct.dict()
    except Exception:
        payload = vars(acct) if hasattr(acct, "__dict__") else {}

    for k, v in payload.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
