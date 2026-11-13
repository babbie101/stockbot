# codebase/data.py
import pandas as pd


def fetch_ticker(symbol: str, period: str = "6m") -> pd.DataFrame:
    """
    Return a DataFrame with daily close prices for `symbol`.
    Uses yfinance (free, no auth for public stocks).
    """
    url = f"https://query.yahoo-finance.com/api/v9/quote?symbol={symbol}&period={period}"
    df = pd.read_csv(url, parse_dates=['Date'])
    return df[["Close"]].rename(columns={"Close": symbol})
