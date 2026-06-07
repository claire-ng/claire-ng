import streamlit as st
import requests
import datetime
import random

CATEGORIES = [
    ("🔭", "Astronomy"), ("🧬", "Biology"), ("🎨", "Art"), ("💰", "Economics"),
    ("🗺️", "Geography"), ("📜", "History"), ("📚", "Literature"), ("🧮", "Mathematics"),
    ("💊", "Medicine"), ("🎵", "Music"), ("⚙️", "Technology"), ("🧠", "Psychology"),
    ("⚗️", "Science"), ("🏛️", "Philosophy"), ("⚡", "Physics"),
]
CATEGORY_NAMES = [c[1] for c in CATEGORIES]
CATEGORY_MAP = {c[1]: c[0] for c in CATEGORIES}

FALLBACK_FACTS = [
    {"title": "Honey never spoils", "extract": "Archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible. Honey's low moisture content and acidic pH make it inhospitable to bacteria and microorganisms.", "url": "https://en.wikipedia.org/wiki/Honey"},
    {"title": "Octopuses have three hearts", "extract": "Two hearts pump blood to the gills, while the third pumps it to the rest of the body. When an octopus swims, the heart that delivers blood to the body actually stops beating, which is why octopuses tire so quickly.", "url": "https://en.wikipedia.org/wiki/Octopus"},
    {"title": "A day on Venus is longer than a year on Venus", "extract": "Venus rotates so slowly that one full rotation (a day) takes 243 Earth days, while it only takes 225 Earth days to orbit the Sun. Venus also rotates in the opposite direction to most planets.", "url": "https://en.wikipedia.org/wiki/Venus"},
    {"title": "The human brain uses 20% of your body's energy", "extract": "Despite accounting for only about 2% of body weight, the brain consumes roughly 20% of the body's total energy. Most of this energy fuels electrical signals sent between neurons.", "url": "https://en.wikipedia.org/wiki/Brain"},
    {"title": "Cleopatra lived closer to the Moon landing than to the pyramids", "extract": "The Great Pyramid was built around 2560 BC. Cleopatra lived around 30 BC — about 2,500 years after the pyramid. The Moon landing was 1969 AD, only about 2,000 years after Cleopatra.", "url": "https://en.wikipedia.org/wiki/Cleopatra"},
    {"title": "More chess games exist than atoms in the universe", "extract": "The number of possible unique chess games is estimated at 10^120 (the Shannon number), while atoms in the observable universe number around 10^80. This is why chess remains endlessly complex.", "url": "https://en.wikipedia.org/wiki/Chess"},
    {"title": "Bananas are berries, but strawberries are not", "extract": "Botanically, a berry develops from a single flower with one ovary. Bananas qualify. Strawberries develop from multiple ovaries, making them aggregate fruits — not true berries.", "url": "https://en.wikipedia.org/wiki/Berry_(botany)"},
    {"title": "The shortest war in history lasted 38 minutes", "extract": "The Anglo-Zanzibar War of 1896 is the shortest recorded war. It was fought between the UK and Zanzibar Sultanate on August 27, 1896, and lasted between 38 and 45 minutes.", "url": "https://en.wikipedia.org/wiki/Anglo-Zanzibar_War"},
    {"title": "Water can boil and freeze simultaneously", "extract": "This is called the triple point — the specific temperature and pressure at which a substance exists as solid, liquid, and gas at once. For water: exactly 0.01°C and 611.657 pascals.", "url": "https://en.wikipedia.org/wiki/Triple_point"},
    {"title": "Oxford University is older than the Aztec Empire", "extract": "Teaching at Oxford began around 1096 AD. The Aztec Empire was founded in 1428 AD — making Oxford over 300 years older than the Aztecs.", "url": "https://en.wikipedia.org/wiki/University_of_Oxford"},
    {"title": "Sharks are older than trees", "extract": "Sharks have existed for around 450 million years, while trees only evolved about 350 million years ago. Sharks predate trees by 100 million years and survived all five mass extinction events.", "url": "https://en.wikipedia.org/wiki/Shark"},
    {"title": "Nintendo was founded in 1889", "extract": "Long before video games, Nintendo was founded in Kyoto, Japan in 1889 to produce handmade playing cards called hanafuda. It didn't enter the video game industry until the 1970s.", "url": "https://en.wikipedia.org/wiki/Nintendo"},
    {"title": "The Eiffel Tower grows in summer", "extract": "The iron structure of the Eiffel Tower expands when heated, causing it to grow by up to 15 cm (6 inches) taller during hot summer days compared to cold winter days.", "url": "https://en.wikipedia.org/wiki/Eiffel_Tower"},
    {"title": "Crows can recognize human faces", "extract": "Research shows crows remember individual human faces and can hold grudges for years. They've been observed warning other crows about specific people who threatened them.", "url": "https://en.wikipedia.org/wiki/Crow"},
    {"title": "There's a planet that rains glass sideways", "extract": "Exoplanet HD 189733b has winds of 8,700 km/h and temperatures of 1,000°C. Its silicate atmosphere condenses into glass particles that rain down sideways at supersonic speeds.", "url": "https://en.wikipedia.org/wiki/HD_189733_b"},
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
        sample = rng.sample(FALLBACK_FACTS, 3)
        articles = [dict(f) | {"thumbnail": None} for f in sample]

    return articles


def render_card(article: dict, idx: int = 0, show_save: bool = True):
    title = article["title"]
    extract = article["extract"]
    url = article.get("url", "#")
    thumbnail = article.get("thumbnail")
    color = CARD_COLORS[idx % len(CARD_COLORS)]

    is_saved = title in st.session_state.get("saved_articles", {})

    if thumbnail:
        left, right = st.columns([1, 3])
        with left:
            st.image(thumbnail, use_container_width=True)
        with right:
            st.markdown(f"""
            <div style="background:{color};border-radius:12px;padding:20px 24px;margin-bottom:4px;">
                <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#888;margin-bottom:8px;">DID YOU KNOW</div>
                <div style="font-size:20px;font-weight:700;color:#fff;margin-bottom:10px;">{title}</div>
                <div style="font-size:15px;color:#ccc;line-height:1.6;">{extract}</div>
            </div>
            """, unsafe_allow_html=True)
            col_a, col_b = st.columns([1, 1])
            with col_a:
                if url != "#":
                    st.markdown(f"[Read more on Wikipedia →]({url})")
            with col_b:
                if show_save:
                    if is_saved:
                        if st.button("★ Saved", key=f"unsave_{title}"):
                            del st.session_state["saved_articles"][title]
                            st.rerun()
                    else:
                        if st.button("☆ Save", key=f"save_{title}"):
                            if "saved_articles" not in st.session_state:
                                st.session_state["saved_articles"] = {}
                            st.session_state["saved_articles"][title] = article
                            st.rerun()
    else:
        st.markdown(f"""
        <div style="background:{color};border-radius:12px;padding:24px 28px;margin-bottom:4px;">
            <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#888;margin-bottom:8px;">DID YOU KNOW</div>
            <div style="font-size:22px;font-weight:700;color:#fff;margin-bottom:12px;">{title}</div>
            <div style="font-size:15px;color:#ccc;line-height:1.7;">{extract}</div>
        </div>
        """, unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if url != "#":
                st.markdown(f"[Read more on Wikipedia →]({url})")
        with col_b:
            if show_save:
                if is_saved:
                    if st.button("★ Saved", key=f"unsave_{title}"):
                        del st.session_state["saved_articles"][title]
                        st.rerun()
                else:
                    if st.button("☆ Save", key=f"save_{title}"):
                        if "saved_articles" not in st.session_state:
                            st.session_state["saved_articles"] = {}
                        st.session_state["saved_articles"][title] = article
                        st.rerun()

    st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)


def update_streak():
    today = str(datetime.date.today())
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    streak_data = st.session_state.get("streak", {"count": 0, "last": None})

    if streak_data["last"] == today:
        return streak_data["count"]
    elif streak_data["last"] == yesterday:
        streak_data["count"] += 1
    else:
        streak_data["count"] = 1

    streak_data["last"] = today
    st.session_state["streak"] = streak_data
    return streak_data["count"]


def render():
    today = datetime.date.today()
    day_seed = int(today.strftime("%Y%m%d"))
    streak = update_streak()

    # Header
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
        <div>
            <span style="font-size:32px;font-weight:800;">🧠 Daily Learning</span><br>
            <span style="color:#888;font-size:14px;">{today.strftime('%A, %B %d %Y')}</span>
        </div>
        <div style="text-align:center;background:#1e1e2e;border-radius:12px;padding:12px 20px;">
            <div style="font-size:28px;font-weight:800;color:#f59e0b;">🔥 {streak}</div>
            <div style="font-size:11px;color:#888;letter-spacing:1px;">DAY STREAK</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab_daily, tab_explore, tab_saved = st.tabs(["✨ Today's Picks", "🔍 Explore", "★ Saved"])

    with tab_daily:
        if "daily_articles" not in st.session_state or st.session_state.get("daily_date") != str(today):
            with st.spinner("Loading today's topics..."):
                st.session_state["daily_articles"] = get_daily_articles(day_seed)
                st.session_state["daily_date"] = str(today)

        articles = st.session_state.get("daily_articles", [])
        if articles:
            for i, art in enumerate(articles):
                render_card(art, idx=i)
        else:
            st.warning("Could not load articles. Try refreshing.")

        if st.button("🔄 Shuffle topics"):
            del st.session_state["daily_articles"]
            st.rerun()

    with tab_explore:
        cols = st.columns(5)
        selected_category = st.session_state.get("selected_category", CATEGORIES[0][1])
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
            st.markdown(f"### {emoji} {active}")
            if "explore_article" not in st.session_state:
                with st.spinner(f"Finding something about {active}..."):
                    art = fetch_wikipedia_article(active)
                    if not art:
                        rng = random.Random(day_seed + hash(active))
                        fallback = rng.choice(FALLBACK_FACTS)
                        art = dict(fallback) | {"thumbnail": None}
                    st.session_state["explore_article"] = art

            render_card(st.session_state["explore_article"], idx=2)

            if st.button("🔄 Find another"):
                st.session_state.pop("explore_article", None)
                st.rerun()

    with tab_saved:
        saved = st.session_state.get("saved_articles", {})
        if not saved:
            st.markdown("""
            <div style="text-align:center;padding:60px 0;color:#666;">
                <div style="font-size:48px;">★</div>
                <div style="font-size:18px;margin-top:12px;">No saved articles yet</div>
                <div style="font-size:14px;margin-top:4px;">Hit ☆ Save on any article to bookmark it here</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**{len(saved)} saved article{'s' if len(saved) != 1 else ''}**")
            for i, art in enumerate(saved.values()):
                render_card(art, idx=i)
