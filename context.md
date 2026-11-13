# Context & Plan — Codebase (Stock Trading Bot)

## 1. Project Overview
A minimal stock-trading-bot skeleton inside the `codebase/` directory of the repo `babbie101/stockbot.git`.
Currently empty except for a bare Git init; we're building from scratch (YAGNI).

### Folder layout (`codebase/`)
```
codebase/
├── __init__.py          # package marker
├── requirements.txt     # dependencies
├── app.py               # main entry point
├── data.py              # fetch prices via yfinance
├── strategy.py          # BUY/SELL/HOLD logic
└── test_bot.py          # smoke test
```

---

## 2. What We're Doing (Phase by Phase)

| Phase                            | Goal                                                    | Key File(s)                                      |
| -------------------------------- | ------------------------------------------------------- | ------------------------------------------------ |
| **0 – Setup**                    | Scaffold project skeleton, install deps                 | `__init__.py`, `requirements.txt`, `app.py` stub |
| **1 – Data fetching**            | Pull live/daily close prices for any ticker             | `data.py` → `fetch_ticker()`                     |
| **2 – Strategy engine**          | Simple rule-based signal (e.g., price up → BUY)         | `strategy.py` → `generate_signal()`              |
| **3 – Orchestration**            | Tie data + strategy into one runnable script            | `app.py` → `run_trade()`                         |
| **4 – Testing**                  | Verify pipeline runs without crashing                   | `test_bot.py`                                    |
| **5 – Risk / Broker** *(future)* | Add stop-loss, position sizing, real broker integration | TBD                                              |

---

## 3. Core Concepts You Need to Understand First

### A. Market Data Sources
- **`yfinance`** (free, public): Yahoo Finance CSV API → daily OHLCV. No API key needed for stocks like AAPL, TSLA.
- Alternatives later: Alpha Vantage, Polygon.io, IEX Cloud (paid).
- *Why:* Every bot needs raw price data. Start here before adding complexity.

### B. Technical Indicators (simple version)
- **Close price**: last day's closing price.
- **Previous close**: yesterday's close.
- **Signal**: `BUY` if today > yesterday, `SELL` if today < yesterday, else `HOLD`.
- Later we'll add moving averages, RSI, MACD — just math on the DataFrame above.

### C. Strategy Logic
- Rules can be as simple as "compare two days' closes".
- Real strategies use moving averages, trend lines, volume spikes, etc.
- Keep it readable first; upgrade with over-engineering checks later.

### D. Risk Management (to come)
- Position sizing (don't put all capital on one trade).
- Stop-loss / take-profit levels.
- Drawdown limits.
- *Not implemented yet* — flagged as future phase.

### E. Execution Layer
- WebSocket vs polling for real-time signals.
- Order types: market, limit, stop.
- For now: print the signal; wire up later.

---

## 4. How I Want to Learn Along the Way

### Step-by-step learning resources
1. **`yfinance` docs** — https://github.com/inversive/yfinance or PyPI page. Quickstart.
2. **`pandas` docs** — https://pandas.pydata.org/docs/. Focus on Series/DataFrame ops.
3. **Trading basics** — free articles: "How to backtest SMA crossover", blogs.
4. **Obsidian vault** — already set up. Use `.obsidian/graph.json` to visualize connections between notes/tags.
5. **Practice on paper first** — simulate trades in spreadsheet before touching a broker.

### My pace (lazy mode)
- **Day 1–2:** Install deps, run `data.py` for AAPL → see live prices.
- **Day 3–4:** Implement `strategy.py` → get BUY/SELL output.
- **Day 5:** Run `app.py` → confirm end-to-end flow.
- **Week 2:** Add basic risk (stop-loss) manually in `app.py`.
- **Later:** Swap to WebSocket, add real broker calls.

### When to ask me to add something
- "Add stop-loss after X"
- "Show me the moving average crossover"
- "Explain why I'm using pandas instead of numpy"

---

## 5. Immediate Next Steps (today / tomorrow)

1. **Install dependencies**
   ```bash
   pip install -r codebase/requirements.txt
   ```
2. **Run the smoke test**
   ```bash
   python codebase/test_bot.py
   ```
3. **If it works**, run `python codebase/app.py` to see the signal for AAPL.
4. **Then decide which ticker(s)** you actually want to watch.

---

## 6. Open Questions

- [ ] Which stock(s) will we track initially? (AAPL suggested)
- [ ] Do we need an API key for real-time data?
- [ ] Should we store signals in a CSV or database?
- [ ] Is there a specific learning resource you prefer?

---

*This file is living — update it as we progress.*
