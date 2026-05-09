"""
Binny's - tries their search API and multiple URL patterns.
"""
import logging, json, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.binnys.com"

URLS = [
    BASE + "/wine/?pf_t_tag=on_sale&view=72",
    BASE + "/wine/?sort=discount_desc",
    BASE + "/wine/red-wine/?pf_t_tag=on_sale",
]

def scrape_binnys() -> list:
    wines = []
    for url in URLS:
        html = get_page(url, ua_index=0)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[Binny's] {url} -> {len(html):,} chars")

        # Check for JSON data embedded in page
        for script in soup.find_all("script"):
            text = script.string or ""
            if '"products"' in text or '"items"' in text:
                try:
                    m = re.search(r'"(?:products|items)"\s*:\s*(\[.+?\])\s*[,}]', text, re.DOTALL)
                    if m:
                        items = json.loads(m.group(1))
                        for p in items[:30]:
                            name = p.get("name","") or p.get("title","")
                            if not name: continue
                            price = float(p.get("price",0) or p.get("salePrice",0) or 0) or None
                            orig  = float(p.get("regularPrice",0) or p.get("comparePrice",0) or 0) or None
                            image = p.get("image","") or p.get("thumbnail","")
                            if image and not image.startswith("http"): image = BASE + image
                            purl  = p.get("url","") or p.get("productUrl","")
                            if purl and not purl.startswith("http"): purl = BASE + purl
                            varietal, wine_type, country, region = infer_attributes(name)
                            wines.append(wine_stub(name=name, price=price, original_price=orig,
                                url=purl or url, image=image, source="Binny's",
                                varietal=varietal, region=region, country=country, wine_type=wine_type))
                        if wines: return wines
                except Exception as e:
                    logger.debug(f"[Binny's] JSON: {e}")

        cards = (soup.select("li.item") or soup.select(".product-item") or
                 soup.select("[class*='product-card']") or soup.select("[class*='product-tile']") or
                 soup.select("li[class*='item']") or soup.select("article"))

        logger.info(f"[Binny's] {len(cards)} cards")
        for card in cards[:40]:
            try:
                name_el = (card.select_one(".product-item-link") or card.select_one("a.product-name") or
                           card.select_one("[class*='name'] a") or card.select_one("h2 a") or
                           card.select_one("h3 a") or card.select_one("a[href*='/wine/']"))
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3: continue
                link = name_el.get("href", url) if name_el else url
                if link and not link.startswith("http"): link = BASE + link
                sale_el = (card.select_one(".special-price .price") or card.select_one("[class*='sale'] .price"))
                orig_el = (card.select_one(".old-price .price") or card.select_one("[class*='regular'] .price"))
                any_p   = card.select_one("[class*='price']")
                price   = parse_price(sale_el.get_text() if sale_el else "")
                original= parse_price(orig_el.get_text() if orig_el else "")
                if not price and any_p: price = parse_price(any_p.get_text())
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("data-lazy") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                    elif image.startswith("/"): image = BASE + image
                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=link, image=image, source="Binny's",
                    varietal=varietal, region=region, country=country, wine_type=wine_type))
            except Exception as e:
                logger.debug(f"[Binny's] {e}")
        if wines: break

    logger.info(f"[Binny's] {len(wines)} wines")
    return wines
