"""
Scraper for Naked Wines (nakedwines.com) — on-sale / deals section.
"""
import logging
from scrapers import get_page, parse_price, wine_stub
from scrapers.lastbottle import _infer_attributes
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

DEALS_URL = "https://us.nakedwines.com/wines/all-wines-on-sale.htm"


def scrape_nakedwines() -> list[dict]:
    wines = []
    html = get_page(DEALS_URL)
    if not html:
        return wines

    soup = BeautifulSoup(html, "html.parser")

    # Naked Wines product grid
    cards = soup.select(".product-grid__item, .product-card, [class*='product-item']")
    if not cards:
        cards = soup.select("li[class*='wine'], div[class*='wine-card']")

    logger.info(f"[Naked Wines] found {len(cards)} cards")

    for card in cards[:30]:
        try:
            name_el = card.select_one("h2, h3, .product-name, [class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else DEALS_URL
            if url and not url.startswith("http"):
                url = "https://us.nakedwines.com" + url

            price_el = card.select_one("[class*='sale-price'], [class*='angel-price'], .price")
            orig_el = card.select_one("[class*='rrp'], [class*='regular'], [class*='was']")
            price = parse_price(price_el.get_text() if price_el else "")
            original = parse_price(orig_el.get_text() if orig_el else "")

            img_el = card.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")
                if image and image.startswith("//"):
                    image = "https:" + image

            # Naked Wines often includes varietal/region in subheadings
            sub_el = card.select_one(".product-subtitle, .varietal, [class*='sub']")
            sub_text = sub_el.get_text(strip=True) if sub_el else ""

            # Rating
            rating_el = card.select_one("[class*='rating'], [class*='score']")
            rating_text = rating_el.get_text(strip=True) if rating_el else ""
            rating_match = re.search(r"(\d+(?:\.\d+)?)", rating_text)
            rating = float(rating_match.group(1)) if rating_match else None

            varietal, wine_type, country, region = _infer_attributes(name + " " + sub_text)

            wines.append(
                wine_stub(
                    name=name,
                    price=price,
                    original_price=original,
                    url=url,
                    image=image,
                    source="Naked Wines",
                    varietal=varietal,
                    region=region,
                    country=country,
                    wine_type=wine_type,
                    rating=rating,
                    rating_source="Naked Wines Community",
                    description=sub_text,
                )
            )
        except Exception as e:
            logger.debug(f"[Naked Wines] card error: {e}")

    return wines
