"""Stock trading bot package."""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .data import fetch_ticker
from .strategy import generate_signal
from .app import run_trade

__all__ = ["fetch_ticker", "generate_signal", "run_trade"]
