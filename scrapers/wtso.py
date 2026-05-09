"""
Scraper for WTSO - Wines 'Til Sold Out (wtso.com)
Flash deals site — typically one or two deals live at a time.
"""
import logging
from scrapers import get_page, parse_price, wine_stub
from scrapers.lastbottle import _infer_attributes
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def scrape_wtso() -> list[dict]:
    wines = []
    html = get_page("https://www.wtso.com/")
    if not html:
        return wines

    soup = BeautifulSoup(html, "html.parser")

    # WTSO typically shows flash deals prominently
    deal_sections = soup.select(".deal, .product, .wine-deal, [class*='deal'], [class*='flash']")
    if not deal_sections:
        deal_sections = soup.select("article, .item")

    logger.info(f"[WTSO] found {len(deal_sections)} deal elements")

    for card in deal_sections[:20]:
        try:
            name_el = card.select_one("h1, h2, h3, .title, .name, [class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 4:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else "https://www.wtso.com"
            if url and not url.startswith("http"):
                url = "https://www.wtso.com" + url

            price_el = card.select_one(".price, [class*='price']")
            price = parse_price(price_el.get_text() if price_el else "")

            orig_el = card.select_one("[class*='orig'], [class*='retail'], [class*='was'], [class*='msrp']")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image and image.startswith("//"):
                    image = "https:" + image

            desc_el = card.select_one(".description, p")
            description = desc_el.get_text(strip=True)[:300] if desc_el else ""

            varietal, wine_type, country, region = _infer_attributes(name + " " + description)

            wines.append(
                wine_stub(
                    name=name,
                    price=price,
                    original_price=original,
                    url=url,
                    image=image,
                    source="WTSO",
                    varietal=varietal,
                    region=region,
                    country=country,
                    wine_type=wine_type,
                    description=description,
                )
            )
        except Exception as e:
            logger.debug(f"[WTSO] card error: {e}")

    return wines
