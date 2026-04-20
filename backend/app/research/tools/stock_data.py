import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import yfinance as yf
import requests
from langchain_core.tools import tool

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com/",
    "Origin": "https://finance.yahoo.com",
}


def _fetch_yahoo_chart(ticker: str) -> dict:
    """
    Call the Yahoo Finance v8 chart endpoint directly with cookie+crumb auth.
    This works from Docker where the yfinance library session gets blocked.
    """
    session = requests.Session()
    session.headers.update(_BROWSER_HEADERS)

    # Step 1: fetch a cookie by hitting the quote page
    session.get(f"https://finance.yahoo.com/quote/{ticker}", timeout=10)

    # Step 2: get a crumb token
    crumb_resp = session.get(
        "https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=10
    )
    crumb = crumb_resp.text.strip()
    if not crumb or "<" in crumb:
        raise ValueError("Could not obtain Yahoo Finance crumb")

    # Step 3: fetch 1-month chart data
    end = int(datetime.utcnow().timestamp())
    start = int((datetime.utcnow() - timedelta(days=35)).timestamp())
    chart_url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={start}&period2={end}&interval=1d&crumb={crumb}"
    )
    resp = session.get(chart_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    result = data.get("chart", {}).get("result", [])
    if not result:
        raise ValueError(f"No chart data returned for {ticker}")

    chart = result[0]
    meta = chart.get("meta", {})
    timestamps = chart.get("timestamp", [])
    closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    volumes = chart.get("indicators", {}).get("quote", [{}])[0].get("volume", [])

    historical_prices = []
    for ts, close, vol in zip(timestamps, closes, volumes):
        if close is None:
            continue
        historical_prices.append({
            "date": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
            "close": round(float(close), 2),
            "volume": int(vol) if vol else 0,
        })

    if not historical_prices:
        raise ValueError(f"No price data found for ticker: {ticker}")

    current_price = meta.get("regularMarketPrice") or historical_prices[-1]["close"]

    return {
        "ticker": ticker.upper(),
        "company_name": meta.get("longName") or meta.get("shortName") or ticker,
        "current_price": current_price,
        "market_cap": None,
        "pe_ratio": None,
        "forward_pe": None,
        "revenue": None,
        "profit_margin": None,
        "dividend_yield": None,
        "52_week_high": meta.get("fiftyTwoWeekHigh"),
        "52_week_low": meta.get("fiftyTwoWeekLow"),
        "sector": None,
        "industry": None,
        "historical_prices": historical_prices[-5:],
        "source": "yahoo_chart",
    }


def _fetch_from_yfinance(ticker: str) -> dict:
    """Fetch stock data from yfinance library as primary attempt."""
    try:
        session = requests.Session()
        session.headers.update(_BROWSER_HEADERS)
        stock = yf.Ticker(ticker, session=session)

        hist = stock.history(period="1mo")
        if hist.empty:
            raise ValueError(f"No price data found for ticker: {ticker}")

        historical_prices = []
        for date, row in hist.iterrows():
            historical_prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        current_price = historical_prices[-1]["close"] if historical_prices else None

        market_cap = year_high = year_low = None
        try:
            fast = stock.fast_info
            market_cap = getattr(fast, "market_cap", None)
            year_high = getattr(fast, "year_high", None)
            year_low = getattr(fast, "year_low", None)
        except Exception:
            pass

        info: dict = {}
        try:
            fetched = stock.info
            if isinstance(fetched, dict) and fetched:
                info = fetched
        except Exception:
            pass

        return {
            "ticker": ticker.upper(),
            "company_name": info.get("longName", info.get("shortName", ticker)),
            "current_price": info.get("regularMarketPrice", info.get("currentPrice", current_price)),
            "market_cap": info.get("marketCap", market_cap),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "revenue": info.get("totalRevenue"),
            "profit_margin": info.get("profitMargins"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high": info.get("fiftyTwoWeekHigh", year_high),
            "52_week_low": info.get("fiftyTwoWeekLow", year_low),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "historical_prices": historical_prices[-5:],
            "source": "yfinance",
        }
    except Exception as e:
        logger.debug(f"yfinance library error for {ticker}: {e}")
        raise


def _fetch_from_fmp(ticker: str) -> dict:
    """Fetch stock data from Financial Modeling Prep (fallback)."""
    api_key = settings.FMP_API_KEY
    if not api_key:
        raise ValueError("FMP_API_KEY not configured")

    base_url = "https://financialmodelingprep.com/api/v3"

    # Get quote
    quote_url = f"{base_url}/quote/{ticker}?apikey={api_key}"
    resp = requests.get(quote_url, timeout=10)
    resp.raise_for_status()
    quotes = resp.json()

    if not quotes:
        raise ValueError(f"No FMP data found for ticker: {ticker}")

    quote = quotes[0]

    # Get historical prices
    hist_url = f"{base_url}/historical-price-full/{ticker}?timeseries=5&apikey={api_key}"
    hist_resp = requests.get(hist_url, timeout=10)
    hist_data = hist_resp.json()
    historical_prices = []
    if "historical" in hist_data:
        for entry in hist_data["historical"][:5]:
            historical_prices.append({
                "date": entry["date"],
                "close": entry["close"],
                "volume": entry["volume"],
            })

    return {
        "ticker": ticker.upper(),
        "company_name": quote.get("name", ticker),
        "current_price": quote.get("price"),
        "market_cap": quote.get("marketCap"),
        "pe_ratio": quote.get("pe"),
        "revenue": None,  # Not in quote endpoint
        "sector": None,
        "industry": None,
        "historical_prices": historical_prices,
        "source": "financial_modeling_prep",
    }


@tool
def get_stock_data(ticker: str) -> str:
    """
    Fetch comprehensive stock data for a given ticker symbol.
    Returns current price, market cap, P/E ratio, revenue, historical prices, and company info.
    Use this when you need financial data about a specific stock or company.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
    """
    try:
        data = _fetch_from_yfinance(ticker)
        return json.dumps(data, default=str)
    except Exception as e:
        logger.warning(f"yfinance library failed for {ticker}: {e}. Trying direct Yahoo chart API.")
        try:
            data = _fetch_yahoo_chart(ticker)
            return json.dumps(data, default=str)
        except Exception as e2:
            logger.warning(f"Yahoo chart API failed for {ticker}: {e2}. Trying FMP fallback.")
            try:
                data = _fetch_from_fmp(ticker)
                return json.dumps(data, default=str)
            except Exception as e3:
                logger.error(f"All data sources failed for {ticker}: {e3}")
                return json.dumps({
                    "error": True,
                    "message": f"Unable to fetch stock data for {ticker} at this time",
                    "ticker": ticker,
                })
