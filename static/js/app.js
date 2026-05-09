/* Vinomatic — app.js */

// ── State ─────────────────────────────────────────────────────────────────────
let savedUrls   = new Set();
let allWines    = [];   // full result set, filtered client-side for snappiness

// ── Elements ──────────────────────────────────────────────────────────────────
const grid            = document.getElementById("wineGrid");
const loadingState    = document.getElementById("loadingState");
const emptyState      = document.getElementById("emptyState");
const errorState      = document.getElementById("errorState");
const dealCount       = document.getElementById("deal-count");
const refreshBtn      = document.getElementById("refreshBtn");
const discountSlider  = document.getElementById("discountSlider");
const discountVal     = document.getElementById("discountVal");
const sourceStatus    = document.getElementById("sourceStatus");
const wishlistDrawer  = document.getElementById("wishlistDrawer");
const wishlistOverlay = document.getElementById("wishlistOverlay");
const wishlistBadge   = document.getElementById("wishlistBadge");
const wishlistGroups  = document.getElementById("wishlistGroups");
const wishlistEmpty   = document.getElementById("wishlistEmpty");
const wishlistFooter  = document.getElementById("wishlistFooter");

// ── Checklist helpers ─────────────────────────────────────────────────────────
function buildChecklist(listId, values) {
  /** values: array of {value, count} sorted by count desc */
  const el = document.getElementById(listId);
  if (!values.length) { el.innerHTML = '<div class="checklist-empty">None in results</div>'; return; }
  el.innerHTML = values.map(({value, count}) => `
    <label class="checklist-item">
      <input type="checkbox" class="${listId}-check" value="${value}">
      <span class="check-box"></span>
      <span class="check-label" title="${value}">${value}</span>
      <span class="check-count">${count}</span>
    </label>`).join("");
}

function filterChecklist(listId, query) {
  const q = query.toLowerCase();
  document.querySelectorAll(`#${listId} .checklist-item`).forEach(item => {
    const label = item.querySelector(".check-label").textContent.toLowerCase();
    item.classList.toggle("hidden-item", q.length > 0 && !label.includes(q));
  });
}

function getChecked(listId) {
  return Array.from(document.querySelectorAll(`#${listId} .checklist-item input:checked`))
              .map(el => el.value.toLowerCase());
}

function populateChecklists(wines) {
  const count = (arr, key) => {
    const map = {};
    arr.forEach(w => { const v = w[key]; if (v) map[v] = (map[v]||0)+1; });
    return Object.entries(map).sort((a,b) => b[1]-a[1]).map(([value,count]) => ({value,count}));
  };
  buildChecklist("varietalList", count(wines, "varietal"));
  buildChecklist("regionList",   count(wines, "region"));
  buildChecklist("countryList",  count(wines, "country"));
}

// ── Filter logic (client-side after initial load) ─────────────────────────────
function applyFilters() {
  const wine_type   = document.querySelector("#typeFilter .pill.active")?.dataset.value?.toLowerCase() || "";
  const varietals   = getChecked("varietalList");
  const regions     = getChecked("regionList");
  const countries   = getChecked("countryList");
  const min_price   = parseFloat(document.getElementById("minPrice").value) || null;
  const max_price   = parseFloat(document.getElementById("maxPrice").value) || null;
  const min_disc    = parseInt(discountSlider.value) || 0;
  const sort_by     = document.getElementById("sortBy").value;
  const sources     = new Set(Array.from(document.querySelectorAll(".source-check:checked")).map(el => el.value));

  let filtered = allWines.filter(w => {
    if (!sources.has(w.source)) return false;
    if (wine_type && (w.type||"").toLowerCase() !== wine_type) return false;
    if (varietals.length && !varietals.includes((w.varietal||"").toLowerCase())) return false;
    if (regions.length   && !regions.includes((w.region||"").toLowerCase()))     return false;
    if (countries.length && !countries.includes((w.country||"").toLowerCase()))  return false;
    if (min_price != null && (w.price||0) < min_price) return false;
    if (max_price != null && (w.price||Infinity) > max_price) return false;
    if (min_disc > 0 && (w.discount_pct||0) < min_disc) return false;
    return true;
  });

  if (sort_by === "price_asc")  filtered.sort((a,b) => (a.price||9999)-(b.price||9999));
  else if (sort_by === "price_desc") filtered.sort((a,b) => (b.price||0)-(a.price||0));
  else if (sort_by === "discount")   filtered.sort((a,b) => (b.discount_pct||0)-(a.discount_pct||0));
  else if (sort_by === "rating")     filtered.sort((a,b) => (b.rating||0)-(a.rating||0));

  dealCount.textContent = `${filtered.length} deal${filtered.length !== 1?"s":""} found`;
  renderWines(filtered);
}

discountSlider.addEventListener("input", () => { discountVal.textContent = discountSlider.value + "%+"; });
document.querySelectorAll("#typeFilter .pill").forEach(pill => {
  pill.addEventListener("click", () => {
    document.querySelectorAll("#typeFilter .pill").forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
    applyFilters();
  });
});
document.getElementById("sortBy").addEventListener("change", applyFilters);
discountSlider.addEventListener("change", applyFilters);
document.getElementById("minPrice").addEventListener("change", applyFilters);
document.getElementById("maxPrice").addEventListener("change", applyFilters);
document.querySelectorAll(".source-check").forEach(el => el.addEventListener("change", applyFilters));

function clearFilters() {
  document.querySelectorAll(".source-check").forEach(el => el.checked = true);
  document.querySelectorAll("#typeFilter .pill").forEach(p => p.classList.remove("active"));
  document.querySelector('#typeFilter .pill[data-value=""]').classList.add("active");
  document.querySelectorAll(".checklist-item input").forEach(el => el.checked = false);
  document.querySelectorAll(".check-search").forEach(el => { el.value = ""; filterChecklist(el.closest(".sidebar-section").querySelector(".checklist").id, ""); });
  document.getElementById("minPrice").value = "";
  document.getElementById("maxPrice").value = "";
  discountSlider.value = 0; discountVal.textContent = "0%+";
  document.getElementById("sortBy").value = "discount";
  applyFilters();
}

// Hook checklist checkboxes to filter after check
document.addEventListener("change", e => {
  if (e.target.matches(".checklist-item input")) applyFilters();
});

// ── Rendering ─────────────────────────────────────────────────────────────────
function showState(state) {
  loadingState.classList.add("hidden");
  emptyState.classList.add("hidden");
  errorState.classList.add("hidden");
  grid.innerHTML = "";
  sourceStatus.classList.add("hidden");
  sourceStatus.innerHTML = "";
  if (state === "loading") loadingState.classList.remove("hidden");
  if (state === "empty")   emptyState.classList.remove("hidden");
  if (state === "error")   errorState.classList.remove("hidden");
}

function renderSourceStatus(wines) {
  const counts = {};
  wines.forEach(w => { counts[w.source] = (counts[w.source]||0)+1; });
  const all = Array.from(document.querySelectorAll(".source-check")).map(el => el.value);
  sourceStatus.innerHTML = all.map(src =>
    counts[src]
      ? `<span class="source-pill ok">${src}: ${counts[src]}</span>`
      : `<span class="source-pill empty">${src}: 0</span>`
  ).join("");
  sourceStatus.classList.remove("hidden");
}

const TYPE_COLORS = {red:"type-red",white:"type-white",rose:"type-rose","rosé":"type-rose",sparkling:"type-sparkling",dessert:"type-dessert"};
const TYPE_ICONS  = {red:"🍷",white:"🥂",rose:"🌸","rosé":"🌸",sparkling:"🍾",dessert:"🍯"};
function typeIcon(t) { return TYPE_ICONS[(t||"").toLowerCase()] || "🍷"; }

const tpl = document.getElementById("wineCardTpl");

function renderWines(wines) {
  grid.innerHTML = "";
  renderSourceStatus(allWines); // always show full source totals
  if (!wines.length) { showState("empty"); return; }
  sourceStatus.classList.remove("hidden"); // keep status visible even when empty

  wines.forEach((w, i) => {
    const card = tpl.content.cloneNode(true).querySelector(".wine-card");
    card.style.animationDelay = `${Math.min(i * 0.025, 0.5)}s`;
    card.dataset.wine = JSON.stringify(w);

    const saveBtn = card.querySelector(".save-btn");
    if (savedUrls.has(w.url)) saveBtn.classList.add("saved");

    card.querySelector(".card-link").href = w.url || "#";

    const img = card.querySelector(".card-image");
    if (w.image) {
      img.src = w.image; img.alt = w.name;
      img.onerror = () => { img.style.display="none"; addImgPlaceholder(img.parentNode, w.type); };
    } else { img.style.display="none"; addImgPlaceholder(img.parentNode, w.type); }

    const badge = card.querySelector(".discount-badge");
    if (w.discount_pct > 0) badge.textContent = `–${w.discount_pct}%`;
    else badge.style.display = "none";

    const typeTag = card.querySelector(".card-type-tag");
    if (w.type) {
      typeTag.textContent = w.type;
      const cls = TYPE_COLORS[(w.type||"").toLowerCase()];
      if (cls) typeTag.classList.add(cls);
    } else typeTag.style.display = "none";

    card.querySelector(".card-source").textContent   = w.source   || "";
    card.querySelector(".card-name").textContent     = w.name     || "Unknown Wine";
    card.querySelector(".card-varietal").textContent = w.varietal || "";
    card.querySelector(".card-region").textContent   = w.region   || "";
    card.querySelector(".card-country").textContent  = w.country  || "";

    const priceEl = card.querySelector(".card-price");
    const origEl  = card.querySelector(".card-original");
    priceEl.textContent = w.price != null ? `$${w.price.toFixed(2)}` : "See site";
    if (w.original_price && w.original_price > (w.price||0)) origEl.textContent = `$${w.original_price.toFixed(2)}`;
    else origEl.style.display = "none";

    if (w.rating) {
      card.querySelector(".card-rating").classList.remove("hidden");
      card.querySelector(".rating-val").textContent = w.rating.toFixed(1);
    }
    grid.appendChild(card);
  });
}

function addImgPlaceholder(parent, type) {
  const ph = document.createElement("span");
  ph.className = "card-image-placeholder";
  ph.textContent = typeIcon(type);
  parent.appendChild(ph);
}

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function fetchWines() {
  showState("loading");
  refreshBtn.classList.add("loading");
  dealCount.textContent = "Loading…";

  const sources = Array.from(document.querySelectorAll(".source-check:checked")).map(el => el.value);
  const params = new URLSearchParams();
  sources.forEach(s => params.append("sources", s));

  try {
    const res = await fetch(`/api/wines?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    allWines = data.wines || [];
    populateChecklists(allWines);
    dealCount.textContent = `${allWines.length} deal${allWines.length!==1?"s":""} found`;
    applyFilters();
  } catch (err) {
    console.error(err);
    showState("error");
    dealCount.textContent = "Error";
  } finally {
    refreshBtn.classList.remove("loading");
  }
}

// ── Wishlist ──────────────────────────────────────────────────────────────────
function toggleWishlist() {
  const open = wishlistDrawer.classList.toggle("open");
  wishlistOverlay.classList.toggle("open", open);
  if (open) renderWishlist();
}
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && wishlistDrawer.classList.contains("open")) toggleWishlist();
});

async function toggleSave(btn) {
  const card = btn.closest(".wine-card");
  const wine = JSON.parse(card.dataset.wine || "{}");
  if (!wine.url) return;
  if (btn.classList.contains("saved")) {
    await fetch(`/api/wishlist/${encodeURIComponent(wine.url)}`, { method: "DELETE" });
    btn.classList.remove("saved");
    savedUrls.delete(wine.url);
  } else {
    await fetch("/api/wishlist", { method: "POST",
      headers: {"Content-Type":"application/json"}, body: JSON.stringify(wine) });
    btn.classList.add("saved");
    savedUrls.add(wine.url);
    btn.style.transform = "scale(1.4)";
    setTimeout(() => btn.style.transform = "", 300);
  }
  await updateBadge();
}

async function updateBadge() {
  try {
    const res = await fetch("/api/wishlist");
    const data = await res.json();
    const items = data.items || [];
    savedUrls = new Set(items.map(i => i.url));
    wishlistBadge.textContent = items.length;
    wishlistBadge.classList.toggle("hidden", items.length === 0);
    return items;
  } catch { return []; }
}

async function renderWishlist() {
  const items = await updateBadge();
  wishlistGroups.innerHTML = "";
  if (!items.length) {
    wishlistEmpty.classList.remove("hidden");
    wishlistFooter.classList.add("hidden");
    return;
  }
  wishlistEmpty.classList.add("hidden");
  wishlistFooter.classList.remove("hidden");

  const groups = {};
  items.forEach(w => { if (!groups[w.source]) groups[w.source]=[]; groups[w.source].push(w); });

  Object.entries(groups).forEach(([source, wines]) => {
    const group = document.createElement("div");
    group.className = "wishlist-group";
    group.innerHTML = `
      <div class="group-header">
        <span class="group-name">${source} · ${wines.length} bottle${wines.length>1?"s":""}</span>
        <button class="group-open-btn" onclick="openSiteGroup('${source}')">
          Shop ${source}
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        </button>
      </div>`;
    wines.forEach(w => {
      const item = document.createElement("div");
      item.className = "wishlist-item";
      const imgHtml = w.image
        ? `<img class="wl-image" src="${w.image}" onerror="this.style.display='none'" alt="">`
        : `<div class="wl-image-ph">${typeIcon(w.type)}</div>`;
      const discHtml = w.discount_pct > 0 ? `<span class="wl-badge">–${w.discount_pct}%</span>` : "";
      const origHtml = (w.original_price && w.original_price > (w.price||0))
        ? `<span class="wl-orig">$${w.original_price.toFixed(2)}</span>` : "";
      const meta = [w.varietal, w.region, w.country].filter(Boolean).join(" · ");
      item.innerHTML = `
        ${imgHtml}
        <div class="wl-info">
          <div class="wl-name" title="${w.name}">${w.name}</div>
          ${meta ? `<div class="wl-meta">${meta}</div>` : ""}
          <div><span class="wl-price">${w.price!=null?"$"+w.price.toFixed(2):"See site"}</span>${origHtml}${discHtml}</div>
        </div>
        <button class="wl-remove" title="Remove" onclick="removeItem('${encodeURIComponent(w.url)}',this)">✕</button>`;
      group.appendChild(item);
    });
    wishlistGroups.appendChild(group);
  });
}

async function removeItem(encodedUrl, btn) {
  await fetch(`/api/wishlist/${encodedUrl}`, { method: "DELETE" });
  btn.closest(".wishlist-item").remove();
  const group = btn.closest(".wishlist-group");
  if (group && !group.querySelector(".wishlist-item")) group.remove();
  await updateBadge();
  document.querySelectorAll(".save-btn.saved").forEach(b => {
    const w = JSON.parse(b.closest(".wine-card").dataset.wine || "{}");
    if (!savedUrls.has(w.url)) b.classList.remove("saved");
  });
  if (!wishlistGroups.querySelector(".wishlist-item")) {
    wishlistEmpty.classList.remove("hidden");
    wishlistFooter.classList.add("hidden");
  }
}

function openSiteGroup(source) {
  const items = [];
  wishlistGroups.querySelectorAll(".wishlist-group").forEach(g => {
    if (g.querySelector(".group-name")?.textContent.startsWith(source)) {
      g.querySelectorAll(".wl-remove").forEach(btn => {
        const m = btn.getAttribute("onclick").match(/removeItem\('(.+?)'/);
        if (m) items.push(decodeURIComponent(m[1]));
      });
    }
  });
  items.forEach((url, i) => setTimeout(() => window.open(url, "_blank"), i * 200));
}

async function openAllSites() {
  const items = await updateBadge();
  items.forEach((w, i) => setTimeout(() => window.open(w.url, "_blank"), i * 200));
}

async function clearWishlist() {
  if (!confirm("Clear your entire wine list?")) return;
  await fetch("/api/wishlist/clear", { method: "POST" });
  savedUrls.clear();
  document.querySelectorAll(".save-btn.saved").forEach(b => b.classList.remove("saved"));
  wishlistGroups.innerHTML = "";
  wishlistEmpty.classList.remove("hidden");
  wishlistFooter.classList.add("hidden");
  wishlistBadge.classList.add("hidden");
}

// ── Init ──────────────────────────────────────────────────────────────────────
updateBadge();
fetchWines();
