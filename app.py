from flask import Flask, render_template, jsonify, request
from scrapers.lastbottle import scrape_lastbottle
from scrapers.winechateau import scrape_winechateau
from scrapers.wtso import scrape_wtso
from scrapers.nakedwines import scrape_nakedwines
from scrapers.binnys import scrape_binnys
from scrapers.totalwine import scrape_totalwine
from scrapers.liquorbarn import scrape_liquorbarn
from scrapers.winecom import scrape_winecom
from scrapers.klwines import scrape_klwines
from scrapers.wineaccess import scrape_wineaccess
import concurrent.futures
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

SCRAPERS = {
    "Last Bottle":  scrape_lastbottle,
    "WTSO":         scrape_wtso,
    "Wine.com":     scrape_winecom,
    "Total Wine":   scrape_totalwine,
    "Binny's":      scrape_binnys,
    "Naked Wines":  scrape_nakedwines,
    "K&L Wines":    scrape_klwines,
    "Wine Chateau": scrape_winechateau,
    "Liquor Barn":  scrape_liquorbarn,
    "Wine Access":  scrape_wineaccess,
}


def run_scrapers(selected_sources=None):
    results = []
    sources = selected_sources if selected_sources else list(SCRAPERS.keys())

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(SCRAPERS[name]): name
            for name in sources
            if name in SCRAPERS
        }
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                wines = future.result(timeout=25)
                results.extend(wines)
                logger.info(f"[{name}] {len(wines)} wines returned")
            except Exception as e:
                logger.warning(f"[{name}] failed: {e}")

    return results


@app.route("/")
def index():
    return render_template("index.html", sources=list(SCRAPERS.keys()))


@app.route("/api/wines")
def get_wines():
    selected = request.args.getlist("sources")
    wines = run_scrapers(selected if selected else None)

    varietal  = request.args.get("varietal", "").lower()
    region    = request.args.get("region", "").lower()
    country   = request.args.get("country", "").lower()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    min_disc  = request.args.get("min_discount", type=int)
    wine_type = request.args.get("wine_type", "").lower()
    sort_by   = request.args.get("sort_by", "discount")

    filtered = []
    for w in wines:
        if varietal and varietal not in (w.get("varietal") or "").lower():
            continue
        if region and region not in (w.get("region") or "").lower():
            continue
        if country and country not in (w.get("country") or "").lower():
            continue
        if wine_type and wine_type not in (w.get("type") or "").lower():
            continue
        price = w.get("price")
        if price is not None:
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
        if min_disc is not None and (w.get("discount_pct") or 0) < min_disc:
            continue
        filtered.append(w)

    if sort_by == "price_asc":
        filtered.sort(key=lambda x: x.get("price") or 9999)
    elif sort_by == "price_desc":
        filtered.sort(key=lambda x: x.get("price") or 0, reverse=True)
    elif sort_by == "discount":
        filtered.sort(key=lambda x: x.get("discount_pct") or 0, reverse=True)
    elif sort_by == "rating":
        filtered.sort(key=lambda x: x.get("rating") or 0, reverse=True)

    return jsonify({"wines": filtered, "total": len(filtered)})


@app.route("/api/sources")
def get_sources():
    return jsonify({"sources": list(SCRAPERS.keys())})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
