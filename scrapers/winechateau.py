"""
Scraper for Wine Chateau (winechateau.com) — sale / deals page.
"""
import logging
from scrapers import get_page, parse_price, wine_stub
from scrapers.lastbottle import _infer_attributes
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEALS_URL = "https://www.winechateau.com/category+SALE_WINES"


def scrape_winechateau() -> list[dict]:
    wines = []
    html = get_page(DEALS_URL)
    if not html:
        return wines

    soup = BeautifulSoup(html, "html.parser")

    # Wine Chateau product cards
    cards = soup.select(".product-item, .product_item, li.item, .wine-item")
    if not cards:
        # fallback: try common e-commerce patterns
        cards = soup.select("li[class*='product'], div[class*='product-card']")

    logger.info(f"[Wine Chateau] found {len(cards)} cards")

    for card in cards[:30]:  # cap at 30
        try:
            name_el = card.select_one("a.product-name, .product-name, h2, h3, .name")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else DEALS_URL
            if url and not url.startswith("http"):
                url = "https://www.winechateau.com" + url

            price_el = card.select_one(".special-price .price, .sale-price, [class*='sale']")
            orig_el = card.select_one(".old-price .price, .regular-price, [class*='old']")
            price = parse_price(price_el.get_text() if price_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image and image.startswith("//"):
                    image = "https:" + image

            varietal, wine_type, country, region = _infer_attributes(name)

            wines.append(
                wine_stub(
                    name=name,
                    price=price,
                    original_price=original,
                    url=url,
                    image=image,
                    source="Wine Chateau",
                    varietal=varietal,
                    region=region,
                    country=country,
                    wine_type=wine_type,
                )
            )
        except Exception as e:
            logger.debug(f"[Wine Chateau] card parse error: {e}")

    return wines
