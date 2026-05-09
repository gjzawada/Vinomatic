/* Vinomatic — app.js */

const grid = document.getElementById("wineGrid");
const loadingState = document.getElementById("loadingState");
const emptyState = document.getElementById("emptyState");
const errorState = document.getElementById("errorState");
const dealCount = document.getElementById("deal-count");
const refreshBtn = document.getElementById("refreshBtn");
const discountSlider = document.getElementById("discountSlider");
const discountVal = document.getElementById("discountVal");

// Discount slider live update
discountSlider.addEventListener("input", () => {
  discountVal.textContent = discountSlider.value + "%+";
});

// Pill filter (wine type)
document.querySelectorAll("#typeFilter .pill").forEach(pill => {
  pill.addEventListener("click", () => {
    document.querySelectorAll("#typeFilter .pill").forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
  });
});

function getFilters() {
  const sources = Array.from(document.querySelectorAll(".source-check:checked"))
    .map(el => el.value);
  const wine_type = document.querySelector("#typeFilter .pill.active")?.dataset.value || "";
  const min_price = document.getElementById("minPrice").value;
  const max_price = document.getElementById("maxPrice").value;
  const min_discount = discountSlider.value;
  const varietal = document.getElementById("varietalInput").value;
  const region = document.getElementById("regionInput").value;
  const country = document.getElementById("countryInput").value;
  const sort_by = document.getElementById("sortBy").value;

  const params = new URLSearchParams();
  sources.forEach(s => params.append("sources", s));
  if (wine_type) params.set("wine_type", wine_type);
  if (min_price) params.set("min_price", min_price);
  if (max_price) params.set("max_price", max_price);
  if (min_discount > 0) params.set("min_discount", min_discount);
  if (varietal) params.set("varietal", varietal);
  if (region) params.set("region", region);
  if (country) params.set("country", country);
  params.set("sort_by", sort_by);
  return params;
}

function clearFilters() {
  document.querySelectorAll(".source-check").forEach(el => el.checked = true);
  document.querySelectorAll("#typeFilter .pill").forEach(p => p.classList.remove("active"));
  document.querySelector('#typeFilter .pill[data-value=""]').classList.add("active");
  document.getElementById("minPrice").value = "";
  document.getElementById("maxPrice").value = "";
  discountSlider.value = 0;
  discountVal.textContent = "0%+";
  document.getElementById("varietalInput").value = "";
  document.getElementById("regionInput").value = "";
  document.getElementById("countryInput").value = "";
  document.getElementById("sortBy").value = "discount";
  fetchWines();
}

function showState(state) {
  loadingState.classList.add("hidden");
  emptyState.classList.add("hidden");
  errorState.classList.add("hidden");
  grid.innerHTML = "";
  if (state === "loading") loadingState.classList.remove("hidden");
  if (state === "empty") emptyState.classList.remove("hidden");
  if (state === "error") errorState.classList.remove("hidden");
}

const tpl = document.getElementById("wineCardTpl");

function renderWines(wines) {
  grid.innerHTML = "";
  if (!wines.length) { showState("empty"); return; }

  wines.forEach((w, i) => {
    const card = tpl.content.cloneNode(true).querySelector(".wine-card");
    card.style.animationDelay = `${i * 0.04}s`;

    const link = card.querySelector(".card-link");
    link.href = w.url || "#";

    // Image
    const img = card.querySelector(".card-image");
    if (w.image) {
      img.src = w.image;
      img.alt = w.name;
      img.onerror = () => {
        img.style.display = "none";
        const ph = document.createElement("span");
        ph.className = "card-image-placeholder";
        ph.textContent = typeIcon(w.type);
        img.parentNode.appendChild(ph);
      };
    } else {
      img.style.display = "none";
      const ph = document.createElement("span");
      ph.className = "card-image-placeholder";
      ph.textContent = typeIcon(w.type);
      img.parentNode.appendChild(ph);
    }

    // Badge
    const badge = card.querySelector(".discount-badge");
    if (w.discount_pct > 0) {
      badge.textContent = `–${w.discount_pct}%`;
    } else {
      badge.style.display = "none";
    }

    card.querySelector(".card-source").textContent = w.source || "";
    card.querySelector(".card-name").textContent = w.name || "Unknown Wine";

    const varEl = card.querySelector(".card-varietal");
    const regEl = card.querySelector(".card-region");
    if (w.varietal) varEl.textContent = w.varietal;
    else varEl.style.display = "none";
    if (w.region) regEl.textContent = w.region;
    else regEl.style.display = "none";

    const priceEl = card.querySelector(".card-price");
    const origEl = card.querySelector(".card-original");
    if (w.price != null) {
      priceEl.textContent = `$${w.price.toFixed(2)}`;
    } else {
      priceEl.textContent = "See site";
    }
    if (w.original_price && w.original_price > (w.price || 0)) {
      origEl.textContent = `$${w.original_price.toFixed(2)}`;
    } else {
      origEl.style.display = "none";
    }

    const ratingEl = card.querySelector(".card-rating");
    if (w.rating) {
      ratingEl.classList.remove("hidden");
      card.querySelector(".rating-val").textContent = w.rating.toFixed(1);
    }

    grid.appendChild(card);
  });
}

function typeIcon(type) {
  if (!type) return "🍷";
  const t = type.toLowerCase();
  if (t === "red") return "🍷";
  if (t === "white") return "🥂";
  if (t === "rosé" || t === "rose") return "🌸";
  if (t === "sparkling") return "🍾";
  if (t === "dessert") return "🍯";
  return "🍷";
}

async function fetchWines() {
  showState("loading");
  refreshBtn.classList.add("loading");
  dealCount.textContent = "Loading…";

  const params = getFilters();
  try {
    const res = await fetch(`/api/wines?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const wines = data.wines || [];
    dealCount.textContent = `${wines.length} deal${wines.length !== 1 ? "s" : ""} found`;
    renderWines(wines);
  } catch (err) {
    console.error("Fetch error:", err);
    showState("error");
    dealCount.textContent = "Error";
  } finally {
    refreshBtn.classList.remove("loading");
  }
}

// Kick off on load
fetchWines();
