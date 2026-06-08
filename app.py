import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import json
from pathlib import Path
from screener import DEFAULT_TICKERS, fetch_screen, fetch_chart_data
from portfolio import enrich_portfolio
import daily_learn
import tools
import deep_dive

WATCHLIST_FILE = Path("watchlist.json")

def load_watchlist():
    if WATCHLIST_FILE.exists():
        return json.loads(WATCHLIST_FILE.read_text())
    return DEFAULT_TICKERS

def save_watchlist(tickers):
    WATCHLIST_FILE.write_text(json.dumps(tickers))

st.set_page_config(
    page_title="Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f1117; border-right: 1px solid #1e1e2e; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #1e1e2e; border-radius: 8px; padding: 6px 16px;
    color: #888; border: none;
}
.stTabs [aria-selected="true"] { background: #7c3aed !important; color: #fff !important; }
div[data-testid="metric-container"] {
    background: #1e1e2e; border-radius: 10px; padding: 16px;
    border: 1px solid #2a2a3e;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Filters")
    pct_min, pct_max = st.slider("% Change today", -20.0, 20.0, (-20.0, 20.0), 0.5)
    vol_ratio_min = st.slider("Min volume / 20-day avg", 0.0, 10.0, 0.0, 0.1)
    rsi_min, rsi_max = st.slider("RSI range", 0, 100, (0, 100))

    st.divider()
    st.markdown("### Watchlist")

    current = load_watchlist()

    custom_raw = st.text_area(
        "Tickers (comma-separated)",
        value=", ".join(current),
        height=130,
    )
    custom_tickers = [t.strip().upper() for t in custom_raw.split(",") if t.strip()]

    to_remove = st.multiselect("Remove tickers", options=current)
    if to_remove:
        if st.button("🗑️ Remove selected", use_container_width=True):
            updated = [t for t in custom_tickers if t not in to_remove]
            save_watchlist(updated)
            st.rerun()

    col_run, col_save = st.columns(2)
    run = col_run.button("▶ Run", type="primary", use_container_width=True)
    if col_save.button("💾 Save", use_container_width=True):
        save_watchlist(custom_tickers)
        st.success("Watchlist saved!")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:8px;">
    <span style="font-size:28px;font-weight:800;">📈 Trading Dashboard</span>
    <span style="color:#666;font-size:13px;margin-left:12px;">Prices delayed ~15 min · Yahoo Finance</span>
</div>
""", unsafe_allow_html=True)

tab_screen, tab_portfolio, tab_learn, tab_glossary, tab_calendar, tab_dive, tab_macro = st.tabs([
    "🔍 Screener", "💼 Portfolio", "🧠 Daily Learning", "📖 Glossary", "📅 Calendar", "🏢 Deep Dive", "🌍 Macro"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCREENER
# ═══════════════════════════════════════════════════════════════════════════════
with tab_screen:
    if "df" not in st.session_state:
        st.session_state["df"] = pd.DataFrame()

    if run:
        with st.spinner(f"Fetching {len(custom_tickers)} tickers…"):
            st.session_state["df"] = fetch_screen(custom_tickers)

    df: pd.DataFrame = st.session_state["df"]

    if df.empty:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#555;">
            <div style="font-size:40px;">📊</div>
            <div style="font-size:18px;margin-top:8px;">Click <b>▶ Run Screen</b> in the sidebar to load data</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        mask = df["% Change"].between(pct_min, pct_max) & (df["Vol / Avg"] >= vol_ratio_min)
        if "RSI (14)" in df.columns:
            mask &= df["RSI (14)"].isna() | df["RSI (14)"].between(rsi_min, rsi_max)
        filtered = df[mask].copy()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Showing", f"{len(filtered)} / {len(df)}")
        if not filtered.empty:
            c2.metric("Gainers 🟢", int((filtered["% Change"] > 0).sum()))
            c3.metric("Losers 🔴", int((filtered["% Change"] < 0).sum()))
            avg_rsi = filtered["RSI (14)"].mean()
            c4.metric("Avg RSI", f"{avg_rsi:.1f}" if pd.notna(avg_rsi) else "—")

        st.divider()

        def colour_pct(val):
            if pd.isna(val): return ""
            return "color: #22c55e" if val > 0 else ("color: #ef4444" if val < 0 else "")

        def colour_rsi(val):
            if pd.isna(val): return ""
            if val >= 70: return "color: #ef4444; font-weight:bold"
            if val <= 30: return "color: #22c55e; font-weight:bold"
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
        st.markdown("#### Chart")
        col_l, col_r = st.columns([1, 3])
        with col_l:
            ticker_choice = st.selectbox("Ticker", options=filtered["Ticker"].tolist())
            chart_period = st.radio("Period", ["1d", "5d", "1mo"], index=1, horizontal=True)
            interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d"}

        with col_r:
            if ticker_choice:
                with st.spinner(f"Loading {ticker_choice}…"):
                    cdf = fetch_chart_data(ticker_choice, period=chart_period, interval=interval_map[chart_period])
                if cdf.empty:
                    st.warning("No chart data.")
                else:
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                        row_heights=[0.55, 0.25, 0.20], vertical_spacing=0.03)
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
                    colors = ["#22c55e" if c >= o else "#ef4444" for c, o in zip(cdf["Close"], cdf["Open"])]
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
    st.markdown("#### My Portfolio")

    from portfolio import load_positions, save_positions
    positions = load_positions()

    with st.expander("➕ Add / Edit Position", expanded=len(positions) == 0):
        with st.form("add_position"):
            fc1, fc2, fc3 = st.columns(3)
            new_ticker = fc1.text_input("Ticker", placeholder="e.g. AAPL").strip().upper()
            new_shares = fc2.number_input("Shares", min_value=0.001, step=0.001, format="%.3f")
            new_cost = fc3.number_input("Avg Cost / Share ($)", min_value=0.01, step=0.01, format="%.2f")
            submitted = st.form_submit_button("Save Position", type="primary")
            if submitted and new_ticker:
                existing = next((p for p in positions if p["ticker"] == new_ticker), None)
                if existing:
                    existing["shares"] = new_shares
                    existing["cost_basis"] = new_cost
                else:
                    positions.append({"ticker": new_ticker, "shares": new_shares, "cost_basis": new_cost})
                save_positions(positions)
                st.success(f"Saved {new_ticker}")
                st.rerun()

    if positions:
        remove_ticker = st.selectbox("Remove a position", ["—"] + [p["ticker"] for p in positions])
        if remove_ticker != "—" and st.button(f"Remove {remove_ticker}", type="secondary"):
            save_positions([p for p in positions if p["ticker"] != remove_ticker])
            st.rerun()

    st.divider()

    if not positions:
        st.info("No positions yet. Add some above.")
    else:
        if st.button("🔄 Refresh Prices", type="primary"):
            with st.spinner("Fetching live prices…"):
                st.session_state["pdf"] = enrich_portfolio(positions)
        elif "pdf" not in st.session_state:
            with st.spinner("Fetching live prices…"):
                st.session_state["pdf"] = enrich_portfolio(positions)

        pdf: pd.DataFrame = st.session_state.get("pdf", pd.DataFrame())
        if pdf.empty:
            st.warning("Could not fetch prices.")
        else:
            total_value = pdf["Mkt Value"].sum()
            total_cost = pdf["Total Cost"].sum()
            total_upl = pdf["Unrealized P&L"].sum()
            total_day = pdf["Day P&L"].sum()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Portfolio Value", f"${total_value:,.2f}")
            m2.metric("Total Cost Basis", f"${total_cost:,.2f}")
            m3.metric("Unrealized P&L", f"${total_upl:,.2f}",
                      delta=f"{total_upl / total_cost * 100:+.2f}%" if total_cost else None)
            m4.metric("Today's P&L", f"${total_day:,.2f}",
                      delta=f"{total_day / (total_value - total_day) * 100:+.2f}%" if total_value else None)

            st.divider()

            def colour_pl(val):
                if pd.isna(val): return ""
                return "color: #22c55e" if val > 0 else ("color: #ef4444" if val < 0 else "")

            pdf_styled = (
                pdf.style
                .map(colour_pl, subset=["Unrealized P&L", "Unrealized %", "Day P&L", "Day %"])
                .format({
                    "Shares": "{:.3f}", "Avg Cost": "${:.2f}", "Last Price": "${:.2f}",
                    "Mkt Value": "${:,.2f}", "Total Cost": "${:,.2f}",
                    "Unrealized P&L": "${:+,.2f}", "Unrealized %": "{:+.2f}%",
                    "Day P&L": "${:+,.2f}", "Day %": "{:+.2f}%",
                }, na_rep="—")
            )
            st.dataframe(pdf_styled, use_container_width=True)

            st.divider()
            st.markdown("#### Allocation")
            pie = px.pie(pdf.dropna(subset=["Mkt Value"]), names="Ticker", values="Mkt Value",
                         color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
            pie.update_layout(template="plotly_dark", height=360, margin=dict(t=20))
            st.plotly_chart(pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DAILY LEARNING
# ═══════════════════════════════════════════════════════════════════════════════
with tab_learn:
    daily_learn.render()

with tab_glossary:
    tools.render_glossary()

with tab_calendar:
    tools.render_calendar()

with tab_dive:
    deep_dive.render_deep_dive()

with tab_macro:
    deep_dive.render_macro()
