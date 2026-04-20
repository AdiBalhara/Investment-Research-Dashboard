import json
import logging
import time
from typing import Optional

import requests
from langchain_core.tools import tool

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_news_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = 0  # Disabled cache temporarily


def _get_cached(query: str) -> Optional[list]:
    """Get cached news results if still valid."""
    cache_key = query.lower().strip()
    if cache_key in _news_cache:
        entry = _news_cache[cache_key]
        if time.time() - entry["timestamp"] < CACHE_TTL_SECONDS:
            return entry["data"]
        else:
            del _news_cache[cache_key]
    return None


def _set_cache(query: str, data: list):
    """Cache news results."""
    cache_key = query.lower().strip()
    _news_cache[cache_key] = {
        "data": data,
        "timestamp": time.time(),
    }


@tool
def search_news(query: str) -> str:
    """
    Search for recent financial news articles about a company, ticker, or topic.
    Returns articles with title, source, URL, date, and description.
    Use this when you need recent news, market sentiment, or current events about a company.
    
    Args:
        query: Search query (e.g., "Apple earnings", "TSLA stock news", "tech sector outlook")
    """
    # Check cache first
    cached = _get_cached(query)
    if cached is not None:
        return json.dumps({"articles": cached, "cached": True, "query": query})

    api_key = settings.NEWS_API_KEY
    if not api_key:
        return json.dumps({
            "articles": [],
            "query": query,
            "message": "News API key not configured. Unable to fetch news.",
        })

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 4,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "description": article.get("description", "")[:150] + "...",
                "sentiment": "neutral",  # Will be enriched by AI agent
            })

        # Cache the results
        _set_cache(query, articles)

        return json.dumps({"articles": articles, "cached": False, "query": query})

    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI request failed: {e}")
        return json.dumps({
            "articles": [],
            "query": query,
            "message": f"Failed to fetch news: {str(e)}",
        })
