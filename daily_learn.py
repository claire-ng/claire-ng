import streamlit as st
import requests
import datetime
import random
import db

CATEGORIES = [
    ("🔭", "Astronomy"), ("🧬", "Biology"), ("🎨", "Art"), ("💰", "Economics"),
    ("🗺️", "Geography"), ("📜", "History"), ("📚", "Literature"), ("🧮", "Mathematics"),
    ("💊", "Medicine"), ("🎵", "Music"), ("⚙️", "Technology"), ("🧠", "Psychology"),
    ("⚗️", "Science"), ("🏛️", "Philosophy"), ("⚡", "Physics"),
]
CATEGORY_MAP = {c[1]: c[0] for c in CATEGORIES}

FALLBACK_FACTS = [
    {"title": "Honey never spoils", "extract": "Archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible. Honey's low moisture content and acidic pH make it inhospitable to bacteria.", "url": "https://en.wikipedia.org/wiki/Honey"},
    {"title": "Octopuses have three hearts", "extract": "Two hearts pump blood to the gills, while the third pumps it to the rest of the body. When an octopus swims, the heart that delivers blood to the body actually stops beating.", "url": "https://en.wikipedia.org/wiki/Octopus"},
    {"title": "A day on Venus is longer than a year on Venus", "extract": "Venus rotates so slowly that one full rotation takes 243 Earth days, while it only takes 225 Earth days to orbit the Sun. Venus also rotates in the opposite direction to most planets.", "url": "https://en.wikipedia.org/wiki/Venus"},
    {"title": "The human brain uses 20% of your body's energy", "extract": "Despite being only 2% of body weight, the brain consumes roughly 20% of the body's total energy. Most of this fuels electrical signals sent between neurons.", "url": "https://en.wikipedia.org/wiki/Brain"},
    {"title": "Cleopatra lived closer to the Moon landing than to the pyramids", "extract": "The Great Pyramid was built around 2560 BC. Cleopatra lived around 30 BC — 2,500 years after the pyramid. The Moon landing was 1969 AD, only 2,000 years after Cleopatra.", "url": "https://en.wikipedia.org/wiki/Cleopatra"},
    {"title": "More chess games exist than atoms in the universe", "extract": "The number of possible unique chess games is estimated at 10^120, while atoms in the observable universe number around 10^80. This is why chess remains endlessly complex.", "url": "https://en.wikipedia.org/wiki/Chess"},
    {"title": "Bananas are berries, but strawberries are not", "extract": "Botanically, a berry develops from a single flower with one ovary. Bananas qualify. Strawberries develop from multiple ovaries, making them aggregate fruits.", "url": "https://en.wikipedia.org/wiki/Berry_(botany)"},
    {"title": "The shortest war lasted 38 minutes", "extract": "The Anglo-Zanzibar War of 1896 is the shortest recorded war. It was fought between the UK and Zanzibar Sultanate on August 27, 1896, lasting 38–45 minutes.", "url": "https://en.wikipedia.org/wiki/Anglo-Zanzibar_War"},
    {"title": "Water can boil and freeze simultaneously", "extract": "Called the triple point, this is the specific temperature and pressure at which a substance exists as solid, liquid, and gas at once. For water: 0.01°C and 611.657 pascals.", "url": "https://en.wikipedia.org/wiki/Triple_point"},
    {"title": "Oxford University is older than the Aztec Empire", "extract": "Teaching at Oxford began around 1096 AD. The Aztec Empire was founded in 1428 AD — making Oxford over 300 years older.", "url": "https://en.wikipedia.org/wiki/University_of_Oxford"},
    {"title": "Sharks are older than trees", "extract": "Sharks have existed for around 450 million years, while trees only evolved about 350 million years ago. Sharks survived all five mass extinction events.", "url": "https://en.wikipedia.org/wiki/Shark"},
    {"title": "Nintendo was founded in 1889", "extract": "Long before video games, Nintendo was founded in Kyoto in 1889 to produce handmade playing cards. It didn't enter the video game industry until the 1970s.", "url": "https://en.wikipedia.org/wiki/Nintendo"},
    {"title": "The Eiffel Tower grows in summer", "extract": "The iron structure expands when heated, causing it to grow up to 15 cm taller during hot summer days compared to cold winter days.", "url": "https://en.wikipedia.org/wiki/Eiffel_Tower"},
    {"title": "Crows can recognize human faces", "extract": "Research shows crows remember individual human faces and hold grudges for years. They warn other crows about specific people who threatened them.", "url": "https://en.wikipedia.org/wiki/Crow"},
    {"title": "There's a planet that rains glass sideways", "extract": "Exoplanet HD 189733b has winds of 8,700 km/h and silicate particles that rain down sideways at supersonic speeds at 1,000°C.", "url": "https://en.wikipedia.org/wiki/HD_189733_b"},
]

CARD_COLORS = ["#1a1f3a", "#1a2e1a", "#2e1a2e", "#2e2a1a", "#1a2a2e"]


def fetch_wikipedia_article(topic: str = None) -> dict | None:
    try:
        if topic:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}"
        else:
            url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
        r = requests.get(url, timeout=6, headers={"User-Agent": "DailyLearn/1.0"})
        r.raise_for_status()
        data = r.json()
        if data.get("type") == "disambiguation" or len(data.get("extract", "")) < 80:
            return None
        return {
            "title": data.get("title", ""),
            "extract": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", "#"),
            "thumbnail": data.get("thumbnail", {}).get("source"),
        }
    except Exception:
        return None


def get_daily_articles(seed: int) -> list[dict]:
    articles = []
    for _ in range(10):
        art = fetch_wikipedia_article()
        if art:
            articles.append(art)
        if len(articles) == 3:
            break
    if not articles:
        rng = random.Random(seed)
        articles = [dict(f) | {"thumbnail": None} for f in rng.sample(FALLBACK_FACTS, 3)]
    return articles


def render_card(article: dict, idx: int, user_email: str | None, saved: dict):
    title = article["title"]
    extract = article["extract"]
    url = article.get("url", "#")
    thumbnail = article.get("thumbnail")
    color = CARD_COLORS[idx % len(CARD_COLORS)]
    is_saved = title in saved

    content_html = f"""
    <div style="background:{color};border-radius:12px;padding:20px 24px;margin-bottom:4px;">
        <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#666;margin-bottom:6px;">DID YOU KNOW</div>
        <div style="font-size:19px;font-weight:700;color:#fff;margin-bottom:10px;">{title}</div>
        <div style="font-size:14px;color:#bbb;line-height:1.7;">{extract}</div>
    </div>
    """

    if thumbnail:
        c1, c2 = st.columns([1, 3])
        with c1:
            st.image(thumbnail, use_container_width=True)
        with c2:
            st.markdown(content_html, unsafe_allow_html=True)
            _render_card_actions(title, url, article, is_saved, user_email, saved, idx)
    else:
        st.markdown(content_html, unsafe_allow_html=True)
        _render_card_actions(title, url, article, is_saved, user_email, saved, idx)

    st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)


def _render_card_actions(title, url, article, is_saved, user_email, saved, idx):
    ca, cb = st.columns([2, 1])
    with ca:
        if url and url != "#":
            st.markdown(f"[Read more on Wikipedia →]({url})")
    with cb:
        if is_saved:
            if st.button("★ Saved", key=f"unsave_{idx}_{title[:20]}"):
                if user_email:
                    db.delete_article(user_email, title)
                else:
                    saved.pop(title, None)
                    st.session_state["guest_saved"] = saved
                st.rerun()
        else:
            if st.button("☆ Save", key=f"save_{idx}_{title[:20]}"):
                if user_email:
                    db.save_article(user_email, article)
                else:
                    saved[title] = article
                    st.session_state["guest_saved"] = saved
                st.rerun()


def render(user_email: str | None = None):
    today = datetime.date.today()
    day_seed = int(today.strftime("%Y%m%d"))

    streak = db.get_streak(user_email) if user_email else _local_streak()

    saved = db.load_saved_articles(user_email) if user_email else st.session_state.get("guest_saved", {})

    # Header with streak
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
        <div>
            <div style="font-size:26px;font-weight:800;">🧠 Daily Learning</div>
            <div style="color:#666;font-size:13px;">{today.strftime('%A, %B %d %Y')}</div>
        </div>
        <div style="text-align:center;background:#1e1e2e;border-radius:12px;padding:12px 24px;border:1px solid #2a2a3e;">
            <div style="font-size:26px;font-weight:800;color:#f59e0b;">🔥 {streak}</div>
            <div style="font-size:10px;color:#666;letter-spacing:1px;text-transform:uppercase;">day streak</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_daily, tab_explore, tab_saved = st.tabs(["✨ Today's Picks", "🔍 Explore", f"★ Saved ({len(saved)})"])

    with tab_daily:
        if "daily_articles" not in st.session_state or st.session_state.get("daily_date") != str(today):
            with st.spinner("Loading today's topics..."):
                st.session_state["daily_articles"] = get_daily_articles(day_seed)
                st.session_state["daily_date"] = str(today)

        articles = st.session_state.get("daily_articles", [])
        if articles:
            for i, art in enumerate(articles):
                render_card(art, i, user_email, saved)
        else:
            st.warning("Could not load articles. Try refreshing.")

        if st.button("🔄 Shuffle topics"):
            del st.session_state["daily_articles"]
            st.rerun()

    with tab_explore:
        cols = st.columns(5)
        for i, (emoji, name) in enumerate(CATEGORIES):
            with cols[i % 5]:
                if st.button(f"{emoji} {name}", use_container_width=True, key=f"cat_{name}"):
                    st.session_state["selected_category"] = name
                    st.session_state.pop("explore_article", None)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        active = st.session_state.get("selected_category")
        if active:
            emoji = CATEGORY_MAP.get(active, "🔍")
            st.markdown(f"#### {emoji} {active}")
            if "explore_article" not in st.session_state:
                with st.spinner(f"Finding something about {active}..."):
                    art = fetch_wikipedia_article(active)
                    if not art:
                        rng = random.Random(day_seed + hash(active))
                        art = dict(rng.choice(FALLBACK_FACTS)) | {"thumbnail": None}
                    st.session_state["explore_article"] = art
            render_card(st.session_state["explore_article"], 2, user_email, saved)
            if st.button("🔄 Find another"):
                st.session_state.pop("explore_article", None)
                st.rerun()
        else:
            st.markdown("<div style='color:#666;text-align:center;padding:40px 0'>Pick a category above to explore</div>", unsafe_allow_html=True)

    with tab_saved:
        if not saved:
            st.markdown("""
            <div style="text-align:center;padding:60px 0;color:#555;">
                <div style="font-size:40px;">★</div>
                <div style="font-size:16px;margin-top:10px;">No saved articles yet</div>
                <div style="font-size:13px;margin-top:4px;color:#444;">Hit ☆ Save on any article to bookmark it here</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**{len(saved)} saved article{'s' if len(saved) != 1 else ''}**")
            for i, art in enumerate(saved.values()):
                render_card(art, i, user_email, saved)


def _local_streak() -> int:
    today = str(datetime.date.today())
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    data = st.session_state.get("streak", {"count": 1, "last": today})
    if data["last"] == today:
        return data["count"]
    elif data["last"] == yesterday:
        data["count"] += 1
    else:
        data["count"] = 1
    data["last"] = today
    st.session_state["streak"] = data
    return data["count"]
