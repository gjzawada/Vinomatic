"""
Naked Wines US - on-sale wines.
"""
import logging
import json
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://us.nakedwines.com"
SALE_URL = BASE + "/wines/all-wines-on-sale.htm"


def scrape_nakedwines() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=0)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    # Try JSON embedded product data first
    for script in soup.find_all("script"):
        text = script.string or ""
        if "window.__INITIAL_STATE__" in text or '"products"' in text:
            try:
                # Extract JSON blob
                import re
                m = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});', text, re.DOTALL)
                if m:
                    data = json.loads(m.group(1))
                    products = (
                        data.get("products", {}).get("items", []) or
                        data.get("catalog", {}).get("products", [])
                    )
                    for p in products[:30]:
                        name = p.get("name", "")
                        price = float(p.get("price", 0) or p.get("salePrice", 0) or 0) or None
                        orig = float(p.get("rrp", 0) or p.get("regularPrice", 0) or 0) or None
                        image = p.get("image", "") or p.get("imageUrl", "")
                        url = p.get("url", "") or SALE_URL
                        if url and not url.startswith("http"): url = BASE + url
                        varietal = p.get("grape", "") or p.get("varietal", "")
                        region = p.get("region", "")
                        country = p.get("country", "")
                        wine_type = p.get("wineType", "") or p.get("type", "")
                        rating = float(p.get("rating", 0) or 0) or None
                        if name:
                            wines.append(wine_stub(
                                name=name, price=price, original_price=orig,
                                url=url, image=image, source="Naked Wines",
                                varietal=varietal, region=region, country=country,
                                wine_type=wine_type, rating=rating,
                                rating_source="Naked Wines Community",
                            ))
                    if wines:
                        return wines
            except Exception as e:
                logger.debug(f"[Naked Wines] JSON parse: {e}")

    # HTML fallback
    cards = (
        soup.select(".product-grid__item") or
        soup.select("[class*='product-card']") or
        soup.select("[class*='wine-card']") or
        soup.select("li[class*='product']")
    )
    logger.info(f"[Naked Wines] {len(cards)} HTML cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one("h2, h3, [class*='name'], [class*='title']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else SALE_URL
            if url and not url.startswith("http"): url = BASE + url

            price_el = card.select_one("[class*='angel'], [class*='sale'], [class*='price']")
            orig_el = card.select_one("[class*='rrp'], [class*='regular'], [class*='was']")
            price = parse_price(price_el.get_text() if price_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image

            import re
            rating_el = card.select_one("[class*='rating'], [class*='score']")
            rating = None
            if rating_el:
                m = re.search(r"(\d+(?:\.\d+)?)", rating_el.get_text())
                if m: rating = float(m.group(1))

            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=url, image=image, source="Naked Wines",
                varietal=varietal, region=region, country=country,
                wine_type=wine_type, rating=rating,
                rating_source="Naked Wines Community",
            ))
        except Exception as e:
            logger.debug(f"[Naked Wines] {e}")

    logger.info(f"[Naked Wines] {len(wines)} wines")
    return wines
