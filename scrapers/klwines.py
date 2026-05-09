"""K&L Wine Merchants - SF Bay Area."""
import logging
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.klwines.com"
URLS = [
    BASE + "/Products?&productTypeID=1&ms=5&order=1",  # on sale wines
    BASE + "/Products?&productTypeID=1&ms=5",
]

def scrape_klwines() -> list:
    wines = []
    for url in URLS:
        html = get_page(url, ua_index=2)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[K&L] {url} -> {len(html)} chars")

        cards = (soup.select(".tf-product-container") or soup.select(".result") or
                 soup.select("[class*='product-result']") or soup.select("[class*='wine-result']") or
                 soup.select("li[class*='result']") or soup.select(".search-result"))
        logger.info(f"[K&L] {len(cards)} cards")
        if not cards: continue

        for card in cards[:30]:
            try:
                name_el = (card.select_one("a.header") or card.select_one(".product-name a") or
                           card.select_one("h2 a") or card.select_one("h3 a") or
                           card.select_one("[class*='name'] a") or card.select_one("a[href*='/Products/']"))
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3: continue
                link_el = card.select_one("a[href]")
                purl = link_el["href"] if link_el else url
                if purl and not purl.startswith("http"): purl = BASE + purl
                price_el = card.select_one(".price,[class*='price']")
                orig_el  = card.select_one("[class*='was'],[class*='orig'],[class*='retail'],s,del")
                price    = parse_price(price_el.get_text() if price_el else "")
                original = parse_price(orig_el.get_text() if orig_el else "")
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                    elif image.startswith("/"): image = BASE + image
                desc_el = card.select_one(".tf-detail-text,.description,p")
                desc = desc_el.get_text(strip=True)[:200] if desc_el else ""
                varietal, wine_type, country, region = infer_attributes(name + " " + desc)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=purl, image=image, source="K&L Wines",
                    varietal=varietal, region=region, country=country, wine_type=wine_type, description=desc))
            except Exception as e:
                logger.debug(f"[K&L] {e}")
        if wines: break
    logger.info(f"[K&L] total: {len(wines)}")
    return wines
