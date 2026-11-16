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