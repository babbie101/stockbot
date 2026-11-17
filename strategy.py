import numpy as np
import pandas as pd

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:#used to tell if a stck is dropping or falling 
    data = df.copy()
    data["SMA_20"] = data["Close"].rolling(window=20).mean()#SMA = simple moving average good for medium time holds
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    return data.dropna()
    pass

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["Signal"] = (data["SMA_20"] > data["SMA_50"]) & (data["Close"] < data["Close"].shift(3))
    return data

def simulate_trades(df: pd.DataFrame, max_hold_days: int = 10) -> list[float]:
    trades = []
    in_trade = False
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    days_held = 0

    for _, row in df.iterrows():
        if not in_trade:
            if row["Signal"]:
                in_trade = True
                entry_price = row["Close"]
                stop_loss = entry_price - (2.0 * row["ATR"])
                take_profit = entry_price + (4.0 * row["ATR"])
                days_held = 0
        else:
            days_held += 1
            exit_price = None

            if row["Low"] <= stop_loss:
                exit_price = stop_loss
            elif row["High"] >= take_profit:
                exit_price = take_profit
            elif days_held >= max_hold_days:
                exit_price = row["Close"]

            if exit_price is not None:
                return_pct = (exit_price - entry_price) / entry_price
                trades.append(return_pct)
                in_trade = False

    return trades
#funcituon to simulate trades by going thought a stocks price and checks if our signal is true might need to change this 
#if i get a new api but testing
# also ahndlkes stop loss 