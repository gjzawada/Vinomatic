"""
Binny's Beverage Depot - Chicago-based, great deals page.
Uses a tag-based filter URL.
"""
import logging
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.binnys.com"
SALE_URL = BASE + "/wine/?pf_t_tag=on_sale&view=72"


def scrape_binnys() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=0)
    if not html:
        logger.warning("[Binny's] no HTML")
        return wines

    soup = BeautifulSoup(html, "lxml")

    cards = (
        soup.select(".product-item") or
        soup.select("[class*='product-card']") or
        soup.select("li[class*='item']") or
        soup.select(".grid-item")
    )
    logger.info(f"[Binny's] {len(cards)} cards")

    for card in cards[:40]:
        try:
            name_el = card.select_one(".product-item-link, .product-name a, h2 a, h3 a, a[class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            link = name_el.get("href", SALE_URL) if name_el else SALE_URL
            if link and not link.startswith("http"): link = BASE + link

            sale_el = card.select_one(".special-price .price, [class*='sale-price'], [class*='special'] .price")
            orig_el = card.select_one(".old-price .price, [class*='was-price'], [class*='regular'] .price")
            # Fallback to any price
            any_price_el = card.select_one(".price, [class*='price']")

            price = parse_price(sale_el.get_text() if sale_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")
            if not price and any_price_el:
                price = parse_price(any_price_el.get_text())

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-lazy") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image
                if image.startswith("/"): image = BASE + image

            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=link, image=image, source="Binny's",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[Binny's] {e}")

    logger.info(f"[Binny's] {len(wines)} wines")
    return wines
