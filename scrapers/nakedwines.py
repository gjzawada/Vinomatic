"""
Naked Wines - uses their public API endpoint.
"""
import logging, json
from bs4 import BeautifulSoup
from scrapers import get_page, parse_price, wine_stub, infer_attributes

logger = logging.getLogger(__name__)
BASE = "https://us.nakedwines.com"

# Naked Wines has a public JSON API for their catalog
API_URLS = [
    BASE + "/api/wines?on_sale=true&page_size=48&sort=savings",
    BASE + "/api/v2/wines?on_sale=true&per_page=48",
    BASE + "/wines/all-wines-on-sale.htm",
]

def scrape_nakedwines() -> list:
    wines = []

    for url in API_URLS:
        html = get_page(url, ua_index=0)
        if not html: continue

        # Try JSON response
        if html.strip().startswith("{") or html.strip().startswith("["):
            try:
                data = json.loads(html)
                products = (data if isinstance(data, list) else
                           data.get("wines", data.get("products", data.get("items", []))))
                for p in products[:40]:
                    name = p.get("name","") or p.get("title","")
                    if not name: continue
                    price = float(p.get("angel_price",0) or p.get("price",0) or p.get("sale_price",0) or 0) or None
                    orig  = float(p.get("rrp",0) or p.get("regular_price",0) or p.get("retail_price",0) or 0) or None
                    image = p.get("image","") or p.get("image_url","") or p.get("bottle_image","")
                    if image and not image.startswith("http"): image = "https:" + image
                    slug  = p.get("url","") or p.get("product_url","") or p.get("path","")
                    purl  = BASE + slug if slug and not slug.startswith("http") else (slug or BASE)
                    varietal   = p.get("grape","") or p.get("varietal","")
                    region     = p.get("region","")
                    country    = p.get("country","")
                    wine_type  = p.get("wine_type","") or p.get("type","") or p.get("colour","")
                    rating     = float(p.get("rating",0) or p.get("average_rating",0) or 0) or None
                    if not varietal: varietal, wine_type, country, region = infer_attributes(name)
                    wines.append(wine_stub(name=name, price=price, original_price=orig,
                        url=purl, image=image, source="Naked Wines",
                        varietal=varietal, region=region, country=country,
                        wine_type=wine_type, rating=rating, rating_source="Naked Wines"))
                if wines:
                    logger.info(f"[Naked Wines] {len(wines)} from API")
                    return wines
            except Exception as e:
                logger.debug(f"[Naked Wines] JSON: {e}")

        # HTML fallback
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"[Naked Wines] HTML {url} -> {len(html):,} chars")

        # Check for next.js / React embedded data
        for script in soup.find_all("script", id="__NEXT_DATA__"):
            try:
                data = json.loads(script.string or "")
                # Navigate the Next.js page props
                props = data.get("props",{}).get("pageProps",{})
                products = (props.get("wines",[]) or props.get("products",[]) or
                           props.get("initialData",{}).get("wines",[]))
                for p in products[:40]:
                    name = p.get("name","")
                    if not name: continue
                    price = float(p.get("angelPrice",0) or p.get("price",0) or 0) or None
                    orig  = float(p.get("rrp",0) or p.get("regularPrice",0) or 0) or None
                    image = p.get("image","") or p.get("bottleImage","")
                    slug  = p.get("url","") or ""
                    purl  = BASE + slug if slug and not slug.startswith("http") else (slug or BASE)
                    varietal  = p.get("grape","") or p.get("varietal","")
                    region    = p.get("region","")
                    country   = p.get("country","")
                    wine_type = p.get("wineType","") or p.get("colour","")
                    rating    = float(p.get("rating",0) or 0) or None
                    if not varietal: varietal, wine_type, country, region = infer_attributes(name)
                    wines.append(wine_stub(name=name, price=price, original_price=orig,
                        url=purl, image=image, source="Naked Wines",
                        varietal=varietal, region=region, country=country,
                        wine_type=wine_type, rating=rating, rating_source="Naked Wines"))
                if wines: return wines
            except Exception as e:
                logger.debug(f"[Naked Wines] Next.js: {e}")

        cards = (soup.select(".product-grid__item") or soup.select("[class*='product-card']") or
                 soup.select("[class*='wine-card']") or soup.select("li[class*='product']"))
        for card in cards[:30]:
            try:
                name_el = card.select_one("h2, h3, [class*='name'], [class*='title']")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name: continue
                link_el = card.select_one("a[href]")
                purl = link_el["href"] if link_el else BASE
                if purl and not purl.startswith("http"): purl = BASE + purl
                price_el = card.select_one("[class*='angel'],[class*='sale'],[class*='price']")
                orig_el  = card.select_one("[class*='rrp'],[class*='regular'],[class*='was']")
                price    = parse_price(price_el.get_text() if price_el else "")
                original = parse_price(orig_el.get_text() if orig_el else "")
                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src","")
                    if image.startswith("//"): image = "https:" + image
                varietal, wine_type, country, region = infer_attributes(name)
                wines.append(wine_stub(name=name, price=price, original_price=original,
                    url=purl, image=image, source="Naked Wines",
                    varietal=varietal, region=region, country=country, wine_type=wine_type,
                    rating_source="Naked Wines"))
            except Exception as e:
                logger.debug(f"[Naked Wines] {e}")
        if wines: break

    logger.info(f"[Naked Wines] {len(wines)} wines")
    return wines
