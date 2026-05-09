"""
Liquor Barn - Kentucky-based retailer with online sales.
"""
import logging
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.liquorbarn.com"
SALE_URL = BASE + "/wine?on_sale=true&sort=percent_discount_desc"


def scrape_liquorbarn() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=2)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    cards = (
        soup.select(".product-item") or
        soup.select("[class*='product-card']") or
        soup.select("[class*='product-tile']") or
        soup.select("li[class*='product']")
    )
    logger.info(f"[Liquor Barn] {len(cards)} cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one("a[class*='name'], .product-title, h2 a, h3 a, [class*='title'] a")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name: continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else SALE_URL
            if url and not url.startswith("http"): url = BASE + url

            price_el = card.select_one("[class*='sale-price'], [class*='special'], ins .amount")
            orig_el = card.select_one("[class*='regular-price'], [class*='original'], del .amount")
            any_p = card.select_one("[class*='price']")

            price = parse_price(price_el.get_text() if price_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")
            if not price and any_p:
                price = parse_price(any_p.get_text())

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image
                if image.startswith("/"): image = BASE + image

            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=url, image=image, source="Liquor Barn",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[Liquor Barn] {e}")

    logger.info(f"[Liquor Barn] {len(wines)} wines")
    return wines
