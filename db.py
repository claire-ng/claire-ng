import streamlit as st
from supabase import create_client, Client
import os

_client: Client | None = None


def _get_client() -> Client | None:
    global _client
    if _client:
        return _client
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    _client = create_client(url, key)
    return _client


def get_user_email() -> str | None:
    try:
        user = st.experimental_user
        return user.email if user and user.email else None
    except Exception:
        return None


# ── Watchlist ─────────────────────────────────────────────────────────────────

def load_watchlist(email: str) -> list[str]:
    db = _get_client()
    if not db or not email:
        return []
    try:
        res = db.table("watchlists").select("tickers").eq("email", email).execute()
        if res.data:
            return res.data[0]["tickers"] or []
        return []
    except Exception:
        return []


def save_watchlist(email: str, tickers: list[str]) -> None:
    db = _get_client()
    if not db or not email:
        return
    try:
        existing = db.table("watchlists").select("email").eq("email", email).execute()
        if existing.data:
            db.table("watchlists").update({"tickers": tickers}).eq("email", email).execute()
        else:
            db.table("watchlists").insert({"email": email, "tickers": tickers}).execute()
    except Exception:
        pass


# ── Portfolio ─────────────────────────────────────────────────────────────────

def load_positions(email: str) -> list[dict]:
    db = _get_client()
    if not db or not email:
        return []
    try:
        res = db.table("portfolio").select("ticker,shares,cost_basis").eq("email", email).execute()
        return res.data or []
    except Exception:
        return []


def save_position(email: str, ticker: str, shares: float, cost_basis: float) -> None:
    db = _get_client()
    if not db or not email:
        return
    try:
        existing = db.table("portfolio").select("id").eq("email", email).eq("ticker", ticker).execute()
        if existing.data:
            db.table("portfolio").update({"shares": shares, "cost_basis": cost_basis}).eq("email", email).eq("ticker", ticker).execute()
        else:
            db.table("portfolio").insert({"email": email, "ticker": ticker, "shares": shares, "cost_basis": cost_basis}).execute()
    except Exception:
        pass


def delete_position(email: str, ticker: str) -> None:
    db = _get_client()
    if not db or not email:
        return
    try:
        db.table("portfolio").delete().eq("email", email).eq("ticker", ticker).execute()
    except Exception:
        pass


# ── Saved articles ────────────────────────────────────────────────────────────

def load_saved_articles(email: str) -> dict[str, dict]:
    db = _get_client()
    if not db or not email:
        return {}
    try:
        res = db.table("saved_articles").select("title,extract,url").eq("email", email).execute()
        return {row["title"]: row for row in (res.data or [])}
    except Exception:
        return {}


def save_article(email: str, article: dict) -> None:
    db = _get_client()
    if not db or not email:
        return
    try:
        existing = db.table("saved_articles").select("id").eq("email", email).eq("title", article["title"]).execute()
        if not existing.data:
            db.table("saved_articles").insert({
                "email": email,
                "title": article["title"],
                "extract": article.get("extract", ""),
                "url": article.get("url", ""),
            }).execute()
    except Exception:
        pass


def delete_article(email: str, title: str) -> None:
    db = _get_client()
    if not db or not email:
        return
    try:
        db.table("saved_articles").delete().eq("email", email).eq("title", title).execute()
    except Exception:
        pass


# ── Streak ────────────────────────────────────────────────────────────────────

def get_streak(email: str) -> int:
    db = _get_client()
    if not db or not email:
        return st.session_state.get("streak", {}).get("count", 1)
    try:
        import datetime
        today = str(datetime.date.today())
        yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
        res = db.table("streaks").select("streak_count,last_visit").eq("email", email).execute()
        if res.data:
            row = res.data[0]
            last = row["last_visit"]
            count = row["streak_count"]
            if last == today:
                return count
            elif last == yesterday:
                count += 1
            else:
                count = 1
            db.table("streaks").update({"streak_count": count, "last_visit": today}).eq("email", email).execute()
            return count
        else:
            db.table("streaks").insert({"email": email, "streak_count": 1, "last_visit": today}).execute()
            return 1
    except Exception:
        return 1
