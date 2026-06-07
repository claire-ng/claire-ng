import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from screener import DEFAULT_TICKERS, fetch_screen, fetch_chart_data
from portfolio import load_positions, save_positions, enrich_portfolio

st.set_page_config(
    page_title="Day Trading Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Day Trading Dashboard")
st.caption("Data via Yahoo Finance · prices delayed ~15 min")

tab_screen, tab_portfolio = st.tabs(["Stock Screener", "Portfolio"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCREENER
# ═══════════════════════════════════════════════════════════════════════════════
with tab_screen:
    with st.sidebar:
        st.header("Screener Filters")

        pct_min, pct_max = st.slider(
            "% Change today",
            min_value=-20.0, max_value=20.0,
            value=(-20.0, 20.0), step=0.5,
        )
        vol_ratio_min = st.slider(
            "Min volume / 20-day avg",
            min_value=0.0, max_value=10.0,
            value=0.0, step=0.1,
        )
        rsi_min, rsi_max = st.slider(
            "RSI range", min_value=0, max_value=100, value=(0, 100),
        )

        st.divider()
        st.subheader("Watchlist")
        custom_raw = st.text_area(
            "Tickers (comma-separated)",
            value=", ".join(DEFAULT_TICKERS),
            height=150,
        )
        custom_tickers = [t.strip().upper() for t in custom_raw.split(",") if t.strip()]
        run = st.button("Run Screen", type="primary", use_container_width=True)

    if "df" not in st.session_state:
        st.session_state["df"] = pd.DataFrame()

    if run:
        with st.spinner(f"Fetching data for {len(custom_tickers)} tickers…"):
            st.session_state["df"] = fetch_screen(custom_tickers)

    df: pd.DataFrame = st.session_state["df"]

    if df.empty:
        st.info("Click **Run Screen** in the sidebar to fetch data.")
    else:
        mask = (
            df["% Change"].between(pct_min, pct_max)
            & (df["Vol / Avg"] >= vol_ratio_min)
        )
        if "RSI (14)" in df.columns:
            rsi_mask = df["RSI (14)"].isna() | df["RSI (14)"].between(rsi_min, rsi_max)
            mask &= rsi_mask

        filtered = df[mask].copy()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Showing", f"{len(filtered)} / {len(df)}")
        if not filtered.empty:
            gainers = (filtered["% Change"] > 0).sum()
            losers = (filtered["% Change"] < 0).sum()
            c2.metric("Gainers", gainers)
            c3.metric("Losers", losers)
            avg_rsi = filtered["RSI (14)"].mean()
            c4.metric("Avg RSI", f"{avg_rsi:.1f}" if pd.notna(avg_rsi) else "—")

        st.divider()

        def colour_pct(val):
            if pd.isna(val):
                return ""
            return "color: #22c55e" if val > 0 else ("color: #ef4444" if val < 0 else "")

        def colour_rsi(val):
            if pd.isna(val):
                return ""
            if val >= 70:
                return "color: #ef4444; font-weight:bold"
            if val <= 30:
                return "color: #22c55e; font-weight:bold"
            return ""

        styled = (
            filtered.style
            .map(colour_pct, subset=["% Change", "% from High"])
            .map(colour_rsi, subset=["RSI (14)"])
            .format({
                "Price": "${:.2f}",
                "% Change": "{:+.2f}%",
                "Vol / Avg": "{:.2f}x",
                "RSI (14)": "{:.1f}",
                "% from High": "{:+.1f}%",
                "Mkt Cap ($B)": "${:.1f}B",
            }, na_rep="—")
        )
        st.dataframe(styled, use_container_width=True, height=400)

        st.divider()
        st.subheader("Chart")
        col_l, col_r = st.columns([1, 3])
        with col_l:
            ticker_choice = st.selectbox("Pick a ticker", options=filtered["Ticker"].tolist())
            chart_period = st.radio("Period", ["1d", "5d", "1mo"], index=1, horizontal=True)
            interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d"}

        with col_r:
            if ticker_choice:
                with st.spinner(f"Loading {ticker_choice} chart…"):
                    cdf = fetch_chart_data(ticker_choice, period=chart_period,
                                           interval=interval_map[chart_period])
                if cdf.empty:
                    st.warning("No chart data available.")
                else:
                    fig = make_subplots(
                        rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.55, 0.25, 0.20], vertical_spacing=0.03,
                    )
                    fig.add_trace(go.Candlestick(
                        x=cdf.index, open=cdf["Open"], high=cdf["High"],
                        low=cdf["Low"], close=cdf["Close"], name="Price",
                        increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
                    ), row=1, col=1)
                    if "EMA9" in cdf:
                        fig.add_trace(go.Scatter(x=cdf.index, y=cdf["EMA9"], name="EMA9",
                                                  line=dict(color="#facc15", width=1)), row=1, col=1)
                    if "EMA20" in cdf:
                        fig.add_trace(go.Scatter(x=cdf.index, y=cdf["EMA20"], name="EMA20",
                                                  line=dict(color="#818cf8", width=1)), row=1, col=1)
                    colors = ["#22c55e" if c >= o else "#ef4444"
                              for c, o in zip(cdf["Close"], cdf["Open"])]
                    fig.add_trace(go.Bar(x=cdf.index, y=cdf["Volume"], name="Volume",
                                          marker_color=colors, showlegend=False), row=2, col=1)
                    if "RSI" in cdf:
                        fig.add_trace(go.Scatter(x=cdf.index, y=cdf["RSI"], name="RSI",
                                                  line=dict(color="#a78bfa", width=1.5)), row=3, col=1)
                        fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=3, col=1)
                        fig.add_hline(y=30, line_dash="dot", line_color="#22c55e", row=3, col=1)
                    fig.update_layout(
                        template="plotly_dark", title=f"{ticker_choice} · {chart_period}",
                        xaxis_rangeslider_visible=False,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        height=560, margin=dict(l=0, r=0, t=40, b=0),
                    )
                    fig.update_yaxes(title_text="Price", row=1, col=1)
                    fig.update_yaxes(title_text="Vol", row=2, col=1)
                    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
                    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PORTFOLIO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_portfolio:
    st.subheader("My Portfolio")
    st.caption("Enter your positions manually (mirrors your Chase self-directed account).")

    positions = load_positions()

    # ── Add / edit positions ──────────────────────────────────────────────────
    with st.expander("➕ Add / Edit Position", expanded=len(positions) == 0):
        with st.form("add_position"):
            fc1, fc2, fc3 = st.columns(3)
            new_ticker = fc1.text_input("Ticker", placeholder="e.g. AAPL").strip().upper()
            new_shares = fc2.number_input("Shares", min_value=0.001, step=0.001, format="%.3f")
            new_cost = fc3.number_input("Avg Cost per Share ($)", min_value=0.01, step=0.01, format="%.2f")

            submitted = st.form_submit_button("Save Position", type="primary")
            if submitted and new_ticker:
                existing = next((p for p in positions if p["ticker"] == new_ticker), None)
                if existing:
                    existing["shares"] = new_shares
                    existing["cost_basis"] = new_cost
                    st.success(f"Updated {new_ticker}")
                else:
                    positions.append({"ticker": new_ticker, "shares": new_shares, "cost_basis": new_cost})
                    st.success(f"Added {new_ticker}")
                save_positions(positions)
                st.rerun()

    # ── Remove a position ─────────────────────────────────────────────────────
    if positions:
        remove_ticker = st.selectbox(
            "Remove a position",
            options=["—"] + [p["ticker"] for p in positions],
        )
        if remove_ticker != "—":
            if st.button(f"Remove {remove_ticker}", type="secondary"):
                positions = [p for p in positions if p["ticker"] != remove_ticker]
                save_positions(positions)
                st.rerun()

    st.divider()

    # ── Live P&L table ────────────────────────────────────────────────────────
    if not positions:
        st.info("No positions yet. Add some above.")
        st.stop()

    if st.button("Refresh Prices", type="primary"):
        with st.spinner("Fetching live prices…"):
            pdf = enrich_portfolio(positions)
        st.session_state["pdf"] = pdf
    elif "pdf" not in st.session_state:
        with st.spinner("Fetching live prices…"):
            pdf = enrich_portfolio(positions)
        st.session_state["pdf"] = pdf

    pdf: pd.DataFrame = st.session_state["pdf"]

    if pdf.empty:
        st.warning("Could not fetch prices.")
        st.stop()

    # Summary metrics
    total_value = pdf["Mkt Value"].sum()
    total_cost = pdf["Total Cost"].sum()
    total_upl = pdf["Unrealized P&L"].sum()
    total_day = pdf["Day P&L"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"${total_value:,.2f}")
    m2.metric("Total Cost Basis", f"${total_cost:,.2f}")
    m3.metric(
        "Unrealized P&L",
        f"${total_upl:,.2f}",
        delta=f"{total_upl / total_cost * 100:+.2f}%" if total_cost else None,
    )
    m4.metric(
        "Today's P&L",
        f"${total_day:,.2f}",
        delta=f"{total_day / (total_value - total_day) * 100:+.2f}%" if total_value else None,
    )

    st.divider()

    def colour_pl(val):
        if pd.isna(val):
            return ""
        return "color: #22c55e" if val > 0 else ("color: #ef4444" if val < 0 else "")

    pdf_styled = (
        pdf.style
        .map(colour_pl, subset=["Unrealized P&L", "Unrealized %", "Day P&L", "Day %"])
        .format({
            "Shares": "{:.3f}",
            "Avg Cost": "${:.2f}",
            "Last Price": "${:.2f}",
            "Mkt Value": "${:,.2f}",
            "Total Cost": "${:,.2f}",
            "Unrealized P&L": "${:+,.2f}",
            "Unrealized %": "{:+.2f}%",
            "Day P&L": "${:+,.2f}",
            "Day %": "{:+.2f}%",
        }, na_rep="—")
    )
    st.dataframe(pdf_styled, use_container_width=True)

    st.divider()

    # ── Allocation pie ────────────────────────────────────────────────────────
    st.subheader("Allocation")
    pie = px.pie(
        pdf.dropna(subset=["Mkt Value"]),
        names="Ticker",
        values="Mkt Value",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.4,
    )
    pie.update_layout(template="plotly_dark", height=360, margin=dict(t=20))
    st.plotly_chart(pie, use_container_width=True)
