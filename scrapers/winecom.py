"""
Wine.com - largest US online wine retailer.
Uses their search API which is more reliable than HTML scraping.
"""
import logging, json, re
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://www.wine.com"

# Wine.com has a public catalog API
API_URL = BASE + "/api/product/list/?categoryId=7155&sortBy=savings&rows=50&start=0"

def scrape_winecom() -> list:
    wines = []

    # Try their catalog API first
    html = get_page(API_URL, ua_index=0)
    if html and html.strip().startswith("{"):
        try:
            data = json.loads(html)
            products = (data.get("products", {}).get("list", []) or
                       data.get("catalog", {}).get("products", []) or
                       data.get("items", []))
            for p in products[:40]:
                name = p.get("name","")
                if not name: continue
                price = float(p.get("priceMin",0) or p.get("price",0) or 0) or None
                orig  = float(p.get("retailPrice",0) or p.get("regularPrice",0) or 0) or None
                image = p.get("bottleShot","") or p.get("image","")
                if image and not image.startswith("http"): image = "https:" + image
                slug  = p.get("productUrl","") or p.get("url","")
                url   = BASE + slug if slug else BASE
                varietal = p.get("varietal",""); region = p.get("region","")
                country  = p.get("country","");  wine_type = p.get("type","")
                rating   = float(p.get("rating",0) or 0) or None
                if not varietal: varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=orig,
                    url=url, image=image, source="Wine.com",
                    varietal=varietal, region=region, country=country,
                    wine_type=wine_type, rating=rating, rating_source="Wine.com"))
            if wines:
                logger.info(f"[Wine.com] {len(wines)} from API")
                return wines
        except Exception as e:
            logger.debug(f"[Wine.com] API parse: {e}")

    # HTML fallback
    for url in [BASE + "/list/wine/7155?sortBy=savings", BASE + "/wine/c/c0010"]:
        html = get_page(url, ua_index=0)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[Wine.com] {url} -> {len(html):,} chars")

        # Try embedded JSON
        for script in soup.find_all("script"):
            text = script.string or ""
            if "catalogItems" in text or "productData" in text or '"products"' in text:
                try:
                    m = re.search(r'(?:catalogItems|products)["\s:]+(\[.+?\])\s*[,;}\]]', text, re.DOTALL)
                    if m:
                        items = json.loads(m.group(1))
                        for item in items[:30]:
                            name = item.get("name","")
                            if not name: continue
                            price = float(item.get("price",0) or item.get("salePrice",0) or 0) or None
                            orig  = float(item.get("retailPrice",0) or 0) or None
                            image = item.get("bottleShot","") or item.get("image","")
                            if image and not image.startswith("http"): image = "https:" + image
                            slug  = item.get("productUrl","") or item.get("url","")
                            purl  = BASE + slug if slug else url
                            varietal, wine_type, country, region = infer_attributes(name)
                            wines.append(wine_stub(name=name, price=price, original_price=orig,
                                url=purl, image=image, source="Wine.com",
                                varietal=varietal, region=region, country=country, wine_type=wine_type))
                        if wines: return wines
                except Exception as e:
                    logger.debug(f"[Wine.com] embedded JSON: {e}")

        cards = (soup.select(".prodItemWrap") or soup.select("[class*='product-item']") or
                 soup.select(".plpWineCard") or soup.select("[data-wine-id]") or
                 soup.select("[class*='product-card']"))
        for card in cards[:30]:
            try:
                name_el = (card.select_one(".prodItemName a") or card.select_one("[class*='name'] a") or
                           card.select_one("h2 a") or card.select_one("h3 a"))
                name = name_el.get_text(strip=True) if name_el else ""
                if not name: continue
                link_el = card.select_one("a[href]")
                purl = link_el["href"] if link_el else url
                if purl and not purl.startswith("http"): purl = BASE + purl
                price_el = card.select_one("[class*='sale'],[class*='price']")
                orig_el  = card.select_one("[class*='reg'],[class*='was']")
                price    = parse_price(price_el.get_text() if price_el else "")
                original = parse_price(orig_el.get_text() if orig_el else "")
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=purl, image=image, source="Wine.com",
                    varietal=varietal, region=region, country=country, wine_type=wine_type))
            except Exception as e:
                logger.debug(f"[Wine.com] {e}")
        if wines: break

    logger.info(f"[Wine.com] {len(wines)} wines")
    return wines
