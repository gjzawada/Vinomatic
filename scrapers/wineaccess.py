"""
Wine Access - curated selection, good deals.
"""
import logging
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.wineaccess.com"
SALE_URL = BASE + "/store/search?type=wine&on_sale=1&sort=savings_desc"


def scrape_wineaccess() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=1)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    cards = (
        soup.select(".wine-card") or
        soup.select("[class*='product-card']") or
        soup.select("[class*='wine-item']") or
        soup.select(".product")
    )
    logger.info(f"[Wine Access] {len(cards)} cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one("h2, h3, [class*='name'], [class*='title']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name: continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else SALE_URL
            if url and not url.startswith("http"): url = BASE + url

            price_el = card.select_one("[class*='sale'], [class*='price']")
            orig_el = card.select_one("[class*='regular'], [class*='was'], [class*='orig']")
            price = parse_price(price_el.get_text() if price_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image

            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=url, image=image, source="Wine Access",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[Wine Access] {e}")

    logger.info(f"[Wine Access] {len(wines)} wines")
    return wines
