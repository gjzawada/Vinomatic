"""
Last Bottle - uses their RSS feed which bypasses bot protection.
"""
import logging, json, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.lastbottle.com"

def scrape_lastbottle() -> list:
    wines = []

    # Try RSS feed first - much more reliable than HTML scraping
    rss = get_page(BASE + "/rss.php", ua_index=0)
    if rss and len(rss) > 500:
        soup = BeautifulSoup(rss, "xml")
        for item in soup.find_all("item")[:20]:
            try:
                name = (item.find("title") or item.find("name") or BeautifulSoup("","xml")).get_text(strip=True)
                url  = (item.find("link") or item.find("url") or BeautifulSoup("","xml")).get_text(strip=True)
                desc_el = item.find("description") or item.find("summary")
                desc = BeautifulSoup(desc_el.get_text() if desc_el else "", "lxml").get_text(strip=True)[:300]

                # Extract price from description
                price_match = re.search(r'\$(\d+(?:\.\d+)?)', desc)
                price = float(price_match.group(1)) if price_match else None

                orig_match = re.search(r'(?:retail|was|value)[:\s]+\$(\d+(?:\.\d+)?)', desc, re.I)
                original = float(orig_match.group(1)) if orig_match else None

                img_el = item.find("enclosure") or item.find("media:content") or item.find("image")
                image = img_el.get("url","") if img_el else ""

                if not name or len(name) < 3: continue
                varietal, wine_type, country, region = infer_attributes(name + " " + desc)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=url or BASE, image=image, source="Last Bottle",
                    varietal=varietal, region=region, country=country, wine_type=wine_type, description=desc))
            except Exception as e:
                logger.debug(f"[Last Bottle] RSS item: {e}")

    if wines:
        logger.info(f"[Last Bottle] {len(wines)} from RSS")
        return wines

    # Fallback: try JSON-LD on homepage
    html = get_page(BASE + "/", ua_index=0)
    if not html: return wines
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list): data = data[0]
            if data.get("@type") in ("Product","Offer"):
                name = data.get("name","")
                offers = data.get("offers", {})
                price = float(offers.get("price", 0) or 0) or None
                image = data.get("image","")
                if isinstance(image, list): image = image[0]
                desc = data.get("description","")[:300]
                varietal, wine_type, country, region = infer_attributes(name + " " + desc)
                if name:
                    wines.append(wine_stub(name=name, price=price, original_price=None,
                        url=BASE, image=image, source="Last Bottle",
                        varietal=varietal, region=region, country=country, wine_type=wine_type, description=desc))
                    return wines
        except Exception: pass

    logger.info(f"[Last Bottle] {len(wines)} wines")
    return wines
