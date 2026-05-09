"""
Shared utilities for all scrapers.
"""
import httpx
import re
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_page(url: str, timeout: int = 15) -> str | None:
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def parse_price(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"[\$£€]?\s*([\d,]+\.?\d*)", text.replace(",", ""))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def calc_discount(original: float | None, sale: float | None) -> int:
    if original and sale and original > 0:
        return round((1 - sale / original) * 100)
    return 0


def wine_stub(
    name: str,
    price: float | None,
    original_price: float | None,
    url: str,
    image: str,
    source: str,
    varietal: str = "",
    region: str = "",
    country: str = "",
    wine_type: str = "",
    vintage: str = "",
    rating: float | None = None,
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
