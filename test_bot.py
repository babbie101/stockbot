"""Smoke tests for the trading bot pipeline."""

import pandas as pd

from data import (
    clean_stock_df,
    add_base_features,
    fetch_and_cache_data,
    fetch_ticker,
    get_clean_tickers,
    load_market_data,
)
from strategy import generate_signal


def test_fetch_and_cache_data_batches_download_and_reuses_csv_cache(
    monkeypatch, tmp_path
):
    tickers = ["AAA", "BBB"]
    columns = pd.MultiIndex.from_product(
        [tickers, ["Open", "High", "Low", "Close", "Volume"]]
    )
    downloaded = pd.DataFrame(
        [[10, 12, 9, 11, 1000, 20, 22, 19, 21, 2000]],
        index=pd.to_datetime(["2025-01-02"]),
        columns=columns,
    )
    calls = []

    def fake_download(**kwargs):
        calls.append(kwargs)
        return downloaded

    monkeypatch.setattr("data.yf.download", fake_download)

    first_result = fetch_and_cache_data(
        tickers, "2025-01-01", "2025-01-03", cache_dir=tmp_path
    )
    second_result = fetch_and_cache_data(
        tickers, "2025-01-01", "2025-01-03", cache_dir=tmp_path
    )

    assert len(calls) == 1
    assert calls[0]["auto_adjust"] is True
    assert calls[0]["interval"] == "1d"
    assert list(first_result) == tickers
    assert list(first_result["AAA"].columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    pd.testing.assert_frame_equal(first_result["AAA"], second_result["AAA"])
    assert len(list(tmp_path.glob("*.csv"))) == 2


def test_get_clean_tickers_filters_industries_and_normalizes_symbols(monkeypatch):
    constituents = pd.DataFrame(
        {
            "Symbol": ["AAPL", "XYZ.A", "BRK.B", "JPM", "LMT", "MO", "  MSFT  "],
            "GICS Sector": [
                "Information Technology",
                "Information Technology",
                "Financials",
                "Financials",
                "Industrials",
                "Consumer Staples",
                " Information Technology ",
            ],
            "GICS Sub-Industry": [
                "Technology Hardware",
                "Technology Hardware",
                "Insurance",
                "Banks",
                "Aerospace & Defense",
                "Tobacco",
                "Systems Software",
            ],
        }
    )
    monkeypatch.setattr("data.pd.read_html", lambda _url: [constituents])

    assert get_clean_tickers() == ["AAPL", "XYZ-A", "MSFT"]


def test_clean_stock_df_drops_incomplete_and_low_price_rows():
    frame = pd.DataFrame(
        {
            "Open": [10.0, 4.5, 8.0],
            "High": [11.0, 5.0, None],
            "Low": [9.0, 4.0, 7.0],
            "Close": [10.5, 4.8, 8.5],
            "Volume": [600_000, 600_000, 900_000],
        },
        index=pd.date_range("2025-01-01", periods=3),
    )

    clean = clean_stock_df(frame)

    assert clean.index.tolist() == [pd.Timestamp("2025-01-01")]
    assert frame["High"].isna().sum() == 1


def test_clean_stock_df_rejects_below_threshold_average_volume():
    frame = pd.DataFrame(
        {
            "Open": [10.0, 10.0],
            "High": [11.0, 11.0],
            "Low": [9.0, 9.0],
            "Close": [10.5, 10.5],
            "Volume": [300_000, 400_000],
        }
    )

    assert clean_stock_df(frame).empty


def test_add_base_features_calculates_returns_and_atr():
    index = pd.date_range("2025-01-01", periods=15)
    close = pd.Series(range(10, 25), index=index, dtype=float)
    frame = pd.DataFrame(
        {
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 600_000,
        },
        index=index,
    )

    featured = add_base_features(frame)

    assert len(featured) == 2
    assert featured.index[0] == index[13]
    assert featured.index[-1] == index[-1]
    assert abs(featured.loc[index[-1], "Daily_Return"] - (1 / 23)) < 1e-12
    assert featured.loc[index[-1], "ATR"] == 2
    assert "Daily_Return" not in frame.columns


def test_load_market_data_returns_clean_featured_frames(monkeypatch, tmp_path):
    index = pd.date_range("2025-01-01", periods=20)
    close = pd.Series(range(10, 30), index=index, dtype=float)
    good_frame = pd.DataFrame(
        {
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 600_000,
        },
        index=index,
    )
    low_volume_frame = good_frame.assign(Volume=100_000)
    monkeypatch.setattr("data.get_clean_tickers", lambda: ["AAA", "LOW"])
    monkeypatch.setattr(
        "data.fetch_and_cache_data",
        lambda *_args, **_kwargs: {"AAA": good_frame, "LOW": low_volume_frame},
    )

    result = load_market_data("2025-01-01", "2025-01-21", cache_dir=tmp_path)

    assert list(result) == ["AAA"]
    assert {"Open", "High", "Low", "Close", "Volume", "Daily_Return", "ATR"} <= set(
        result["AAA"].columns
    )
    assert not result["AAA"].isna().any().any()


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
