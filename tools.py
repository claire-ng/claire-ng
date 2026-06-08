import streamlit as st
import datetime
import requests

TERMS = {
    "Yield": "The income you earn from an investment, shown as a percentage. A bond with a 5% yield pays you $5 a year for every $100 you put in. Higher yield usually means higher risk.",
    "Market Cap": "The total value of a company's shares. Share price × number of shares. Apple at $180/share with 15 billion shares = $2.7 trillion market cap. Big = 'large-cap', small = 'small-cap'.",
    "P/E Ratio": "Price-to-Earnings ratio. How much you're paying for $1 of a company's profit. P/E of 20 means you're paying $20 for every $1 earned. High P/E = expensive but fast-growing. Low P/E = cheap but maybe struggling.",
    "Dividend": "A cash payment companies send to shareholders, usually every quarter. If you own 100 shares and the dividend is $0.50/share, you get $50. Not all stocks pay dividends.",
    "Volatility": "How wildly a stock's price swings. High volatility = big up and down moves. Low volatility = steady, calm price. More volatile = more risk, but also more opportunity.",
    "Bull Market": "When prices are rising and people feel confident. Usually defined as a 20%+ rise from a recent low. The opposite of a bear market.",
    "Bear Market": "When prices are falling and fear takes over. Usually defined as a 20%+ drop from a recent high. Recessions often come with bear markets.",
    "Short Selling": "Borrowing shares, selling them, hoping the price falls, then buying them back cheaper and pocketing the difference. Risky — if the price goes up instead, your losses are unlimited.",
    "Options": "Contracts that give you the right (but not obligation) to buy or sell a stock at a set price before a deadline. Used to bet on direction or hedge against losses.",
    "Hedge": "A trade that reduces your risk. Like insurance. If you own Apple stock, buying a 'put option' on Apple hedges you — if Apple crashes, the put gains value and limits your loss.",
    "RSI (Relative Strength Index)": "A 0–100 score that shows if a stock is overbought or oversold. Above 70 = possibly overbought (might fall soon). Below 30 = possibly oversold (might bounce). Traders use it as a signal.",
    "EMA (Exponential Moving Average)": "An average of past prices that gives more weight to recent data. EMA-9 = average of last 9 days. Traders watch when a short EMA crosses a long EMA as a buy/sell signal.",
    "Support Level": "A price floor where a stock tends to stop falling and bounce back up. Buyers step in at this level. If it breaks through support, it can fall fast.",
    "Resistance Level": "A price ceiling where a stock tends to stop rising and pull back. Sellers step in here. If it breaks through resistance, it often surges.",
    "Volume": "How many shares were traded in a period. High volume on a big move = the move is more credible. Low volume = fewer people believe the move.",
    "Liquidity": "How easily you can buy or sell something without moving the price. Cash is perfectly liquid. A rare painting is illiquid. Stocks on big exchanges are very liquid.",
    "Margin": "Borrowing money from your broker to buy more stock than you can afford. Amplifies gains — and losses. If your position falls too much, you get a 'margin call' demanding more cash.",
    "Short Squeeze": "When a heavily-shorted stock rises fast, forcing short sellers to buy shares to cut their losses, which pushes the price even higher. GME in 2021 is the famous example.",
    "ETF (Exchange-Traded Fund)": "A basket of stocks you can buy as one share. SPY tracks the S&P 500 — buying one share is like owning a tiny piece of 500 companies. Lower risk than single stocks.",
    "S&P 500": "An index of the 500 largest US companies by market cap. Considered the benchmark for the US stock market. Most investors try to 'beat the S&P 500'.",
    "Federal Reserve (The Fed)": "The US central bank. Controls interest rates to manage inflation and employment. When the Fed raises rates, borrowing gets expensive and stocks often fall. When they cut, markets usually rally.",
    "Interest Rates": "The cost of borrowing money, set by central banks. High rates = expensive loans, slower economy, lower stock valuations. Low rates = cheap borrowing, more spending, higher stocks.",
    "Inflation": "When prices rise over time and your money buys less. The Fed targets 2% inflation as healthy. Too much inflation erodes savings. Central banks raise interest rates to cool inflation.",
    "GDP (Gross Domestic Product)": "The total value of everything a country produces. The main scorecard for an economy's size and health. Two consecutive quarters of falling GDP = a recession.",
    "Recession": "A period of economic decline, officially defined as two straight quarters of negative GDP growth. Unemployment rises, spending falls, stocks often drop.",
    "Earnings Per Share (EPS)": "A company's profit divided by its number of shares. If a company earns $1B and has 500M shares, EPS = $2. Higher EPS = more profitable per share.",
    "Revenue": "The total money a company brings in from sales, before any costs. Also called 'top line'. Revenue growing fast is usually a good sign, even if profits are small.",
    "Profit Margin": "How much of each dollar of revenue becomes profit. 20% margin means for every $100 in sales, $20 is profit. Higher is better.",
    "IPO (Initial Public Offering)": "When a private company sells shares to the public for the first time on a stock exchange. How companies 'go public' and raise money from everyday investors.",
    "52-Week High/Low": "The highest and lowest price a stock has traded at over the past year. Stocks near their 52-week high are strong. Near their low might be struggling — or a bargain.",
    "Candlestick Chart": "A price chart showing open, high, low, and close for each time period as a colored bar. Green = price went up. Red = price went down. The 'wicks' show the highest and lowest points.",
    "Gap Up / Gap Down": "When a stock opens significantly higher or lower than it closed the day before — usually after earnings or big news. Gaps often get 'filled' later as price retraces.",
    "Cost Basis": "What you originally paid for an investment. Used to calculate your gain or loss. If you bought at $50 and sell at $80, your cost basis is $50 and your gain is $30.",
    "Unrealized Gain/Loss": "Profit or loss on a position you still hold — it's only 'on paper' until you sell. If you bought at $50 and it's now $70, you have a $20 unrealized gain.",
    "Portfolio": "Your full collection of investments across all accounts and assets. Diversifying your portfolio across sectors and asset types reduces overall risk.",
    "Diversification": "Spreading investments across different assets so one bad pick doesn't sink you. 'Don't put all your eggs in one basket.'",
    "Asset Allocation": "How you split your portfolio across categories like stocks, bonds, cash, and real estate. Generally, more stocks = higher risk and reward.",
    "Bond": "A loan you give to a company or government. They pay you interest (the yield) and return your money at a set date. Safer than stocks, but lower returns.",
    "Blue Chip": "Large, well-established, financially stable companies with a long track record. Think Apple, Microsoft, Johnson & Johnson. Generally safer but slower-growing.",
    "Day Trading": "Buying and selling stocks within the same trading day to profit from short-term price moves. High risk, requires skill and discipline, and most day traders lose money.",
    "Momentum": "The tendency for rising stocks to keep rising and falling stocks to keep falling, at least in the short term. Momentum traders ride this trend.",
    "Catalyst": "A specific event that causes a stock to move — earnings beat, FDA approval, major contract win, or bad news. Traders look for upcoming catalysts to plan trades.",
    "Pre-market / After-hours": "Trading that happens before the market opens (4–9:30am ET) or after it closes (4–8pm ET). Lower volume, wider spreads, more volatile.",
}

CALENDAR_EVENTS = [
    # FOMC meetings 2026
    ("2026-06-17", "fed", "FOMC Meeting — Fed interest rate decision"),
    ("2026-07-28", "fed", "FOMC Meeting — Fed interest rate decision"),
    ("2026-09-15", "fed", "FOMC Meeting — Fed interest rate decision"),
    ("2026-11-03", "fed", "FOMC Meeting — Fed interest rate decision"),
    ("2026-12-15", "fed", "FOMC Meeting — Fed interest rate decision"),
    # Jobs reports 2026 (first Friday of each month)
    ("2026-06-05", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2026-07-10", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2026-08-07", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2026-09-04", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2026-10-02", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2026-11-06", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2026-12-04", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    # CPI reports 2026 (mid-month)
    ("2026-06-11", "inflation", "CPI Inflation Report"),
    ("2026-07-14", "inflation", "CPI Inflation Report"),
    ("2026-08-13", "inflation", "CPI Inflation Report"),
    ("2026-09-11", "inflation", "CPI Inflation Report"),
    ("2026-10-14", "inflation", "CPI Inflation Report"),
    ("2026-11-12", "inflation", "CPI Inflation Report"),
    ("2026-12-10", "inflation", "CPI Inflation Report"),
    # Earnings seasons 2026
    ("2026-07-13", "earnings", "Q2 2026 Earnings Season begins"),
    ("2026-10-12", "earnings", "Q3 2026 Earnings Season begins"),
    # Market holidays 2026
    ("2026-07-03", "holiday", "Market closed — Independence Day (observed)"),
    ("2026-09-07", "holiday", "Market closed — Labor Day"),
    ("2026-11-26", "holiday", "Market closed — Thanksgiving"),
    ("2026-12-25", "holiday", "Market closed — Christmas"),
    # 2027
    ("2027-01-01", "holiday", "Market closed — New Year's Day"),
    ("2027-01-18", "holiday", "Market closed — MLK Day"),
    ("2027-01-08", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2027-02-05", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2027-03-05", "jobs", "Jobs Report (Non-Farm Payrolls)"),
    ("2027-01-14", "inflation", "CPI Inflation Report"),
    ("2027-02-11", "inflation", "CPI Inflation Report"),
    ("2027-03-11", "inflation", "CPI Inflation Report"),
    ("2027-01-11", "earnings", "Q4 2026 Earnings Season begins"),
    ("2027-01-26", "fed", "FOMC Meeting — Fed interest rate decision"),
    ("2027-03-16", "fed", "FOMC Meeting — Fed interest rate decision"),
]

EVENT_STYLES = {
    "fed":      {"emoji": "🏦", "color": "#7c3aed", "label": "Fed"},
    "jobs":     {"emoji": "👷", "color": "#0ea5e9", "label": "Jobs"},
    "inflation":{"emoji": "📊", "color": "#f59e0b", "label": "CPI"},
    "earnings": {"emoji": "💰", "color": "#22c55e", "label": "Earnings"},
    "holiday":  {"emoji": "🏖️", "color": "#64748b", "label": "Holiday"},
}


def _search_wikipedia(query: str) -> list[dict]:
    """Search Wikipedia and return top results with summaries."""
    try:
        # Search for matching articles
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", "list": "search", "srsearch": query + " finance",
            "srlimit": 4, "format": "json",
        }
        r = requests.get(search_url, params=params, timeout=6, headers={"User-Agent": "FinanceGlossary/1.0"})
        results = r.json().get("query", {}).get("search", [])
        if not results:
            return []

        # Fetch summaries for the top hits
        articles = []
        for hit in results[:3]:
            title = hit["title"]
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
            sr = requests.get(summary_url, timeout=6, headers={"User-Agent": "FinanceGlossary/1.0"})
            data = sr.json()
            extract = data.get("extract", "")
            if extract and len(extract) > 60:
                articles.append({
                    "title": title,
                    "extract": extract[:600] + ("…" if len(extract) > 600 else ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", "#"),
                })
        return articles
    except Exception:
        return []


def render_glossary():
    st.markdown("#### 📖 Finance Jargon Buster")
    st.caption("Built-in plain-English definitions — or search anything and we'll pull from Wikipedia.")

    search = st.text_input("🔍 Search any finance term...", placeholder="e.g. yield, hedge fund, quantitative easing")

    if not search:
        # Show full alphabetical glossary
        letters = sorted(set(k[0].upper() for k in TERMS))
        for letter in letters:
            group = {k: v for k, v in TERMS.items() if k[0].upper() == letter}
            st.markdown(f"**{letter}**")
            for term, definition in sorted(group.items()):
                with st.expander(term):
                    st.write(definition)
        return

    q = search.lower()
    local_matches = {k: v for k, v in TERMS.items() if q in k.lower() or q in v.lower()}

    if local_matches:
        st.markdown("**From our glossary:**")
        for term, definition in sorted(local_matches.items()):
            with st.expander(term, expanded=True):
                st.write(definition)
        st.markdown("---")

    # Always also pull from Wikipedia
    with st.spinner(f"Searching Wikipedia for '{search}'…"):
        wiki_results = _search_wikipedia(search)

    if wiki_results:
        st.markdown("**From Wikipedia:**")
        for art in wiki_results:
            with st.expander(art["title"], expanded=not local_matches):
                st.write(art["extract"])
                st.markdown(f"[Full article on Wikipedia →]({art['url']})")
    elif not local_matches:
        st.warning(f"No results found for '{search}'. Try different words.")


def render_calendar():
    st.markdown("#### 📅 Market Calendar")
    st.caption("Upcoming events that move markets — know what's coming before it hits.")

    today = datetime.date.today()

    # Parse and filter to upcoming events
    upcoming = []
    for date_str, etype, desc in CALENDAR_EVENTS:
        d = datetime.date.fromisoformat(date_str)
        if d >= today:
            upcoming.append((d, etype, desc))
    upcoming.sort(key=lambda x: x[0])

    # Filter controls
    col1, col2 = st.columns([2, 1])
    with col1:
        show_types = st.multiselect(
            "Filter by type",
            options=["fed", "jobs", "inflation", "earnings", "holiday"],
            default=["fed", "jobs", "inflation", "earnings"],
            format_func=lambda x: f"{EVENT_STYLES[x]['emoji']} {EVENT_STYLES[x]['label']}",
        )
    with col2:
        weeks_ahead = st.selectbox("Show", [4, 8, 12, 26, 52], index=1, format_func=lambda x: f"Next {x} weeks")

    cutoff = today + datetime.timedelta(weeks=weeks_ahead)
    filtered = [(d, e, desc) for d, e, desc in upcoming if e in show_types and d <= cutoff]

    if not filtered:
        st.info("No events in this range. Try extending the time window.")
        return

    # Group by month
    from itertools import groupby
    for month, group in groupby(filtered, key=lambda x: x[0].strftime("%B %Y")):
        st.markdown(f"**{month}**")
        for d, etype, desc in group:
            style = EVENT_STYLES[etype]
            days_away = (d - today).days
            if days_away == 0:
                when = "**TODAY**"
                when_color = "#ef4444"
            elif days_away == 1:
                when = "Tomorrow"
                when_color = "#f59e0b"
            elif days_away <= 7:
                when = f"In {days_away} days"
                when_color = "#f59e0b"
            else:
                when = d.strftime("%a %b %d")
                when_color = "#888"

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 16px;
                        background:#1e1e2e;border-radius:8px;margin-bottom:6px;
                        border-left:3px solid {style['color']};">
                <div style="font-size:20px;">{style['emoji']}</div>
                <div style="flex:1;">
                    <div style="font-size:14px;color:#fff;">{desc}</div>
                    <div style="font-size:11px;color:{when_color};margin-top:2px;">{when}</div>
                </div>
                <div style="background:{style['color']}22;color:{style['color']};
                            font-size:10px;padding:2px 8px;border-radius:4px;font-weight:600;">
                    {style['label']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")
