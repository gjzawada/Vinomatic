"""
Wine Chateau - sale wines listing page.
Uses Magento-style HTML.
"""
import logging
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.winechateau.com"
SALE_URL = BASE + "/category+SALE_WINES&sort=new&view=72"


def scrape_winechateau() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=2)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    # Magento product list patterns
    cards = (
        soup.select("li.item.product") or
        soup.select(".products-grid li") or
        soup.select("[class*='product-item']") or
        soup.select("li[class*='item']")
    )

    logger.info(f"[Wine Chateau] {len(cards)} raw cards")

    for card in cards[:40]:
        try:
            name_el = card.select_one(".product-name a, .product-item-link, h2 a, h3 a")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            link = name_el.get("href", SALE_URL) if name_el else SALE_URL
            if link and not link.startswith("http"):
                link = BASE + link

            # Magento sale price structure
            price_el = (
                card.select_one(".special-price .price") or
                card.select_one("[class*='special'] .price") or
                card.select_one(".price-box .price")
            )
            orig_el = (
                card.select_one(".old-price .price") or
                card.select_one(".regular-price .price") or
                card.select_one("[class*='old'] .price")
            )
            price = parse_price(price_el.get_text() if price_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image
                if image.startswith("/"): image = BASE + image

            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=link, image=image, source="Wine Chateau",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[Wine Chateau] {e}")

    logger.info(f"[Wine Chateau] {len(wines)} wines parsed")
    return wines
