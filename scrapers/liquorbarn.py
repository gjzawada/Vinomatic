"""
Liquor Barn - tries their search API and HTML fallback.
"""
import logging, json, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.liquorbarn.com"
URLS = [
    BASE + "/wine?on_sale=true&sort=percent_discount_desc",
    BASE + "/collections/wine-sale",
    BASE + "/wine?sort=percent_discount_desc",
]

def scrape_liquorbarn() -> list:
    wines = []
    for url in URLS:
        html = get_page(url, ua_index=2)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[Liquor Barn] {url} -> {len(html):,} chars")

        # Check for Shopify JSON (common for liquor stores)
        for script in soup.find_all("script"):
            text = script.string or ""
            if "Shopify.products" in text or '"products"' in text:
                try:
                    m = re.search(r'"products"\s*:\s*(\[.+?\])', text, re.DOTALL)
                    if m:
                        items = json.loads(m.group(1))
                        for p in items[:30]:
                            name = p.get("title","") or p.get("name","")
                            if not name: continue
                            variant = (p.get("variants",[{}]) or [{}])[0]
                            price = float(variant.get("price",0) or 0)/100 or None  # Shopify prices in cents
                            orig  = float(variant.get("compare_at_price",0) or 0)/100 or None
                            if price and price > 1000: price = price/100  # already in dollars
                            if orig  and orig  > 1000: orig  = orig/100
                            image = p.get("featured_image","") or p.get("image","")
                            if image and not image.startswith("http"): image = "https:" + image
                            handle = p.get("handle","")
                            purl = f"{BASE}/products/{handle}" if handle else url
                            varietal, wine_type, country, region = infer_attributes(name)
                            wines.append(wine_stub(name=name, price=price, original_price=orig,
                                url=purl, image=image, source="Liquor Barn",
                                varietal=varietal, region=region, country=country, wine_type=wine_type))
                        if wines: return wines
                except Exception as e:
                    logger.debug(f"[Liquor Barn] Shopify: {e}")

        cards = (soup.select(".product-item") or soup.select("[class*='product-card']") or
                 soup.select("[class*='product-tile']") or soup.select("li[class*='product']") or
                 soup.select(".grid-item") or soup.select("article"))
        logger.info(f"[Liquor Barn] {len(cards)} cards")
        for card in cards[:30]:
            try:
                name_el = (card.select_one("[class*='title'] a") or card.select_one("[class*='name'] a") or
                           card.select_one("h2 a") or card.select_one("h3 a"))
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3: continue
                link_el = card.select_one("a[href]")
                purl = link_el["href"] if link_el else url
                if purl and not purl.startswith("http"): purl = BASE + purl
                sale_el = card.select_one("ins .amount, [class*='sale'], [class*='special']")
                orig_el = card.select_one("del .amount, [class*='regular'], [class*='compare']")
                any_p   = card.select_one("[class*='price']")
                price   = parse_price(sale_el.get_text() if sale_el else "")
                original= parse_price(orig_el.get_text() if orig_el else "")
                if not price and any_p: price = parse_price(any_p.get_text())
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                    elif image.startswith("/"): image = BASE + image
                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=purl, image=image, source="Liquor Barn",
                    varietal=varietal, region=region, country=country, wine_type=wine_type))
            except Exception as e:
                logger.debug(f"[Liquor Barn] {e}")
        if wines: break

    logger.info(f"[Liquor Barn] {len(wines)} wines")
    return wines
