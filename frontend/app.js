const API = "/api/v1";

const state = {
  token: localStorage.getItem("steam_cases_token") || null,
  user: null,
  cases: [],
  currentCase: null,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function money(value) {
  return Number(value || 0).toFixed(2);
}

function rarityLabel(rarity) {
  return ({ common: "COMMON", rare: "RARE", epic: "EPIC", legendary: "LEGENDARY" })[rarity] || String(rarity || "").toUpperCase();
}

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function toast(message, type = "success") {
  const root = $("#toastRoot");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => el.remove(), 3600);
}

function getErrorDetail(payload, fallback = "Произошла ошибка") {
  if (!payload) return fallback;
  if (Array.isArray(payload.detail)) return payload.detail.join(" ");
  return payload.detail || fallback;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);

  const response = await fetch(`${API}${path}`, { ...options, headers });
  let payload = null;
  const text = await response.text();
  if (text) {
    try { payload = JSON.parse(text); } catch { payload = { detail: text }; }
  }

  if (response.status === 401 && state.token) {
    logout(false);
    openAuth("login");
    throw new Error("Сессия истекла. Войди снова.");
  }
  if (!response.ok) throw new Error(getErrorDetail(payload, `HTTP ${response.status}`));
  return payload;
}

function setAuthUI() {
  const authed = Boolean(state.token && state.user);
  $$(".auth-only").forEach(el => el.classList.toggle("hidden", !authed));
  $$(".guest-only").forEach(el => el.classList.toggle("hidden", authed));

  if (authed) {
    $("#profileName").textContent = state.user.username;
    $("#profileAvatar").textContent = state.user.username.slice(0, 1).toUpperCase();
    $("#balanceValue").textContent = money(state.user.balance);
  }
}

async function restoreSession() {
  if (!state.token) {
    setAuthUI();
    return;
  }
  try {
    state.user = await api("/auth/me");
  } catch {
    state.token = null;
    state.user = null;
    localStorage.removeItem("steam_cases_token");
  }
  setAuthUI();
}

function saveSession(auth) {
  state.token = auth.access_token;
  state.user = auth.user;
  localStorage.setItem("steam_cases_token", state.token);
  setAuthUI();
}

function logout(showToast = true) {
  state.token = null;
  state.user = null;
  localStorage.removeItem("steam_cases_token");
  setAuthUI();
  showView("cases");
  if (showToast) toast("Ты вышел из аккаунта");
}

function openModal(id) { $("#" + id).classList.remove("hidden"); document.body.style.overflow = "hidden"; }
function closeModal(id) { $("#" + id).classList.add("hidden"); document.body.style.overflow = ""; }

function openAuth(mode = "login") {
  const login = mode === "login";
  $("#loginForm").classList.toggle("hidden", !login);
  $("#registerForm").classList.toggle("hidden", login);
  $("#authTitle").textContent = login ? "Вход" : "Регистрация";
  $("#authSubtitle").textContent = login
    ? "Войди, чтобы открывать кейсы и получать ключи."
    : "Создай аккаунт и начни собирать игровые ключи.";
  $("#authError").classList.add("hidden");
  openModal("authModal");
}

function showView(view) {
  if ((view === "inventory" || view === "history") && !state.token) {
    openAuth("login");
    return;
  }
  $$(".view").forEach(el => el.classList.remove("active"));
  $(`#${view}View`).classList.add("active");
  $$(".nav-link").forEach(el => el.classList.toggle("active", el.dataset.view === view));
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (view === "inventory") loadInventory();
  if (view === "history") loadHistory();
}

function imageHtml(url, alt, fallbackClass = "case-image-fallback") {
  if (!url) return `<div class="${fallbackClass}">SC</div>`;
  return `<img src="${escapeHtml(url)}" alt="${escapeHtml(alt)}" loading="lazy" onerror="this.outerHTML='<div class=&quot;${fallbackClass}&quot;>SC</div>'" />`;
}

async function loadCases() {
  const rarity = $("#rarityFilter").value;
  const maxPrice = $("#maxPriceFilter").value;
  const params = new URLSearchParams({ limit: "100", offset: "0" });
  if (rarity) params.set("rarity", rarity);
  if (maxPrice) params.set("max_price", maxPrice);

  $("#casesGrid").innerHTML = `<div class="empty-state" style="grid-column:1/-1;margin-bottom:0"><div class="spinner"></div><p>Загружаем кейсы...</p></div>`;
  $("#casesEmpty").classList.add("hidden");
  try {
    const data = await api(`/cases?${params}`);
    state.cases = data.items || [];
    renderCases();
  } catch (err) {
    $("#casesGrid").innerHTML = "";
    $("#casesEmpty").classList.remove("hidden");
    toast(err.message, "error");
  }
}

function renderCases() {
  const grid = $("#casesGrid");
  grid.innerHTML = "";
  $("#casesEmpty").classList.toggle("hidden", state.cases.length > 0);

  for (const c of state.cases) {
    const card = document.createElement("article");
    card.className = "case-card";
    card.innerHTML = `
      <div class="case-image">${imageHtml(c.image_url, c.name)}</div>
      <div class="case-card-body">
        <h3>${escapeHtml(c.name)}</h3>
        <p>${escapeHtml(c.description || "Открой кейс и получи случайную игру из списка выпадения.")}</p>
        <div class="case-card-bottom">
          <div class="price">${money(c.opening_price)} <small>₽</small></div>
          <button class="button button-primary">Открыть</button>
        </div>
      </div>`;
    $("button", card).addEventListener("click", () => showCase(c.id));
    grid.appendChild(card);
  }
}

async function showCase(caseId) {
  openModal("caseModal");
  $("#caseModalContent").innerHTML = `<div class="opening-loader"><div class="spinner"></div><p>Загружаем содержимое кейса...</p></div>`;
  try {
    const c = await api(`/cases/${caseId}`);
    state.currentCase = c;
    const drops = (c.items || []).map(entry => `
      <div class="drop-item">
        ${entry.item.image_url ? `<img src="${escapeHtml(entry.item.image_url)}" alt="${escapeHtml(entry.item.name)}" onerror="this.style.visibility='hidden'">` : `<div></div>`}
        <div>
          <div class="drop-item-name">${escapeHtml(entry.item.name)}</div>
          <div class="drop-item-price">≈ ${money(entry.item.estimated_price)} ₽ · Steam App ${entry.item.steam_app_id}</div>
        </div>
        <div style="text-align:right">
          <span class="rarity-badge ${escapeHtml(entry.item.rarity)}">${rarityLabel(entry.item.rarity)}</span>
          <div class="chance">${escapeHtml(entry.chance_percent)}%</div>
        </div>
      </div>`).join("");

    $("#caseModalContent").innerHTML = `
      <div class="case-detail-head">
        <div class="case-detail-image">${imageHtml(c.image_url, c.name)}</div>
        <div class="case-detail-info">
          <span class="eyebrow">СОДЕРЖИМОЕ КЕЙСА</span>
          <h2 id="caseModalTitle">${escapeHtml(c.name)}</h2>
          <p>${escapeHtml(c.description || "Выигрыш определяется случайно на основании указанных весов.")}</p>
          <div class="case-detail-price">${money(c.opening_price)} ₽</div>
        </div>
      </div>
      <div class="drop-list">
        <h3>Возможные предметы</h3>
        ${drops || `<p style="color:var(--muted)">В кейсе нет предметов.</p>`}
      </div>
      <div class="case-open-bar">
        <span>${state.user ? `Баланс: ${money(state.user.balance)} ₽` : "Для открытия нужно войти"}</span>
        <button id="openCaseNow" class="button button-primary button-large">Открыть за ${money(c.opening_price)} ₽</button>
      </div>`;
    $("#openCaseNow").addEventListener("click", () => openCurrentCase());
  } catch (err) {
    $("#caseModalContent").innerHTML = `<div class="empty-state" style="margin:0"><h3>Не удалось загрузить кейс</h3><p>${escapeHtml(err.message)}</p></div>`;
  }
}

async function openCurrentCase() {
  if (!state.token || !state.user) {
    closeModal("caseModal");
    openAuth("login");
    return;
  }
  const c = state.currentCase;
  if (!c) return;
  $("#caseModalContent").innerHTML = `<div class="opening-loader"><div class="spinner"></div><h3>Открываем кейс...</h3><p style="color:var(--muted)">Выбираем предмет по весам вероятности.</p></div>`;
  try {
    const result = await api(`/cases/${c.id}/open`, { method: "POST" });
    closeModal("caseModal");
    state.user.balance = result.balance_after;
    setAuthUI();
    renderResult(result);
    openModal("resultModal");
  } catch (err) {
    closeModal("caseModal");
    toast(err.message, "error");
  }
}

function renderResult(result) {
  const keyBlock = result.key
    ? `<div class="result-key">${escapeHtml(result.key.key)}</div><div class="result-note">Ключ уже добавлен в твой инвентарь.</div>`
    : `<div class="result-key">Ключ пока не выдан</div><div class="result-note">Для этого предмета не оказалось свободного ключа.</div>`;

  $("#resultContent").innerHTML = `
    ${result.item.image_url ? `<img class="result-item-image" src="${escapeHtml(result.item.image_url)}" alt="${escapeHtml(result.item.name)}">` : ""}
    <div class="result-name">${escapeHtml(result.item.name)}</div>
    <span class="rarity-badge ${escapeHtml(result.item.rarity)}">${rarityLabel(result.item.rarity)}</span>
    ${keyBlock}`;
}

async function loadInventory() {
  const grid = $("#inventoryGrid");
  grid.innerHTML = `<div class="opening-loader" style="grid-column:1/-1"><div class="spinner"></div></div>`;
  $("#inventoryEmpty").classList.add("hidden");
  try {
    const data = await api("/inventory");
    grid.innerHTML = "";
    $("#inventoryEmpty").classList.toggle("hidden", data.items.length > 0);
    data.items.forEach(item => {
      const el = document.createElement("article");
      el.className = "inventory-item";
      el.innerHTML = `
        ${item.item.image_url ? `<img class="inventory-cover" src="${escapeHtml(item.item.image_url)}" alt="${escapeHtml(item.item.name)}">` : `<div class="inventory-cover fallback">GAME</div>`}
        <div class="inventory-meta">
          <span class="rarity-badge ${escapeHtml(item.item.rarity)}">${rarityLabel(item.item.rarity)}</span>
          <h3>${escapeHtml(item.item.name)}</h3>
          <div class="steam-id">Steam App ID: ${item.item.steam_app_id}</div>
          <div class="key-row"><code class="key-code">${escapeHtml(item.key)}</code><button class="button button-secondary copy-key" style="padding:7px 9px">Копировать</button></div>
        </div>
        <div class="inventory-actions">
          <span class="status ${escapeHtml(item.status)}">${item.status === "used" ? "Использован" : "Назначен"}</span>
          ${item.status === "assigned" ? `<button class="button button-ghost mark-used">Пометить использованным</button>` : ""}
        </div>`;
      $(".copy-key", el).addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(item.key);
          toast("Ключ скопирован");
        } catch {
          toast("Не удалось скопировать автоматически — выдели ключ вручную", "error");
        }
      });
      const mark = $(".mark-used", el);
      if (mark) mark.addEventListener("click", () => markKeyUsed(item.id));
      grid.appendChild(el);
    });
  } catch (err) {
    grid.innerHTML = "";
    toast(err.message, "error");
  }
}

async function markKeyUsed(keyId) {
  try {
    await api(`/inventory/${keyId}/use`, { method: "POST" });
    toast("Ключ помечен как использованный");
    await loadInventory();
  } catch (err) { toast(err.message, "error"); }
}

async function loadHistory() {
  const body = $("#historyBody");
  body.innerHTML = `<tr><td colspan="6"><div class="opening-loader"><div class="spinner"></div></div></td></tr>`;
  $("#historyEmpty").classList.add("hidden");
  try {
    const data = await api("/openings?limit=100&offset=0");
    body.innerHTML = "";
    $("#historyEmpty").classList.toggle("hidden", data.items.length > 0);
    $(".table-wrap").classList.toggle("hidden", data.items.length === 0);
    for (const row of data.items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(row.case.name)}</td>
        <td><strong>${escapeHtml(row.item.name)}</strong></td>
        <td><span class="rarity-badge ${escapeHtml(row.item.rarity)}">${rarityLabel(row.item.rarity)}</span></td>
        <td>${money(row.cost)} ₽</td>
        <td class="key-cell">${row.key ? escapeHtml(row.key.key) : "—"}</td>
        <td>${escapeHtml(formatDate(row.opened_at))}</td>`;
      body.appendChild(tr);
    }
  } catch (err) {
    body.innerHTML = "";
    toast(err.message, "error");
  }
}

async function refreshMe() {
  if (!state.token) return;
  try { state.user = await api("/auth/me"); setAuthUI(); } catch { /* handled */ }
}

async function topup(amount) {
  try {
    const data = await api("/balance/top-up", { method: "POST", body: JSON.stringify({ amount: String(amount) }) });
    state.user.balance = data.balance;
    setAuthUI();
    closeModal("topupModal");
    toast(`Баланс пополнен. Сейчас: ${money(data.balance)} ₽`);
  } catch (err) { toast(err.message, "error"); }
}

function bindEvents() {
  $("#loginButton").addEventListener("click", () => openAuth("login"));
  $("#registerButton").addEventListener("click", () => openAuth("register"));
  $("#heroLoginButton").addEventListener("click", () => openAuth("login"));
  $("#switchToRegister").addEventListener("click", () => openAuth("register"));
  $("#switchToLogin").addEventListener("click", () => openAuth("login"));
  $("#logoutButton").addEventListener("click", () => logout());
  $("#topupButton").addEventListener("click", () => openModal("topupModal"));
  $("#applyFilters").addEventListener("click", loadCases);
  $("#refreshInventory").addEventListener("click", loadInventory);
  $("#refreshHistory").addEventListener("click", loadHistory);
  $("#heroCasesButton").addEventListener("click", () => $("#casesSection").scrollIntoView({ behavior: "smooth" }));
  $("#closeResultButton").addEventListener("click", async () => { closeModal("resultModal"); await refreshMe(); showView("inventory"); });

  $$('[data-close-modal]').forEach(el => el.addEventListener("click", () => closeModal(el.dataset.closeModal)));
  $$('[data-view]').forEach(el => el.addEventListener("click", () => showView(el.dataset.view)));
  $$('[data-view-link]').forEach(el => el.addEventListener("click", (e) => { e.preventDefault(); showView(el.dataset.viewLink); }));

  $("#loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const error = $("#authError");
    error.classList.add("hidden");
    try {
      const auth = await api("/auth/login", { method: "POST", body: JSON.stringify({ username: data.get("username"), password: data.get("password") }) });
      saveSession(auth);
      closeModal("authModal");
      toast(`Добро пожаловать, ${auth.user.username}`);
    } catch (err) { error.textContent = err.message; error.classList.remove("hidden"); }
  });

  $("#registerForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const error = $("#authError");
    error.classList.add("hidden");
    try {
      const auth = await api("/auth/register", { method: "POST", body: JSON.stringify({ username: data.get("username"), email: data.get("email"), password: data.get("password") }) });
      saveSession(auth);
      closeModal("authModal");
      toast("Аккаунт создан");
    } catch (err) { error.textContent = err.message; error.classList.remove("hidden"); }
  });

  $("#topupForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await topup(data.get("amount"));
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") $$(".modal:not(.hidden)").forEach(modal => closeModal(modal.id));
  });
}

async function init() {
  bindEvents();
  await restoreSession();
  await loadCases();
}

init();
