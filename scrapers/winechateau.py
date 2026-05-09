"""
Wine Chateau - tries multiple URL patterns and selector strategies.
"""
import logging, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.winechateau.com"
URLS = [
    BASE + "/category+SALE_WINES&sort=new&view=72",
    BASE + "/wine-sale",
    BASE + "/clearance-wine",
]

def scrape_winechateau() -> list:
    wines = []
    for url in URLS:
        html = get_page(url, ua_index=2)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[Wine Chateau] {url} -> {len(html):,} chars")

        # Log top-level class names to help debug selectors
        classes = set()
        for el in soup.find_all(class_=True)[:100]:
            classes.update(el.get("class",[]))
        logger.info(f"[Wine Chateau] classes: {sorted(classes)[:20]}")

        cards = (soup.select("li.item") or soup.select("li.product-item") or
                 soup.select(".products-grid li") or soup.select("[class*='product-item']") or
                 soup.select("[class*='product-card']") or soup.select("[class*='wine-item']") or
                 soup.select("li[class*='item']"))
        logger.info(f"[Wine Chateau] {len(cards)} cards from {url}")
        if not cards: continue

        for card in cards[:40]:
            try:
                name_el = (card.select_one(".product-item-link") or card.select_one(".product-name a") or
                           card.select_one("[class*='name'] a") or card.select_one("h2 a") or card.select_one("h3 a"))
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3: continue

                link = name_el.get("href", url) if name_el else url
                if link and not link.startswith("http"): link = BASE + link

                sale_el = (card.select_one(".special-price .price") or card.select_one("[class*='special'] .price") or
                           card.select_one("[class*='sale'] .price"))
                orig_el = (card.select_one(".old-price .price") or card.select_one(".regular-price .price") or
                           card.select_one("[class*='old'] .price") or card.select_one("[class*='reg'] .price"))
                any_p   = card.select_one("[class*='price']")
                price   = parse_price(sale_el.get_text() if sale_el else "")
                original= parse_price(orig_el.get_text() if orig_el else "")
                if not price and any_p: price = parse_price(any_p.get_text())

                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                    elif image.startswith("/"): image = BASE + image

                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=link, image=image, source="Wine Chateau",
                    varietal=varietal, region=region, country=country, wine_type=wine_type))
            except Exception as e:
                logger.debug(f"[Wine Chateau] {e}")
        if wines: break

    logger.info(f"[Wine Chateau] {len(wines)} wines")
    return wines
