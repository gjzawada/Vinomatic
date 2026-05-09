"""
Total Wine & More - large national retailer.
Note: Total Wine uses heavy JS rendering; this scraper targets
their server-rendered sale page and JSON-LD data.
"""
import logging
import json
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.totalwine.com"
SALE_URL = BASE + "/wine/c/c0010?spiritsvolume=750mL&sortBy=savings&viewall=true"


def scrape_totalwine() -> list:
    wines = []
    html = get_page(SALE_URL, ua_index=1)
    if not html:
        return wines

    soup = BeautifulSoup(html, "lxml")

    # Total Wine embeds product data as JSON in script tags
    for script in soup.find_all("script"):
        text = script.string or ""
        if '"productName"' in text or '"skuPriceInfo"' in text:
            try:
                import re
                # Find JSON arrays of products
                m = re.search(r'"products"\s*:\s*(\[.+?\])\s*[,}]', text, re.DOTALL)
                if m:
                    products = json.loads(m.group(1))
                    for p in products[:30]:
                        name = p.get("productName", "") or p.get("name", "")
                        price_info = p.get("skuPriceInfo", {}) or {}
                        price = float(price_info.get("regularPrice", 0) or 0) or None
                        sale = float(price_info.get("salePrice", 0) or price_info.get("price", 0) or 0) or None
                        if sale and price and sale < price:
                            final_price, orig = sale, price
                        else:
                            final_price, orig = price, None
                        image = p.get("productImage", "") or p.get("image", "")
                        if image and not image.startswith("http"): image = BASE + image
                        slug = p.get("seoUrl", "") or p.get("url", "")
                        url = BASE + slug if slug else SALE_URL
                        varietal = p.get("varietal", "") or p.get("grape", "")
                        region = p.get("region", "")
                        country = p.get("country", "")
                        wine_type = p.get("wineType", "") or p.get("type", "")
                        rating_val = p.get("averageRating", None)
                        rating = float(rating_val) if rating_val else None
                        if name:
                            wines.append(wine_stub(
                                name=name, price=final_price, original_price=orig,
                                url=url, image=image, source="Total Wine",
                                varietal=varietal, region=region, country=country,
                                wine_type=wine_type, rating=rating,
                                rating_source="Total Wine",
                            ))
                    if wines:
                        return wines
            except Exception as e:
                logger.debug(f"[Total Wine] JSON: {e}")

    # HTML fallback
    cards = (
        soup.select("[class*='plp-product-card']") or
        soup.select("[class*='product-card']") or
        soup.select("[data-productid]") or
        soup.select(".product")
    )
    logger.info(f"[Total Wine] {len(cards)} HTML cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one("[class*='product-name'], [class*='title'], h2, h3")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name: continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else SALE_URL
            if url and not url.startswith("http"): url = BASE + url

            price_el = card.select_one("[class*='price-sale'], [class*='was'], [class*='regular']")
            sale_el = card.select_one("[class*='sale'], [class*='now'], [class*='current']")
            price = parse_price(sale_el.get_text() if sale_el else "")
            original = parse_price(price_el.get_text() if price_el else "")
            if not price:
                any_p = card.select_one("[class*='price']")
                price = parse_price(any_p.get_text() if any_p else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image.startswith("//"): image = "https:" + image

            varietal, wine_type, country, region = infer_attributes(name)
            wines.append(wine_stub(
                name=name, price=price, original_price=original,
                url=url, image=image, source="Total Wine",
                varietal=varietal, region=region, country=country, wine_type=wine_type,
            ))
        except Exception as e:
            logger.debug(f"[Total Wine] {e}")

    logger.info(f"[Total Wine] {len(wines)} wines")
    return wines
