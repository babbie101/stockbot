# codebase/data.py
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


CACHE_MAX_AGE = timedelta(hours=24)
OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
MIN_AVERAGE_DAILY_VOLUME = 500_000
MIN_CLOSE_PRICE = 5.0
ATR_WINDOW = 14
EXCLUDED_SECTORS = {"Financials"}
EXCLUDED_SUBINDUSTRIES = {
    "Aerospace & Defense",
    "Casinos & Gaming",
    "Distillers & Vintners",
    "Brewers",
    "Tobacco",
}


def get_clean_tickers() -> list[str]:
    """Return S&P 500 tickers after excluding selected industries."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    if not tables:
        raise ValueError("The S&P 500 constituents page did not contain any tables.")

    constituents = tables[0]
    required_columns = {"Symbol", "GICS Sector", "GICS Sub-Industry"}
    missing_columns = required_columns.difference(constituents.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"The S&P 500 table is missing required columns: {missing}")

    sectors = constituents["GICS Sector"].astype("string").str.strip().str.casefold()
    subindustries = (
        constituents["GICS Sub-Industry"].astype("string").str.strip().str.casefold()
    )
    excluded_sectors = {sector.casefold() for sector in EXCLUDED_SECTORS}
    excluded_subindustries = {
        industry.casefold() for industry in EXCLUDED_SUBINDUSTRIES
    }
    approved = constituents.loc[
        ~sectors.isin(excluded_sectors)
        & ~subindustries.isin(excluded_subindustries),
        "Symbol",
    ]

    tickers = approved.astype("string").str.strip().str.replace(".", "-", regex=False)
    return tickers.dropna().loc[lambda values: values != ""].drop_duplicates().tolist()


def fetch_and_cache_data(
    tickers: list[str],
    start_date: str,
    end_date: str,
    cache_dir: Path | str = Path("data_cache"),
) -> dict[str, pd.DataFrame]:
    """Download daily adjusted OHLCV data, reusing fresh per-ticker CSV caches."""
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start >= end:
        raise ValueError("start_date must be earlier than end_date.")

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    symbols = list(dict.fromkeys(tickers))
    cache_files = {
        symbol: cache_path
        / f"{symbol}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        for symbol in symbols
    }

    now = datetime.now().timestamp()
    frames = {}
    download_symbols = []
    for symbol, file_path in cache_files.items():
        if (
            file_path.exists()
            and now - file_path.stat().st_mtime < CACHE_MAX_AGE.total_seconds()
        ):
            frames[symbol] = pd.read_csv(file_path, index_col=0, parse_dates=True)
        else:
            download_symbols.append(symbol)

    if download_symbols:
        downloaded = yf.download(
            tickers=download_symbols,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=True,
            group_by="ticker",
            progress=False,
        )
        for symbol in download_symbols:
            if isinstance(downloaded.columns, pd.MultiIndex):
                ticker_level = next(
                    (
                        level
                        for level in range(downloaded.columns.nlevels)
                        if symbol in downloaded.columns.get_level_values(level)
                    ),
                    None,
                )
                if ticker_level is None:
                    raise ValueError(f"Downloaded data did not include {symbol}.")
                frame = downloaded.xs(symbol, axis=1, level=ticker_level)
                if isinstance(frame.columns, pd.MultiIndex):
                    frame.columns = frame.columns.get_level_values(-1)
            elif len(download_symbols) == 1:
                frame = downloaded
            else:
                raise ValueError(
                    "Expected ticker-labeled columns for a multi-stock download."
                )

            missing_columns = set(OHLCV_COLUMNS).difference(frame.columns)
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(f"Downloaded data for {symbol} is missing: {missing}")
            frame = frame[OHLCV_COLUMNS].copy()
            if frame.empty:
                raise ValueError(f"Downloaded data for {symbol} is empty.")

            frame.to_csv(cache_files[symbol], index=True)
            frames[symbol] = frame

    return {symbol: frames[symbol] for symbol in symbols}


def clean_stock_df(
    frame: pd.DataFrame,
    min_average_daily_volume: int = MIN_AVERAGE_DAILY_VOLUME,
    min_close_price: float = MIN_CLOSE_PRICE,
) -> pd.DataFrame:
    """Drop incomplete bars and filter illiquid or low-priced data."""
    missing_columns = set(OHLCV_COLUMNS).difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Stock data is missing required columns: {missing}")

    clean = frame.dropna(subset=OHLCV_COLUMNS).copy()
    if clean.empty or clean["Volume"].mean() < min_average_daily_volume:
        return clean.iloc[0:0]

    return clean.loc[clean["Close"] >= min_close_price]


def add_base_features(
    frame: pd.DataFrame,
    atr_window: int = ATR_WINDOW,
) -> pd.DataFrame:
    """Add daily percentage returns and average true range."""
    required_columns = {"High", "Low", "Close"}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Stock data is missing required columns: {missing}")
    if atr_window < 1:
        raise ValueError("atr_window must be at least 1.")

    featured = frame.copy()
    previous_close = featured["Close"].shift(1)
    true_range = pd.concat(
        [
            featured["High"] - featured["Low"],
            (featured["High"] - previous_close).abs(),
            (featured["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    featured["Daily_Return"] = featured["Close"].pct_change()
    featured["ATR"] = true_range.rolling(
        window=atr_window,
        min_periods=atr_window,
    ).mean()
    return featured.dropna(subset=["Daily_Return", "ATR"])


def load_market_data(
    start_date: str,
    end_date: str,
    cache_dir: Path | str = Path("data_cache"),
) -> dict[str, pd.DataFrame]:
    """Load, clean, and add features to the approved stock universe."""
    tickers = get_clean_tickers()
    downloaded = fetch_and_cache_data(
        tickers,
        start_date,
        end_date,
        cache_dir=cache_dir,
    )

    market_data = {}
    for symbol, frame in downloaded.items():
        clean = clean_stock_df(frame)
        if clean.empty:
            continue
        featured = add_base_features(clean)
        if not featured.empty:
            market_data[symbol] = featured

    if not market_data:
        raise ValueError("No usable market data remained after cleaning and feature calculation.")
    return market_data


def fetch_ticker(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """
    Return a DataFrame with daily close prices for `symbol`.
    Uses yfinance (free, no auth for public stocks).
    """
    df = yf.download(symbol, period=period, progress=False)
    if df.empty:
        return pd.DataFrame()
    # yfinance returns MultiIndex columns (Price, Ticker) — flatten to symbol name
    df.columns = df.columns.get_level_values(0)
    return df[["Close"]].rename(columns={"Close": symbol})
