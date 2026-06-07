import streamlit as st
import requests
import datetime
import random

CATEGORIES = [
    "Science", "History", "Technology", "Mathematics", "Philosophy",
    "Biology", "Astronomy", "Psychology", "Economics", "Art",
    "Literature", "Music", "Geography", "Medicine", "Physics",
]

FALLBACK_FACTS = [
    {"title": "Honey never spoils", "extract": "Archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible. Honey's low moisture content and acidic pH make it inhospitable to bacteria and microorganisms.", "url": "https://en.wikipedia.org/wiki/Honey"},
    {"title": "Octopuses have three hearts", "extract": "Two hearts pump blood to the gills, while the third pumps it to the rest of the body. When an octopus swims, the heart that delivers blood to the body actually stops beating, which is why octopuses tire so quickly.", "url": "https://en.wikipedia.org/wiki/Octopus"},
    {"title": "A day on Venus is longer than a year on Venus", "extract": "Venus rotates so slowly that one full rotation (a day) takes 243 Earth days, while it only takes 225 Earth days to orbit the Sun (a year). Venus also rotates in the opposite direction to most planets.", "url": "https://en.wikipedia.org/wiki/Venus"},
    {"title": "The human brain uses about 20% of the body's energy", "extract": "Despite accounting for only about 2% of body weight, the brain consumes roughly 20% of the body's total energy. Most of this energy is used to fuel electrical signals sent between neurons.", "url": "https://en.wikipedia.org/wiki/Brain"},
    {"title": "Cleopatra lived closer in time to the Moon landing than to the Great Pyramid", "extract": "The Great Pyramid was built around 2560 BC. Cleopatra lived around 30 BC — about 2,500 years after the pyramid was built. The Moon landing was in 1969 AD, only about 2,000 years after Cleopatra.", "url": "https://en.wikipedia.org/wiki/Cleopatra"},
    {"title": "There are more possible chess games than atoms in the observable universe", "extract": "The number of possible unique chess games is estimated at 10^120 (the Shannon number), while the number of atoms in the observable universe is estimated at around 10^80. This astronomical complexity is why chess remains challenging even for computers.", "url": "https://en.wikipedia.org/wiki/Chess"},
    {"title": "Bananas are berries, but strawberries are not", "extract": "Botanically, a berry is a fruit developed from a single flower with one ovary. Bananas qualify. Strawberries develop from a flower with multiple ovaries, making them aggregate fruits — not true berries.", "url": "https://en.wikipedia.org/wiki/Berry_(botany)"},
    {"title": "The shortest war in history lasted 38 minutes", "extract": "The Anglo-Zanzibar War of 1896 is the shortest recorded war in history. It was fought between the United Kingdom and the Zanzibar Sultanate on August 27, 1896, and lasted between 38 and 45 minutes.", "url": "https://en.wikipedia.org/wiki/Anglo-Zanzibar_War"},
    {"title": "Water can boil and freeze at the same time", "extract": "This is called the triple point — the specific temperature and pressure at which a substance exists simultaneously as solid, liquid, and gas. For water, this occurs at exactly 0.01°C and 611.657 pascals.", "url": "https://en.wikipedia.org/wiki/Triple_point"},
    {"title": "Oxford University is older than the Aztec Empire", "extract": "Teaching at Oxford began around 1096 AD. The Aztec Empire was founded in 1428 AD — making Oxford over 300 years older than the Aztecs.", "url": "https://en.wikipedia.org/wiki/University_of_Oxford"},
    {"title": "Sharks are older than trees", "extract": "Sharks have existed for around 450 million years, while trees only evolved about 350 million years ago. Sharks predate trees by 100 million years and survived all five mass extinction events.", "url": "https://en.wikipedia.org/wiki/Shark"},
    {"title": "Nintendo was founded in 1889", "extract": "Long before video games, Nintendo was founded in Kyoto, Japan in 1889 to produce handmade playing cards called hanafuda. It didn't enter the video game industry until the 1970s.", "url": "https://en.wikipedia.org/wiki/Nintendo"},
]


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
    for _ in range(8):
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


def render_card(article: dict):
    st.markdown("---")
    thumbnail = article.get("thumbnail")
    if thumbnail:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(thumbnail, use_container_width=True)
        with col2:
            st.subheader(article["title"])
            st.write(article["extract"])
            if article.get("url", "#") != "#":
                st.markdown(f"[Read more on Wikipedia →]({article['url']})")
    else:
        st.subheader(article["title"])
        st.write(article["extract"])
        if article.get("url", "#") != "#":
            st.markdown(f"[Read more on Wikipedia →]({article['url']})")


def render():
    st.title("🧠 Daily Learning")
    st.caption("Something new to learn every day.")

    today = datetime.date.today()
    day_seed = int(today.strftime("%Y%m%d"))

    tab_daily, tab_explore = st.tabs(["Today's Picks", "Explore by Category"])

    with tab_daily:
        st.markdown(f"**{today.strftime('%A, %B %d %Y')}**")

        if "daily_articles" not in st.session_state or st.session_state.get("daily_date") != str(today):
            with st.spinner("Loading today's topics..."):
                st.session_state["daily_articles"] = get_daily_articles(day_seed)
                st.session_state["daily_date"] = str(today)

        articles = st.session_state.get("daily_articles", [])
        if articles:
            for art in articles:
                render_card(art)
        else:
            st.warning("Could not load articles. Try refreshing.")

        if st.button("🔄 Load different topics"):
            del st.session_state["daily_articles"]
            st.rerun()

    with tab_explore:
        category = st.selectbox("Pick a category", CATEGORIES)
        if st.button("Discover"):
            with st.spinner(f"Finding something about {category}..."):
                art = fetch_wikipedia_article(category)
                if not art:
                    rng = random.Random(day_seed + hash(category))
                    fallback = rng.choice(FALLBACK_FACTS)
                    art = dict(fallback) | {"thumbnail": None}
                st.session_state["explore_article"] = art

        if st.session_state.get("explore_article"):
            render_card(st.session_state["explore_article"])
