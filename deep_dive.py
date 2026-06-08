import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

METRIC_EXPLAINERS = {
    "P/E Ratio": "Price-to-Earnings. How much you pay for $1 of profit. Market avg ~20x. High = expensive/fast-growing. Low = cheap or struggling.",
    "Forward P/E": "Same as P/E but uses next year's expected earnings. Lower than trailing P/E = analysts expect profit to grow.",
    "P/B Ratio": "Price-to-Book. Share price vs accounting value of assets. Below 1 = trading below asset value (rare bargain or distress signal).",
    "EV/EBITDA": "Enterprise Value vs earnings before interest, tax, depreciation, amortisation. The go-to multiple in M&A and consulting. <10x = cheap, >20x = expensive.",
    "Gross Margin": "Revenue minus cost of goods, as a %. Shows pricing power. Software is 60-80%+. Retail is 20-30%. Higher = better business model.",
    "Operating Margin": "Profit after running costs, as a %. What's left after paying employees and rent. Consultants use this to benchmark efficiency.",
    "Net Margin": "Final profit as a % of revenue after everything including tax. The bottom line. Varies hugely by industry.",
    "ROE": "Return on Equity. Profit as a % of shareholders' equity. Measures how efficiently management uses investor money. >15% is generally strong.",
    "ROA": "Return on Assets. Profit as a % of total assets. Useful for comparing capital-heavy industries like banks and manufacturing.",
    "Debt/Equity": "Total debt divided by shareholders' equity. High = leveraged/risky. >2x warrants scrutiny. Some industries (utilities, banks) run higher normally.",
    "Revenue Growth": "Year-over-year revenue increase. The top-line growth rate. Consulting cases often start here to size the opportunity.",
    "Current Ratio": "Current assets / current liabilities. Measures short-term liquidity. <1 = potential cash crunch. >2 = very safe.",
    "Free Cash Flow": "Cash left after capital expenditures. More reliable than net income — harder to manipulate. Warren Buffett's favourite metric.",
}


def _get_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


def _get_news(ticker: str) -> list[dict]:
    try:
        t = yf.Ticker(ticker)
        news = t.news or []
        return news[:8]
    except Exception:
        return []


def _fmt(val, prefix="", suffix="", decimals=2, billions=False):
    if val is None or (isinstance(val, float) and (val != val)):
        return "—"
    if billions and abs(val) >= 1e9:
        return f"{prefix}{val/1e9:.1f}B{suffix}"
    if billions and abs(val) >= 1e6:
        return f"{prefix}{val/1e6:.1f}M{suffix}"
    return f"{prefix}{val:.{decimals}f}{suffix}"


def render_deep_dive():
    st.markdown("#### 🏢 Company Deep Dive")
    st.caption("Full fundamentals, valuation multiples, and latest news — the stuff consultants actually look at.")

    ticker_input = st.text_input("Enter a ticker", placeholder="e.g. AAPL, MSFT, TSLA").strip().upper()
    if not ticker_input:
        st.markdown("""
        <div style="text-align:center;padding:50px 0;color:#555;">
            <div style="font-size:36px;">🔎</div>
            <div style="font-size:16px;margin-top:8px;">Enter a ticker above to see the full picture</div>
        </div>
        """, unsafe_allow_html=True)
        return

    with st.spinner(f"Loading {ticker_input}…"):
        info = _get_info(ticker_input)
        news = _get_news(ticker_input)

    if not info:
        st.error(f"Could not find data for {ticker_input}. Check the ticker symbol.")
        return

    name = info.get("longName") or info.get("shortName") or ticker_input
    sector = info.get("sector", "—")
    industry = info.get("industry", "—")
    country = info.get("country", "—")
    summary = info.get("longBusinessSummary", "")
    website = info.get("website", "")
    mktcap = info.get("marketCap")
    employees = info.get("fullTimeEmployees")

    # Header
    st.markdown(f"""
    <div style="background:#1e1e2e;border-radius:12px;padding:20px 24px;margin-bottom:16px;">
        <div style="font-size:22px;font-weight:800;color:#fff;">{name} <span style="color:#888;font-size:16px;font-weight:400;">({ticker_input})</span></div>
        <div style="display:flex;gap:16px;margin-top:8px;flex-wrap:wrap;">
            <span style="color:#888;font-size:13px;">📂 {sector} · {industry}</span>
            <span style="color:#888;font-size:13px;">🌍 {country}</span>
            {'<span style="color:#888;font-size:13px;">🏢 ' + f"{employees:,} employees</span>" if employees else ""}
            {'<span style="color:#888;font-size:13px;">🔗 <a href="' + website + '" style="color:#7c3aed">' + website.replace("https://","").replace("http://","") + '</a></span>' if website else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if summary:
        with st.expander("About the company"):
            st.write(summary)

    # Key stats row
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev = info.get("previousClose")
    pct = ((price - prev) / prev * 100) if price and prev else None
    high52 = info.get("fiftyTwoWeekHigh")
    low52 = info.get("fiftyTwoWeekLow")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", _fmt(price, "$"), f"{pct:+.2f}%" if pct else None)
    c2.metric("Market Cap", _fmt(mktcap, "$", billions=True))
    c3.metric("52W High", _fmt(high52, "$"))
    c4.metric("52W Low", _fmt(low52, "$"))

    st.divider()

    tab_val, tab_fin, tab_news = st.tabs(["📊 Valuation", "💵 Financials", "📰 News"])

    with tab_val:
        st.caption("Valuation multiples — how the market prices this company vs its fundamentals.")
        metrics = [
            ("P/E Ratio",      info.get("trailingPE"),         "", "x"),
            ("Forward P/E",    info.get("forwardPE"),          "", "x"),
            ("P/B Ratio",      info.get("priceToBook"),        "", "x"),
            ("EV/EBITDA",      info.get("enterpriseToEbitda"), "", "x"),
        ]
        cols = st.columns(4)
        for col, (label, val, pre, suf) in zip(cols, metrics):
            col.metric(label, _fmt(val, pre, suf))

        st.markdown("")
        for label, val, pre, suf in metrics:
            if val is not None:
                with st.expander(f"What does {label} mean?"):
                    st.write(METRIC_EXPLAINERS.get(label, ""))

    with tab_fin:
        st.caption("Operating performance — how efficiently the company runs its business.")
        fin_metrics = [
            ("Revenue",         info.get("totalRevenue"),               "$", "", True),
            ("Gross Margin",    (info.get("grossMargins") or 0) * 100,  "", "%", False),
            ("Operating Margin",(info.get("operatingMargins") or 0)*100,"", "%", False),
            ("Net Margin",      (info.get("profitMargins") or 0) * 100, "", "%", False),
            ("ROE",             (info.get("returnOnEquity") or 0) * 100,"", "%", False),
            ("ROA",             (info.get("returnOnAssets") or 0) * 100,"", "%", False),
            ("Debt/Equity",     info.get("debtToEquity"),               "", "x", False),
            ("Free Cash Flow",  info.get("freeCashflow"),               "$", "", True),
        ]

        r1 = st.columns(4)
        r2 = st.columns(4)
        for col, (label, val, pre, suf, bil) in zip(r1 + r2, fin_metrics):
            if bil:
                col.metric(label, _fmt(val, pre, billions=True))
            else:
                col.metric(label, _fmt(val, pre, suf))

        st.markdown("")
        for label, val, *_ in fin_metrics:
            if label in METRIC_EXPLAINERS:
                with st.expander(f"What does {label} mean?"):
                    st.write(METRIC_EXPLAINERS[label])

    with tab_news:
        if not news:
            st.info("No recent news found.")
        else:
            for item in news:
                title = item.get("title", "")
                link = item.get("link", "#")
                publisher = item.get("publisher", "")
                ts = item.get("providerPublishTime")
                import datetime
                time_str = datetime.datetime.fromtimestamp(ts).strftime("%b %d, %H:%M") if ts else ""
                st.markdown(f"""
                <div style="background:#1e1e2e;border-radius:8px;padding:12px 16px;margin-bottom:8px;border-left:3px solid #7c3aed;">
                    <a href="{link}" target="_blank" style="color:#fff;font-size:14px;font-weight:600;text-decoration:none;">{title}</a>
                    <div style="color:#666;font-size:11px;margin-top:4px;">{publisher} · {time_str}</div>
                </div>
                """, unsafe_allow_html=True)


# ── Macro tickers ─────────────────────────────────────────────────────────────
MACRO_TICKERS = {
    "^TNX":  ("10Y Treasury Yield", "%", "The interest rate on 10-year US government bonds. The benchmark for mortgages, corporate loans, and stock valuations. Rising = tightening."),
    "^IRX":  ("3M Treasury Yield",  "%", "Short-term borrowing cost. When this exceeds the 10Y yield, the curve 'inverts' — historically a recession signal."),
    "^VIX":  ("VIX Fear Index",     "",  "The market's 'fear gauge'. Measures expected S&P 500 volatility. Below 20 = calm. 20-30 = nervous. Above 30 = fear/panic."),
    "DX-Y.NYB": ("US Dollar Index", "",  "Tracks the dollar vs a basket of currencies. Strong dollar = bad for US exports and emerging markets. Often moves opposite to stocks."),
    "GC=F":  ("Gold Futures",       "$", "Gold rises when investors are fearful or expect inflation. A classic 'safe haven' asset."),
    "CL=F":  ("Crude Oil (WTI)",    "$", "US oil price. Drives inflation and consumer spending. High oil = higher prices for everything."),
}


def render_macro():
    st.markdown("#### 🌍 Macro Dashboard")
    st.caption("The big-picture numbers that drive markets — the backdrop every analyst needs to know.")

    if st.button("🔄 Refresh", key="macro_refresh"):
        st.session_state.pop("macro_data", None)

    if "macro_data" not in st.session_state:
        with st.spinner("Loading macro data…"):
            rows = {}
            for sym, (label, unit, _) in MACRO_TICKERS.items():
                try:
                    t = yf.Ticker(sym)
                    fi = t.fast_info
                    price = float(fi.last_price)
                    prev = float(fi.previous_close)
                    chg = price - prev
                    pct = chg / prev * 100 if prev else 0
                    rows[sym] = {"label": label, "unit": unit, "price": price, "chg": chg, "pct": pct}
                except Exception:
                    rows[sym] = {"label": label, "unit": unit, "price": None, "chg": None, "pct": None}
            st.session_state["macro_data"] = rows

    rows = st.session_state["macro_data"]

    cols = st.columns(3)
    for i, (sym, data) in enumerate(rows.items()):
        price = data["price"]
        pct = data["pct"]
        unit = data["unit"]
        label = data["label"]
        _, explainer = list(MACRO_TICKERS.items())[i][1][1], list(MACRO_TICKERS.items())[i][1][2]

        val_str = f"{unit}{price:.2f}" if price else "—"
        delta_str = f"{pct:+.2f}%" if pct is not None else None

        with cols[i % 3]:
            st.metric(label, val_str, delta_str)

    st.divider()
    st.markdown("**What do these mean?**")
    exp_cols = st.columns(2)
    for i, (sym, (label, unit, explainer)) in enumerate(MACRO_TICKERS.items()):
        with exp_cols[i % 2]:
            with st.expander(label):
                st.write(explainer)

    # Yield curve visual
    st.divider()
    st.markdown("**Yield Curve**")
    st.caption("When short-term rates exceed long-term rates (inverted), it historically predicts a recession within 12–18 months.")
    curve_tickers = {"3M": "^IRX", "2Y": "^TYX", "10Y": "^TNX", "30Y": "^TYX"}
    curve_tickers = [("3M","^IRX"),("2Y","^FVX"),("10Y","^TNX"),("30Y","^TYX")]
    curve_vals = []
    for label, sym in curve_tickers:
        try:
            val = float(yf.Ticker(sym).fast_info.last_price)
            curve_vals.append((label, val))
        except Exception:
            pass
    if curve_vals:
        labels, vals = zip(*curve_vals)
        color = "#ef4444" if vals[0] > vals[-1] else "#22c55e"
        fig = go.Figure(go.Scatter(
            x=list(labels), y=list(vals), mode="lines+markers",
            line=dict(color=color, width=2), marker=dict(size=8)
        ))
        fig.update_layout(
            template="plotly_dark", height=220,
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="Yield %",
        )
        st.plotly_chart(fig, use_container_width=True)
        if vals[0] > vals[-1]:
            st.warning("⚠️ Yield curve is currently inverted — short-term rates exceed long-term rates. Historically a recession signal.")
        else:
            st.success("✅ Yield curve is normal — long-term rates exceed short-term rates.")
