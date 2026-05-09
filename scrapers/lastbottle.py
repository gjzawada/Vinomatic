"""
Scraper for Last Bottle Wines (lastbottle.com)
Flash-sale site — one deal at a time, but it exposes a simple JSON endpoint.
"""
import logging
from scrapers import get_page, parse_price, wine_stub
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def scrape_lastbottle() -> list[dict]:
    wines = []

    # Last Bottle shows the current deal on the homepage
    html = get_page("https://www.lastbottle.com/")
    if not html:
        return wines

    soup = BeautifulSoup(html, "html.parser")

    try:
        # Product name
        name_el = soup.select_one("h1.product-name, .wine-name, h1")
        name = name_el.get_text(strip=True) if name_el else "Unknown Wine"

        # Price
        price_el = soup.select_one(".sale-price, .price-sale, [class*='sale']")
        orig_el = soup.select_one(".original-price, .price-orig, [class*='orig']")
        price = parse_price(price_el.get_text() if price_el else "")
        original = parse_price(orig_el.get_text() if orig_el else "")

        # Image
        img_el = soup.select_one("img.product-image, .wine-image img, .product img")
        image = img_el.get("src", "") if img_el else ""
        if image and image.startswith("//"):
            image = "https:" + image

        # Description / varietal hints
        desc_el = soup.select_one(".product-description, .description, .wine-desc")
        description = desc_el.get_text(strip=True)[:300] if desc_el else ""

        # Try to sniff varietal/type from the name
        varietal, wine_type, country, region = _infer_attributes(name + " " + description)

        if name and name != "Unknown Wine":
            wines.append(
                wine_stub(
                    name=name,
                    price=price,
                    original_price=original,
                    url="https://www.lastbottle.com/",
                    image=image,
                    source="Last Bottle",
                    varietal=varietal,
                    region=region,
                    country=country,
                    wine_type=wine_type,
                    description=description,
                )
            )
    except Exception as e:
        logger.warning(f"[Last Bottle] parse error: {e}")

    return wines


def _infer_attributes(text: str):
    text_lower = text.lower()
    varietal = ""
    wine_type = ""
    country = ""
    region = ""

    varietals = [
        "cabernet sauvignon", "pinot noir", "chardonnay", "sauvignon blanc",
        "merlot", "syrah", "shiraz", "zinfandel", "malbec", "tempranillo",
        "riesling", "grenache", "sangiovese", "nebbiolo", "barbera",
        "petite sirah", "viognier", "roussanne", "marsanne", "chenin blanc",
        "gewurztraminer", "pinot gris", "pinot grigio", "moscato", "prosecco",
        "champagne", "cabernet franc", "petit verdot", "carmenere",
    ]
    for v in varietals:
        if v in text_lower:
            varietal = v.title()
            break

    if any(w in text_lower for w in ["red", "rouge", "tinto", "rosso"]):
        wine_type = "Red"
    elif any(w in text_lower for w in ["white", "blanc", "bianco", "blanco"]):
        wine_type = "White"
    elif "rosé" in text_lower or "rose" in text_lower:
        wine_type = "Rosé"
    elif "sparkling" in text_lower or "champagne" in text_lower or "prosecco" in text_lower:
        wine_type = "Sparkling"
    elif "dessert" in text_lower or "port" in text_lower or "sauternes" in text_lower:
        wine_type = "Dessert"

    countries = ["france", "italy", "spain", "usa", "argentina", "chile",
                 "australia", "new zealand", "germany", "portugal", "austria",
                 "south africa", "greece", "israel"]
    for c in countries:
        if c in text_lower:
            country = c.title()
            break

    regions = [
        "bordeaux", "burgundy", "rhône", "rhone", "loire", "alsace", "champagne",
        "napa", "sonoma", "willamette", "paso robles", "mendocino",
        "tuscany", "piedmont", "veneto", "sicily", "rioja", "priorat",
        "ribera del duero", "mendoza", "marlborough", "barossa", "mosel",
        "douro", "alentejo",
    ]
    for r in regions:
        if r in text_lower:
            region = r.title()
            break

    return varietal, wine_type, country, region
