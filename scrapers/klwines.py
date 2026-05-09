"""
K&L Wine Merchants - SF Bay Area, excellent selection and deals.
"""
import logging
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.klwines.com"
SALE_URL = BASE + "/Products?&productTypeID=1&ms=5&order=1"  # ms=5 = on sale, order=1 = price low


def scrape_klwines() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=2)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    cards = (
        soup.select(".tf-product-container") or
        soup.select("[class*='product-result']") or
        soup.select(".result") or
        soup.select("[class*='wine-result']")
    )
    logger.info(f"[K&L] {len(cards)} cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one("a.header, .product-name a, h2 a, h3 a, [class*='name'] a")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name: continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else SALE_URL
            if url and not url.startswith("http"): url = BASE + url

            price_el = card.select_one(".price, [class*='price']")
            price = parse_price(price_el.get_text() if price_el else "")

            orig_el = card.select_one("[class*='was'], [class*='orig'], [class*='retail'], s")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image
                if image.startswith("/"): image = BASE + image

            desc_el = card.select_one(".tf-detail-text, .description, p")
            desc = desc_el.get_text(strip=True)[:200] if desc_el else ""

            varietal, wine_type, country, region = infer_attributes(name + " " + desc)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=url, image=image, source="K&L Wines",
                varietal=varietal, region=region, country=country,
                wine_type=wine_type, description=desc,
            ))
        except Exception as e:
            logger.debug(f"[K&L] {e}")

    logger.info(f"[K&L Wines] {len(wines)} wines")
    return wines
