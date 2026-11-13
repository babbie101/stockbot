"""Rule-based signal engine: compare today's close vs yesterday's close."""

from data import fetch_ticker


def generate_signal(symbol: str) -> str:
    """
    Return ``'BUY'`` if today's close > yesterday's close,
    ``'SELL'`` if today's close < yesterday's close,
    otherwise ``'HOLD'``.
    """
    ticker_df = fetch_ticker(symbol)
    if len(ticker_df) < 2:
        return "HOLD"
    latest = ticker_df.iloc[-1]
    previous = ticker_df.iloc[-2]
    if latest["Close"] > previous["Close"]:
        return "BUY"
    elif latest["Close"] < previous["Close"]:
        return "SELL"
    else:
        return "HOLD"
