# 🍷 Vinomatic — Wine Deal Finder

A web app that crawls wine deal sites and lets you filter by varietal, region, country, price, and discount.

## Supported Sources

| Site | What's scraped |
|---|---|
| **Last Bottle** | Current flash deal |
| **WTSO** (Wines 'Til Sold Out) | Current flash deals |
| **Wine Chateau** | Sale wines listing |
| **Naked Wines** | On-sale wines |

> **Note on scrapers**: Wine sites change their HTML frequently. If a site returns 0 results, it likely needs a CSS selector update in `scrapers/<name>.py`. This is normal maintenance for any web scraper.

## Adding More Sites

Create a new file in `scrapers/`, e.g. `scrapers/casemates.py`:

```python
from scrapers import get_page, parse_price, wine_stub
from scrapers.lastbottle import _infer_attributes
from bs4 import BeautifulSoup

def scrape_casemates() -> list[dict]:
    wines = []
    html = get_page("https://www.casemates.com/deals")
    soup = BeautifulSoup(html, "html.parser")
    # ... parse cards ...
    return wines
```

Then register it in `app.py`:

```python
from scrapers.casemates import scrape_casemates
SCRAPERS = {
    ...
    "Casemates": scrape_casemates,
}
```

## Running Locally (Mac)

```bash
# 1. Clone / download this folder
cd wine-deals

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py

# 5. Open http://localhost:5050
```

## Deploying to Render (free tier)

1. Push this folder to a GitHub repo.
2. Go to [render.com](https://render.com) → New → Web Service.
3. Connect your repo — Render will auto-detect `render.yaml`.
4. Click **Deploy**. Your app will be live at `https://vinomatic.onrender.com` (or similar).

> **Free tier note**: Render spins down free services after 15 min of inactivity. First load after sleep takes ~30s.

## Filters Available

- **Sources**: toggle which sites to scrape
- **Wine Type**: Red, White, Rosé, Sparkling, Dessert
- **Price Range**: min / max dollar
- **Min Discount**: slider 0–80%
- **Varietal**: free text (e.g. "Pinot Noir")
- **Region**: free text (e.g. "Burgundy")
- **Country**: free text (e.g. "France")
- **Sort By**: Best Discount, Price ↑, Price ↓, Highest Rated

## Project Structure

```
wine-deals/
├── app.py                  # Flask app + filter logic
├── requirements.txt
├── render.yaml             # Render deployment config
├── scrapers/
│   ├── __init__.py         # Shared utilities (HTTP, parsing)
│   ├── lastbottle.py
│   ├── winechateau.py
│   ├── wtso.py
│   └── nakedwines.py
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```
