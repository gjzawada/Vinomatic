"""
WTSO - Wines Til Sold Out. Flash deal site.
"""
import logging
import json
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.wtso.com"


def scrape_wtso() -> list:
    wines = []
    html = get_page(BASE + "/", ua_index=1)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    # Try JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if data.get("@type") == "Product":
                name = data.get("name", "")
                offers = data.get("offers", {})
                price = float(offers.get("price", 0) or 0) or None
                image = data.get("image", "")
                if isinstance(image, list): image = image[0]
                desc = data.get("description", "")
                varietal, wine_type, country, region = infer_attributes(name + " " + desc)
                if name:
                    wines.append(wine_stub(
                        name=name, price=price, original_price=None,
                        url=BASE, image=image, source="WTSO",
                        varietal=varietal, region=region, country=country,
                        wine_type=wine_type, description=desc[:300],
                    ))
        except Exception:
            pass

    if wines:
        return wines

    # HTML fallback
    for card in soup.select(".deal-container, .product, .wine, article")[:10]:
        try:
            name_el = card.select_one("h1, h2, h3, [class*='name'], [class*='title']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                continue
            price_el = card.select_one("[class*='price'], [class*='cost']")
            price = parse_price(price_el.get_text() if price_el else "")
            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image
            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=None,
                url=BASE, image=image, source="WTSO",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[WTSO] card error: {e}")

    logger.info(f"[WTSO] {len(wines)} wines")
    return wines
