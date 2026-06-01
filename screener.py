import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_TICKERS = [
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "AVGO",
    # Financials
    "JPM", "BAC", "GS", "MS", "V", "MA", "AXP",
    # Healthcare
    "UNH", "JNJ", "LLY", "ABBV", "MRK",
    # Energy
    "XOM", "CVX", "COP",
    # Consumer
    "WMT", "COST", "HD", "NKE", "MCD",
    # ETFs
    "SPY", "QQQ", "IWM", "ARKK", "XLF", "XLE", "XLK",
    # High-momentum names traders watch
    "AMD", "PLTR", "SOFI", "MSTR", "COIN", "RBLX", "HOOD", "GME", "AMC",
    # Semis
    "MU", "INTC", "QCOM", "TSM", "AMAT", "LRCX",
]


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
    avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _fetch_one(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        hist = t.fast_info
        df = t.history(period="60d", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 14:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        close = float(last["Close"])
        prev_close = float(prev["Close"])
        pct_change = (close - prev_close) / prev_close * 100

        volume = float(last["Volume"])
        avg_volume = float(df["Volume"].iloc[-20:].mean())
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0

        rsi_series = _rsi(df["Close"])
        rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else None

        try:
            week52_high = float(hist.fifty_two_week_high)
            week52_low = float(hist.fifty_two_week_low)
            pct_from_high = (close - week52_high) / week52_high * 100
        except Exception:
            week52_high = week52_low = pct_from_high = None

        market_cap = None
        try:
            market_cap = hist.market_cap
        except Exception:
            pass

        return {
            "Ticker": ticker,
            "Price": round(close, 2),
            "% Change": round(pct_change, 2),
            "Volume": int(volume),
            "Vol / Avg": round(volume_ratio, 2),
            "RSI (14)": round(rsi, 1) if rsi is not None and not np.isnan(rsi) else None,
            "52W High": round(week52_high, 2) if week52_high else None,
            "52W Low": round(week52_low, 2) if week52_low else None,
            "% from High": round(pct_from_high, 1) if pct_from_high is not None else None,
            "Mkt Cap ($B)": round(market_cap / 1e9, 1) if market_cap else None,
        }
    except Exception:
        return None


def fetch_screen(tickers: list[str], max_workers: int = 12) -> pd.DataFrame:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_one, t): t for t in tickers}
        for f in as_completed(futures):
            row = f.result()
            if row:
                results.append(row)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df.sort_values("% Change", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def fetch_chart_data(ticker: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        return df
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    df["EMA9"] = _ema(df["Close"], 9)
    df["EMA20"] = _ema(df["Close"], 20)
    df["RSI"] = _rsi(df["Close"])
    return df
