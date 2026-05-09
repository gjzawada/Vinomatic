"""
WTSO - Wines Til Sold Out. Uses JSON-LD and RSS fallback.
"""
import logging, json, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.wtso.com"

def scrape_wtso() -> list:
    wines = []

    # WTSO exposes product data via JSON-LD on homepage
    for path in ["/", "/wines"]:
        html = get_page(BASE + path, ua_index=1)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for d in items:
                    if d.get("@type") != "Product": continue
                    name = d.get("name","")
                    if not name: continue
                    offers = d.get("offers", {})
                    price = float(offers.get("price",0) or 0) or None
                    image = d.get("image","")
                    if isinstance(image, list): image = image[0]
                    desc = d.get("description","")[:300]
                    varietal, wine_type, country, region = infer_attributes(name + " " + desc)
                    wines.append(wine_stub(name=name, price=price, original_price=None,
                        url=BASE, image=image, source="WTSO",
                        varietal=varietal, region=region, country=country, wine_type=wine_type, description=desc))
            except Exception: pass

        if wines:
            logger.info(f"[WTSO] {len(wines)} from JSON-LD")
            return wines

        # HTML fallback with broad selectors
        for card in soup.select("section, article, .deal, [class*='product'], [class*='wine']")[:15]:
            try:
                name_el = card.select_one("h1, h2, h3, [class*='title'], [class*='name']")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 5: continue
                price_el = card.select_one("[class*='price']")
                price = parse_price(price_el.get_text() if price_el else "")
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=None,
                    url=BASE, image=image, source="WTSO",
                    varietal=varietal, region=region, country=country, wine_type=wine_type))
            except Exception: pass
        if wines: break

    logger.info(f"[WTSO] {len(wines)} wines")
    return wines
