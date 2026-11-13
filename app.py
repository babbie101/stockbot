#!/usr/bin/env python3
"""Main entry point for the stock trading bot."""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data import fetch_ticker  # noqa: E402

def run_trade(symbol: str = "AAPL") -> None:
    """Fetch live prices and print the generated signal for *symbol*."""
    ticker_df = fetch_ticker(symbol)
    if ticker_df.empty:
        print(f"No data found for {symbol}.")
        return
    signal = generate_signal(symbol)
    print(f"{symbol}: latest close={ticker_df.iloc[-1]['Close']}, "
          f"previous close={ticker_df.iloc[-2]['Close'] if len(ticker_df) >= 2 else 'N/A'}, "
          f"signal={signal}")


if __name__ == "__main__":
    run_trade()
