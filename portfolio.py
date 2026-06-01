import json
from pathlib import Path

import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

PORTFOLIO_FILE = Path("portfolio.json")


def load_positions() -> list[dict]:
    if not PORTFOLIO_FILE.exists():
        return []
    return json.loads(PORTFOLIO_FILE.read_text())


def save_positions(positions: list[dict]) -> None:
    PORTFOLIO_FILE.write_text(json.dumps(positions, indent=2))


def _fetch_price(ticker: str) -> tuple[str, float | None, float | None]:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = float(info.last_price)
        prev_close = float(info.previous_close)
        return ticker, price, prev_close
    except Exception:
        return ticker, None, None


def enrich_portfolio(positions: list[dict]) -> pd.DataFrame:
    if not positions:
        return pd.DataFrame()

    tickers = list({p["ticker"] for p in positions})
    price_map: dict[str, tuple[float | None, float | None]] = {}

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_price, t): t for t in tickers}
        for f in as_completed(futures):
            ticker, price, prev_close = f.result()
            price_map[ticker] = (price, prev_close)

    rows = []
    for p in positions:
        ticker = p["ticker"]
        shares = float(p["shares"])
        cost_basis = float(p["cost_basis"])  # per share

        price, prev_close = price_map.get(ticker, (None, None))

        total_cost = shares * cost_basis
        market_value = shares * price if price else None
        unrealized_pl = market_value - total_cost if market_value is not None else None
        unrealized_pct = unrealized_pl / total_cost * 100 if total_cost and unrealized_pl is not None else None

        day_pl = shares * (price - prev_close) if price and prev_close else None
        day_pct = (price - prev_close) / prev_close * 100 if price and prev_close else None

        rows.append({
            "Ticker": ticker,
            "Shares": shares,
            "Avg Cost": cost_basis,
            "Last Price": round(price, 2) if price else None,
            "Mkt Value": round(market_value, 2) if market_value else None,
            "Total Cost": round(total_cost, 2),
            "Unrealized P&L": round(unrealized_pl, 2) if unrealized_pl is not None else None,
            "Unrealized %": round(unrealized_pct, 2) if unrealized_pct is not None else None,
            "Day P&L": round(day_pl, 2) if day_pl is not None else None,
            "Day %": round(day_pct, 2) if day_pct else None,
        })

    df = pd.DataFrame(rows)
    df.sort_values("Mkt Value", ascending=False, inplace=True, na_position="last")
    df.reset_index(drop=True, inplace=True)
    return df
