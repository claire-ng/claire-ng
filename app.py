import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from screener import DEFAULT_TICKERS, fetch_screen, fetch_chart_data

st.set_page_config(
    page_title="Day Trading Screener",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Day Trading Screener")
st.caption("Data via Yahoo Finance · prices delayed ~15 min")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

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
        "RSI range",
        min_value=0, max_value=100,
        value=(0, 100),
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

# ── Main ──────────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame()

if run:
    with st.spinner(f"Fetching data for {len(custom_tickers)} tickers…"):
        st.session_state["df"] = fetch_screen(custom_tickers)

df: pd.DataFrame = st.session_state["df"]

if df.empty:
    st.info("Click **Run Screen** in the sidebar to fetch data.")
    st.stop()

# Apply filters
mask = (
    df["% Change"].between(pct_min, pct_max)
    & (df["Vol / Avg"] >= vol_ratio_min)
)
if "RSI (14)" in df.columns:
    rsi_mask = df["RSI (14)"].isna() | df["RSI (14)"].between(rsi_min, rsi_max)
    mask &= rsi_mask

filtered = df[mask].copy()

# ── Summary bar ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Showing", f"{len(filtered)} / {len(df)}")
if not filtered.empty:
    gainers = (filtered["% Change"] > 0).sum()
    losers = (filtered["% Change"] < 0).sum()
    c2.metric("Gainers", gainers, delta=f"+{gainers}", delta_color="normal")
    c3.metric("Losers", losers, delta=f"-{losers}", delta_color="inverse")
    avg_rsi = filtered["RSI (14)"].mean()
    c4.metric("Avg RSI", f"{avg_rsi:.1f}" if pd.notna(avg_rsi) else "—")

st.divider()

# ── Colour helper ─────────────────────────────────────────────────────────────
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
    .applymap(colour_pct, subset=["% Change", "% from High"])
    .applymap(colour_rsi, subset=["RSI (14)"])
    .format({
        "Price": "${:.2f}",
        "% Change": "{:+.2f}%",
        "Vol / Avg": "{:.2f}x",
        "RSI (14)": "{:.1f}",
        "% from High": "{:+.1f}%",
        "Mkt Cap ($B)": "${:.1f}B",
    }, na_rep="—")
)

st.dataframe(styled, use_container_width=True, height=420)

# ── Chart section ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Chart")

col_l, col_r = st.columns([1, 3])
with col_l:
    ticker_choice = st.selectbox(
        "Pick a ticker",
        options=filtered["Ticker"].tolist(),
    )
    chart_period = st.radio(
        "Period",
        ["1d", "5d", "1mo"],
        index=1,
        horizontal=True,
    )
    interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d"}

with col_r:
    if ticker_choice:
        with st.spinner(f"Loading {ticker_choice} chart…"):
            cdf = fetch_chart_data(ticker_choice, period=chart_period, interval=interval_map[chart_period])

        if cdf.empty:
            st.warning("No chart data available.")
        else:
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                row_heights=[0.55, 0.25, 0.20],
                vertical_spacing=0.03,
            )

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=cdf.index,
                open=cdf["Open"], high=cdf["High"],
                low=cdf["Low"], close=cdf["Close"],
                name="Price",
                increasing_line_color="#22c55e",
                decreasing_line_color="#ef4444",
            ), row=1, col=1)

            if "EMA9" in cdf:
                fig.add_trace(go.Scatter(x=cdf.index, y=cdf["EMA9"], name="EMA9",
                                         line=dict(color="#facc15", width=1)), row=1, col=1)
            if "EMA20" in cdf:
                fig.add_trace(go.Scatter(x=cdf.index, y=cdf["EMA20"], name="EMA20",
                                         line=dict(color="#818cf8", width=1)), row=1, col=1)

            # Volume
            colors = ["#22c55e" if c >= o else "#ef4444"
                      for c, o in zip(cdf["Close"], cdf["Open"])]
            fig.add_trace(go.Bar(x=cdf.index, y=cdf["Volume"], name="Volume",
                                  marker_color=colors, showlegend=False), row=2, col=1)

            # RSI
            if "RSI" in cdf:
                fig.add_trace(go.Scatter(x=cdf.index, y=cdf["RSI"], name="RSI",
                                         line=dict(color="#a78bfa", width=1.5)), row=3, col=1)
                fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=3, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="#22c55e", row=3, col=1)

            fig.update_layout(
                template="plotly_dark",
                title=f"{ticker_choice} · {chart_period}",
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=560,
                margin=dict(l=0, r=0, t=40, b=0),
            )
            fig.update_yaxes(title_text="Price", row=1, col=1)
            fig.update_yaxes(title_text="Vol", row=2, col=1)
            fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])

            st.plotly_chart(fig, use_container_width=True)
