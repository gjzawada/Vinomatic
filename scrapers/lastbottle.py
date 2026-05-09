"""
Last Bottle Wines - flash sale, one deal at a time.
Their page is server-rendered and scraper-friendly.
"""
import logging
import re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.lastbottle.com"


def scrape_lastbottle() -> list:
    wines = []
    html = get_page(BASE + "/", ua_index=0)
    if not html:
        logger.warning("[Last Bottle] no HTML returned")
        return wines

    soup = BeautifulSoup(html, "lxml")

    # Last Bottle renders product data in multiple possible structures
    # Try JSON-LD first (most reliable)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if data.get("@type") in ("Product", "Offer"):
                name = data.get("name", "")
                price = float(data.get("offers", {}).get("price", 0) or 0) or None
                image = data.get("image", "")
                if isinstance(image, list):
                    image = image[0]
                desc = data.get("description", "")
                varietal, wine_type, country, region = infer_attributes(name + " " + desc)
                if name:
                    wines.append(wine_stub(
                        name=name, price=price, original_price=None,
                        url=BASE, image=image, source="Last Bottle",
                        varietal=varietal, region=region, country=country,
                        wine_type=wine_type, description=desc[:300],
                    ))
                    return wines
        except Exception:
            pass

    # Fallback: HTML parsing
    # Try multiple selector patterns
    selectors = [
        ("h1.wineTitle", ".salePrice", ".retailPrice", "img.wineImg"),
        ("h1[class*='wine']", "[class*='sale'][class*='price']", "[class*='retail'][class*='price']", "img"),
        ("h1", ".price", ".was", "img"),
    ]

    for name_sel, price_sel, orig_sel, img_sel in selectors:
        name_el = soup.select_one(name_sel)
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        price_el = soup.select_one(price_sel)
        orig_el = soup.select_one(orig_sel)
        img_el = soup.select_one(img_sel)

        price = parse_price(price_el.get_text() if price_el else "")
        original = parse_price(orig_el.get_text() if orig_el else "")
        image = ""
        if img_el:
            image = img_el.get("data-src") or img_el.get("src", "")
            if image.startswith("//"):
                image = "https:" + image

        desc_el = soup.select_one(".wineDescription, .description, [class*='desc']")
        desc = desc_el.get_text(strip=True)[:300] if desc_el else ""

        varietal, wine_type, country, region = infer_attributes(name + " " + desc)
        if name:
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=BASE, image=image, source="Last Bottle",
                varietal=varietal, region=region, country=country,
                wine_type=wine_type, description=desc,
            ))
            break

    logger.info(f"[Last Bottle] {len(wines)} wines")
    return wines
