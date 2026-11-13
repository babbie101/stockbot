"""Smoke tests for the trading bot pipeline."""

import pandas as pd

from data import fetch_ticker
from strategy import generate_signal


def test_fetch_ticker_returns_dataframe():
    result = fetch_ticker("AAPL")
    assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"


def test_generate_signal_buy():
    signal = generate_signal("AAPL")
    assert signal == "BUY"


def test_generate_signal_sell():
    signal = generate_signal("TSLA")
    assert signal == "SELL"


def test_generate_signal_hold():
    signal = generate_signal("MSFT")
    assert signal == "HOLD"
