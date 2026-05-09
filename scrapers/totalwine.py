"""Total Wine & More."""
import logging, json, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.totalwine.com"
URLS = [
    BASE + "/wine/c/c0010?sortBy=savings&viewall=true",
    BASE + "/wine/red-wine/c/c001001?sortBy=savings",
]

def scrape_totalwine() -> list:
    wines = []
    for url in URLS:
        html = get_page(url, ua_index=1)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[Total Wine] {url} -> {len(html)} chars")

        # Try JSON blobs in scripts
        for script in soup.find_all("script"):
            text = script.string or ""
            if len(text) < 50: continue
            for pattern in [r'"products"\s*:\s*(\[.+?\])\s*[,}]',
                            r'catalogItems["\s:]+(\[.+?\])\s*[,;]',
                            r'window\.__data__\s*=\s*(\{.+?\});']:
                try:
                    m = re.search(pattern, text, re.DOTALL)
                    if not m: continue
                    blob = json.loads(m.group(1))
                    items = blob if isinstance(blob, list) else blob.get("products", [])
                    for p in items[:30]:
                        name = p.get("name","") or p.get("productName","")
                        if not name: continue
                        price = float(p.get("price",0) or p.get("salePrice",0) or 0) or None
                        orig  = float(p.get("regularPrice",0) or p.get("retailPrice",0) or 0) or None
                        image = p.get("image","") or p.get("productImage","")
                        slug  = p.get("url","") or p.get("seoUrl","")
                        purl  = BASE + slug if slug else url
                        varietal = p.get("varietal",""); region = p.get("region","")
                        country  = p.get("country","");  wine_type = p.get("type","")
                        if not varietal: varietal, wine_type, country, region = infer_attributes(name)
                        wines.append(wine_stub(name=name, price=price, original_price=orig,
                            url=purl, image=image, source="Total Wine",
                            varietal=varietal, region=region, country=country, wine_type=wine_type))
                    if wines: return wines
                except Exception as e:
                    logger.debug(f"[Total Wine] JSON: {e}")

        # HTML fallback - broad selectors
        cards = (soup.select("[class*='plp-product']") or soup.select("[class*='product-card']") or
                 soup.select("[data-product-id]") or soup.select("[data-sku]") or
                 soup.select("li[class*='product']") or soup.select(".product"))
        logger.info(f"[Total Wine] {len(cards)} HTML cards")
        for card in cards[:30]:
            try:
                name_el = (card.select_one("[class*='product-name']") or card.select_one("[class*='title']") or
                           card.select_one("h2") or card.select_one("h3"))
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3: continue
                link_el = card.select_one("a[href]")
                purl = (link_el["href"] if link_el else url)
                if purl and not purl.startswith("http"): purl = BASE + purl
                price_el = card.select_one("[class*='sale'],[class*='now'],[class*='current']")
                orig_el  = card.select_one("[class*='was'],[class*='regular'],[class*='orig']")
                any_p    = card.select_one("[class*='price']")
                price    = parse_price(price_el.get_text() if price_el else "")
                original = parse_price(orig_el.get_text() if orig_el else "")
                if not price and any_p: price = parse_price(any_p.get_text())
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=purl, image=image, source="Total Wine",
                    varietal=varietal, region=region, country=country, wine_type=wine_type))
            except Exception as e:
                logger.debug(f"[Total Wine] {e}")
        if wines: break
    logger.info(f"[Total Wine] total: {len(wines)}")
    return wines
