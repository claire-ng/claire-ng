import streamlit as st
import requests
import datetime
import random

CATEGORIES = [
    "Science", "History", "Technology", "Mathematics", "Philosophy",
    "Biology", "Astronomy", "Psychology", "Economics", "Art",
    "Literature", "Music", "Geography", "Medicine", "Physics",
]

WIKI_RANDOM_URL = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
WIKI_SEARCH_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"


def fetch_random_article(seed: int) -> dict | None:
    """Fetch a random Wikipedia article. Uses seed to vary by day."""
    try:
        r = requests.get(WIKI_RANDOM_URL, timeout=8, headers={"User-Agent": "DailyLearn/1.0"})
        r.raise_for_status()
        data = r.json()
        if data.get("type") == "disambiguation":
            return None
        return data
    except Exception:
        return None


def fetch_article_by_topic(topic: str) -> dict | None:
    try:
        r = requests.get(
            WIKI_SEARCH_URL.format(requests.utils.quote(topic)),
            timeout=8,
            headers={"User-Agent": "DailyLearn/1.0"},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("type") == "disambiguation":
            return None
        return data
    except Exception:
        return None


def render_article_card(article: dict):
    title = article.get("title", "Unknown")
    extract = article.get("extract", "No summary available.")
    url = article.get("content_urls", {}).get("desktop", {}).get("page", "#")
    thumbnail = article.get("thumbnail", {}).get("source")

    with st.container():
        st.markdown("---")
        if thumbnail:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(thumbnail, use_container_width=True)
            with col2:
                st.subheader(title)
                st.write(extract)
                st.markdown(f"[Read full article on Wikipedia →]({url})")
        else:
            st.subheader(title)
            st.write(extract)
            st.markdown(f"[Read full article on Wikipedia →]({url})")


def render():
    st.title("🧠 Daily Learning")
    st.caption("Expand your mind — something new every day.")

    today = datetime.date.today()
    day_seed = int(today.strftime("%Y%m%d"))

    # Tabs: today's picks vs explore by category
    tab_daily, tab_explore = st.tabs(["Today's Picks", "Explore by Category"])

    with tab_daily:
        st.markdown(f"**{today.strftime('%A, %B %d %Y')}** — here are today's random discoveries:")

        if "daily_articles" not in st.session_state or st.session_state.get("daily_date") != str(today):
            with st.spinner("Fetching today's topics..."):
                articles = []
                random.seed(day_seed)
                attempts = 0
                while len(articles) < 3 and attempts < 10:
                    art = fetch_random_article(day_seed + attempts)
                    if art and art.get("extract") and len(art["extract"]) > 100:
                        articles.append(art)
                    attempts += 1
                st.session_state["daily_articles"] = articles
                st.session_state["daily_date"] = str(today)

        articles = st.session_state["daily_articles"]
        if articles:
            for art in articles:
                render_article_card(art)
        else:
            st.warning("Couldn't load articles right now. Try refreshing.")

        if st.button("🔄 Refresh picks"):
            del st.session_state["daily_articles"]
            st.rerun()

    with tab_explore:
        st.markdown("Pick a category and discover something new:")
        category = st.selectbox("Category", CATEGORIES)

        if st.button("Discover", key="explore_btn"):
            with st.spinner(f"Finding something about {category}..."):
                # Use a random subtopic approach: fetch article with category as seed
                random.seed(day_seed + hash(category))
                art = fetch_article_by_topic(category)
                if art and art.get("extract"):
                    st.session_state["explore_article"] = art
                else:
                    # fallback to random
                    art = fetch_random_article(day_seed)
                    st.session_state["explore_article"] = art

        if "explore_article" in st.session_state and st.session_state["explore_article"]:
            render_article_card(st.session_state["explore_article"])
