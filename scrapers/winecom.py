"""
Wine.com - largest US online wine retailer.
They have a well-structured sale page.
"""
import logging
import json
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.wine.com"
SALE_URL = BASE + "/list/wine/7155?sortBy=savings"


def scrape_winecom() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=0)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    # wine.com embeds catalog JSON
    for script in soup.find_all("script"):
        text = script.string or ""
        if "catalogItems" in text or "productData" in text:
            try:
                import re
                m = re.search(r'catalogItems["\s:]+(\[.+?\])\s*[,;]', text, re.DOTALL)
                if not m:
                    m = re.search(r'"products"\s*:\s*(\[.+?\])', text, re.DOTALL)
                if m:
                    items = json.loads(m.group(1))
                    for item in items[:30]:
                        name = item.get("name", "")
                        price = float(item.get("price", 0) or item.get("salePrice", 0) or 0) or None
                        orig = float(item.get("retailPrice", 0) or item.get("regularPrice", 0) or 0) or None
                        image = item.get("bottleShot", "") or item.get("image", "")
                        if image and not image.startswith("http"): image = "https:" + image
                        slug = item.get("productUrl", "") or item.get("url", "")
                        url = BASE + slug if slug else SALE_URL
                        varietal = item.get("varietal", "")
                        region = item.get("region", "")
                        country = item.get("country", "")
                        wine_type = item.get("type", "")
                        rating = float(item.get("rating", 0) or 0) or None
                        if name:
                            wines.append(wine_stub(
                                name=name, price=price, original_price=orig,
                                url=url, image=image, source="Wine.com",
                                varietal=varietal, region=region, country=country,
                                wine_type=wine_type, rating=rating,
                                rating_source="Wine.com",
                            ))
                    if wines: return wines
            except Exception as e:
                logger.debug(f"[Wine.com] JSON: {e}")

    # HTML fallback
    cards = (
        soup.select(".prodItemWrap") or
        soup.select("[class*='product-item']") or
        soup.select(".plpWineCard") or
        soup.select("[data-wine-id]")
    )
    logger.info(f"[Wine.com] {len(cards)} HTML cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one(".prodItemName a, .wine-name a, h2 a, [class*='name'] a")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name: continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else SALE_URL
            if url and not url.startswith("http"): url = BASE + url

            price_el = card.select_one(".prodItemSale, [class*='sale-price'], .regPrice")
            orig_el = card.select_one(".regPrice, [class*='reg-price'], [class*='was']")
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
                url=url, image=image, source="Wine.com",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[Wine.com] {e}")

    logger.info(f"[Wine.com] {len(wines)} wines")
    return wines
