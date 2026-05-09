"""
Shared utilities for all scrapers.
Compatible with Python 3.9+
"""
from typing import Optional
import httpx
import re
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

def _headers(ua_index: int = 0) -> dict:
    return {
        "User-Agent": USER_AGENTS[ua_index % len(USER_AGENTS)],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }

HEADERS = _headers(0)


def get_page(url: str, timeout: int = 20, ua_index: int = 0) -> Optional[str]:
    try:
        with httpx.Client(
            headers=_headers(ua_index),
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            r = client.get(url)
            r.raise_for_status()
            if len(r.text) < 500:
                logger.warning(f"Suspiciously short response ({len(r.text)} chars) from {url}")
                return None
            return r.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = text.replace(",", "").replace(" ", "")
    match = re.search(r"\$?([\d]+\.?\d*)", cleaned)
    if match:
        try:
            val = float(match.group(1))
            if 1 <= val <= 5000:
                return val
        except ValueError:
            pass
    return None


def calc_discount(original: Optional[float], sale: Optional[float]) -> int:
    if original and sale and original > 0 and sale < original:
        return round((1 - sale / original) * 100)
    return 0


def wine_stub(
    name: str,
    price: Optional[float],
    original_price: Optional[float],
    url: str,
    image: str,
    source: str,
    varietal: str = "",
    region: str = "",
    country: str = "",
    wine_type: str = "",
    vintage: str = "",
    rating: Optional[float] = None,
    rating_source: str = "",
    description: str = "",
) -> dict:
    return {
        "name": name,
        "price": price,
        "original_price": original_price,
        "discount_pct": calc_discount(original_price, price),
        "url": url,
        "image": image,
        "source": source,
        "varietal": varietal,
        "region": region,
        "country": country,
        "type": wine_type,
        "vintage": vintage,
        "rating": rating,
        "rating_source": rating_source,
        "description": description,
    }


VARIETALS = [
    "cabernet sauvignon", "pinot noir", "chardonnay", "sauvignon blanc",
    "merlot", "syrah", "shiraz", "zinfandel", "malbec", "tempranillo",
    "riesling", "pinot grigio", "pinot gris", "moscato", "prosecco",
    "grenache", "sangiovese", "nebbiolo", "barbera", "viognier",
    "gewurztraminer", "chenin blanc", "cabernet franc", "petite sirah",
    "carmenere", "petit verdot",
]

COUNTRIES = [
    "france", "italy", "spain", "usa", "united states", "argentina",
    "chile", "australia", "new zealand", "germany", "portugal", "austria",
    "south africa", "greece", "israel", "hungary",
]

REGIONS = [
    "bordeaux", "burgundy", "champagne", "rhone", "rhone", "loire",
    "alsace", "provence", "languedoc",
    "napa", "napa valley", "sonoma", "willamette", "paso robles",
    "anderson valley", "santa barbara", "central coast",
    "tuscany", "piedmont", "veneto", "sicily", "barolo", "chianti",
    "rioja", "priorat", "ribera del duero", "rias baixas",
    "mendoza", "marlborough", "barossa", "hunter valley",
    "mosel", "rheingau", "douro", "alentejo", "walla walla",
]

WHITE_VARIETALS = {
    "Chardonnay", "Sauvignon Blanc", "Pinot Grigio", "Pinot Gris",
    "Riesling", "Moscato", "Prosecco", "Viognier", "Gewurztraminer",
    "Chenin Blanc",
}


def infer_attributes(text: str):
    t = text.lower()

    varietal = ""
    for v in VARIETALS:
        if v in t:
            varietal = v.title()
            break

    wine_type = ""
    if any(w in t for w in ["sparkling", "champagne", "prosecco", "cava", "cremant", "pet nat"]):
        wine_type = "Sparkling"
    elif any(w in t for w in ["rose wine", "rosato", "rosado", "rose"]) and "rosemary" not in t:
        wine_type = "Rose"
    elif any(w in t for w in ["dessert wine", "port wine", "porto", "sauternes", "late harvest", "tokaj"]):
        wine_type = "Dessert"
    elif any(w in t for w in ["white wine", "blanc", "bianco", "blanco", "weiss"]):
        wine_type = "White"
    elif any(w in t for w in ["red wine", "rouge", "rosso", "tinto"]):
        wine_type = "Red"
    if not wine_type and varietal:
        wine_type = "White" if varietal in WHITE_VARIETALS else "Red"

    country = ""
    for c in COUNTRIES:
        if c in t:
            country = "USA" if c in ("usa", "united states") else c.title()
            break

    region = ""
    for r in REGIONS:
        if r in t:
            region = r.title()
            break

    return varietal, wine_type, country, region
