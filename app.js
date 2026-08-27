const state = {
  asanas: [],
  study: [],
  filtered: [],
  practice: [],
  goal: "",
  contra: new Set(),
  deferredPrompt: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const els = {
  search: $("#searchInput"),
  section: $("#sectionFilter"),
  level: $("#levelFilter"),
  goalChips: $("#goalChips"),
  list: $("#asanaList"),
  count: $("#resultCount"),
  filteredNote: $("#filteredNote"),
  practiceCount: $("#practiceCount"),
  practiceTime: $("#practiceTime"),
  practiceList: $("#practiceList"),
  instruction: $("#instructionText"),
  target: $("#targetMinutes"),
  targetLabel: $("#targetLabel"),
  focus: $("#focusSelect"),
  studySearch: $("#studySearch"),
  studyList: $("#studyList"),
  install: $("#installBtn"),
};

const GOALS = [
  { label: "Растяжка", tokens: ["вытяж", "задняя", "наклон", "бедр"] },
  { label: "Ноги", tokens: ["ног", "стоп", "воин", "стул", "выпад"] },
  { label: "Поясница", tokens: ["пояс", "спина", "крест"] },
  { label: "Таз", tokens: ["таз", "пах", "ягод", "бедр"] },
  { label: "Плечи", tokens: ["плеч", "лопат", "запяст"] },
  { label: "Сила", tokens: ["сила", "кор", "руки", "планка", "центр"] },
  { label: "Баланс", tokens: ["баланс", "стойка", "фокус"] },
  { label: "Скрутки", tokens: ["скрут", "повер", "живот"] },
  { label: "Прогибы", tokens: ["прогиб", "груд", "передняя"] },
  { label: "Восстановление", tokens: ["восстанов", "отдых", "шавасана", "расслаб"] },
];

const CONTRA = {
  knee: ["колен", "мениск", "Padmasana", "Virasana", "Supta Virasana", "Hanumanasana", "Malasana", "Skandasana", "Agnistambhasana", "Tolasana"],
  lowback: ["пояс", "грыж", "ишиас", "Urdhva Dhanurasana", "Kapotasana", "Dhanurasana"],
  wristshoulder: ["запяст", "плеч", "Chaturanga", "Bakasana", "Kakasana", "Mayurasana", "Adho Mukha Vrksasana", "Vasisthasana"],
  menstruation: ["менстру", "Sirsasana", "Sarvangasana", "Halasana", "Karnapidasana", "Pincha", "Adho Mukha Vrksasana"],
  pressure: ["давлен", "глауком", "Sirsasana", "Sarvangasana", "Halasana", "Pincha", "Adho Mukha Vrksasana"],
  pregnancy: ["беремен", "живот", "глубок", "Chaturanga", "Mayurasana"],
};

const BLOCKS = [
  { name: "центрирование", match: (a) => a.section.includes("Сидячие") || a.sanskrit === "Tadasana" || a.sanskrit === "Sukhasana" },
  { name: "разминка", match: (a) => a.section.includes("Разминка") || a.section.includes("паузы") },
  { name: "виньяса", match: (a) => a.section.includes("Виньяса") || a.sanskrit === "Adho Mukha Svanasana" || a.sanskrit === "Phalakasana" },
  { name: "стоячий блок", match: (a) => a.section.includes("Стояч") || a.section.includes("Балансы стоя") },
  { name: "цель", match: () => true },
  { name: "компенсация", match: (a) => a.section.includes("Скрутки лежа") || a.sanskrit === "Apanasana" || a.sanskrit === "Balasana" },
  { name: "завершение", match: (a) => a.sanskrit === "Savasana" || a.section.includes("Восстановление") },
];

function normalize(value) {
  return String(value || "").toLowerCase().trim();
}

function asanaText(asana) {
  return normalize([asana.ru, asana.sanskrit, asana.transliteration, asana.section, asana.goals, asana.contraindications].join(" "));
}

function isBlocked(asana) {
  const text = asanaText(asana);
  return [...state.contra].some((key) => CONTRA[key].some((token) => text.includes(normalize(token))));
}

function matchesGoal(asana, goalLabel) {
  if (!goalLabel) return true;
  const goal = GOALS.find((item) => item.label === goalLabel);
  if (!goal) return true;
  const text = asanaText(asana);
  return goal.tokens.some((token) => text.includes(token));
}

function unique(values) {
  return [...new Set(values)].filter(Boolean).sort((a, b) => a.localeCompare(b, "ru"));
}

function option(label, value = label) {
  return `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

async function loadData() {
  const [asanasRes, studyRes] = await Promise.all([
    fetch("data/asanas.json"),
    fetch("data/study.json"),
  ]);
  state.asanas = await asanasRes.json();
  state.study = await studyRes.json();
  state.practice = JSON.parse(localStorage.getItem("namaskar.practice") || "[]");
}

function setupFilters() {
  els.section.innerHTML = option("Все разделы", "") + unique(state.asanas.map((a) => a.section)).map((s) => option(s)).join("");
  els.level.innerHTML = option("Все уровни", "") + ["начальный", "средний", "продвинутый"].map((s) => option(s)).join("");
  els.focus.innerHTML = GOALS.map((g) => option(g.label)).join("");
  els.goalChips.innerHTML = GOALS.map((g) => `<button type="button" data-goal="${escapeHtml(g.label)}">${escapeHtml(g.label)}</button>`).join("");
}

function bindEvents() {
  [els.search, els.section, els.level].forEach((el) => el.addEventListener("input", renderLibrary));
  $$(".contra-panel input").forEach((input) => input.addEventListener("change", () => {
    input.checked ? state.contra.add(input.value) : state.contra.delete(input.value);
    renderLibrary();
    renderPractice();
  }));
  els.goalChips.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-goal]");
    if (!button) return;
    state.goal = state.goal === button.dataset.goal ? "" : button.dataset.goal;
    renderLibrary();
  });
  $$(".bottom-nav button").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.tab)));
  els.target.addEventListener("input", () => { els.targetLabel.textContent = els.target.value; });
  $("#randomPractice").addEventListener("click", generatePractice);
  $("#clearPractice").addEventListener("click", () => { state.practice = []; persistPractice(); renderPractice(); });
  $("#copyInstruction").addEventListener("click", copyInstruction);
  els.studySearch.addEventListener("input", renderStudy);
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    state.deferredPrompt = event;
    els.install.hidden = false;
  });
  els.install.addEventListener("click", async () => {
    if (!state.deferredPrompt) return;
    state.deferredPrompt.prompt();
    await state.deferredPrompt.userChoice;
    state.deferredPrompt = null;
    els.install.hidden = true;
  });
}

function switchView(tab) {
  $$(".view").forEach((view) => view.classList.toggle("is-active", view.dataset.view === tab));
  $$(".bottom-nav button").forEach((button) => button.classList.toggle("is-active", button.dataset.tab === tab));
  if (tab === "study") renderStudy();
  if (tab === "practice") renderPractice();
}

function renderLibrary() {
  const query = normalize(els.search.value);
  const section = els.section.value;
  const level = els.level.value;
  let blocked = 0;
  state.filtered = state.asanas.filter((asana) => {
    if (isBlocked(asana)) { blocked += 1; return false; }
    if (section && asana.section !== section) return false;
    if (level && asana.level !== level) return false;
    if (state.goal && !matchesGoal(asana, state.goal)) return false;
    if (query && !asanaText(asana).includes(query)) return false;
    return true;
  });
  els.count.textContent = `${state.filtered.length} ${plural(state.filtered.length, ["асана", "асаны", "асан"])}`;
  els.filteredNote.textContent = blocked ? `скрыто: ${blocked}` : "";
  $$("#goalChips button").forEach((button) => button.classList.toggle("is-active", state.goal === button.dataset.goal));
  els.list.innerHTML = state.filtered.length ? "" : `<div class="empty">Ничего не найдено</div>`;
  const template = $("#asanaCardTemplate");
  state.filtered.forEach((asana) => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".asana-card");
    const img = node.querySelector("img");
    img.src = asana.image;
    img.alt = asana.ru;
    node.querySelector("h3").textContent = capitalize(asana.ru);
    node.querySelector(".sanskrit").textContent = asana.sanskrit;
    node.querySelector(".translit").textContent = asana.transliteration;
    node.querySelector(".effect").textContent = `${asana.section} · ${asana.goals} · ${asana.minutes} мин`;
    node.querySelector(".execution").textContent = asana.execution;
    node.querySelector(".contra").textContent = asana.contraindications;
    node.querySelector(".add-button").addEventListener("click", () => addToPractice(asana));
    card.addEventListener("dblclick", () => addToPractice(asana));
    els.list.appendChild(node);
  });
}

function addToPractice(asana) {
  state.practice.push(asana.id);
  persistPractice();
  renderPractice();
}

function removeFromPractice(index) {
  state.practice.splice(index, 1);
  persistPractice();
  renderPractice();
}

function persistPractice() {
  localStorage.setItem("namaskar.practice", JSON.stringify(state.practice));
}

function getPracticeAsanas() {
  return state.practice.map((id) => state.asanas.find((asana) => asana.id === id)).filter(Boolean);
}

function renderPractice() {
  const items = getPracticeAsanas();
  const total = items.reduce((sum, asana) => sum + asana.minutes, 0);
  els.practiceCount.textContent = items.length;
  els.practiceTime.textContent = total;
  els.practiceList.innerHTML = items.length ? "" : `<div class="empty">Добавьте асаны из библиотеки или соберите практику автоматически</div>`;
  items.forEach((asana, index) => {
    const div = document.createElement("div");
    div.className = "sequence-item";
    div.innerHTML = `
      <div class="sequence-index">${index + 1}</div>
      <div><h3>${escapeHtml(capitalize(asana.ru))}</h3><p>${escapeHtml(asana.sanskrit)} · ${asana.minutes} мин</p></div>
      <button class="remove-button" type="button" title="Убрать">×</button>
    `;
    div.querySelector("button").addEventListener("click", () => removeFromPractice(index));
    els.practiceList.appendChild(div);
  });
  els.instruction.value = buildInstruction(items, total);
}

function buildInstruction(items, total) {
  if (!items.length) return "";
  const lines = [
    `Практика Namaskar, примерная длительность ${total} мин.`,
    "Начните с ровного дыхания и короткой настройки внимания.",
    "",
  ];
  items.forEach((asana, index) => {
    lines.push(`${index + 1}. ${capitalize(asana.ru)} (${asana.sanskrit}, ${asana.transliteration}) — ${asana.minutes} мин.`);
    lines.push(asana.voice);
    if (index < items.length - 1) lines.push(`Переход: ${asana.transitionOut}. Затем ${items[index + 1].transitionIn}.`);
    lines.push("");
  });
  lines.push("Завершите практику наблюдением дыхания. Если была интенсивная работа, оставьте больше времени на Шавасану.");
  return lines.join("\n");
}

function generatePractice() {
  const target = Number(els.target.value);
  const focus = els.focus.value;
  const safePool = state.asanas.filter((asana) => !isBlocked(asana));
  const chosen = [];
  const used = new Set();

  function pick(match, preferFocus = false) {
    let pool = safePool.filter((asana) => !used.has(asana.id) && match(asana));
    if (preferFocus) {
      const focused = pool.filter((asana) => matchesGoal(asana, focus));
      if (focused.length) pool = focused;
    }
    if (!pool.length) return null;
    pool.sort((a, b) => scoreAsana(b, focus) - scoreAsana(a, focus));
    const top = pool.slice(0, Math.min(7, pool.length));
    const item = top[Math.floor(Math.random() * top.length)];
    used.add(item.id);
    chosen.push(item);
    return item;
  }

  BLOCKS.forEach((block) => pick(block.match, block.name === "цель"));
  let total = chosen.reduce((sum, asana) => sum + asana.minutes, 0);
  while (total < target - 4) {
    const item = pick((asana) => !asana.section.includes("Инверсии") || target >= 45, true);
    if (!item) break;
    total += item.minutes;
  }
  const savasana = state.asanas.find((a) => a.sanskrit === "Savasana");
  if (savasana && !used.has(savasana.id) && !isBlocked(savasana)) chosen.push(savasana);

  state.practice = chosen.map((asana) => asana.id);
  persistPractice();
  renderPractice();
  switchView("practice");
}

function scoreAsana(asana, focus) {
  let score = 0;
  if (matchesGoal(asana, focus)) score += 5;
  if (asana.level === "начальный") score += 2;
  if (asana.section.includes("Восстановление") || asana.sanskrit === "Savasana") score += 1;
  return score + Math.random();
}

async function copyInstruction() {
  if (!els.instruction.value) return;
  await navigator.clipboard.writeText(els.instruction.value);
  const button = $("#copyInstruction");
  const old = button.textContent;
  button.textContent = "Скопировано";
  setTimeout(() => { button.textContent = old; }, 1200);
}

function renderStudy() {
  const query = normalize(els.studySearch.value);
  const items = state.study.filter((item) => !query || normalize([item.sanskrit, item.transliteration, item.ru, item.parts, item.literal].join(" ")).includes(query));
  els.studyList.innerHTML = items.length ? "" : `<div class="empty">Ничего не найдено</div>`;
  items.slice(0, 80).forEach((item) => {
    const card = document.createElement("article");
    card.className = "study-card";
    card.innerHTML = `
      <h3>${escapeHtml(item.sanskrit)}</h3>
      <p class="translit">${escapeHtml(item.transliteration)} · ${escapeHtml(item.ru)}</p>
      <p class="syllables">${escapeHtml(item.syllables)}</p>
      <p class="parts">${escapeHtml(item.parts)}</p>
      <p class="parts"><strong>Смысл:</strong> ${escapeHtml(item.literal)}</p>
    `;
    els.studyList.appendChild(card);
  });
}

function plural(number, forms) {
  const mod10 = number % 10;
  const mod100 = number % 100;
  if (mod10 === 1 && mod100 !== 11) return forms[0];
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return forms[1];
  return forms[2];
}

function capitalize(value) {
  return String(value || "").replace(/^./, (letter) => letter.toUpperCase());
}

async function init() {
  await loadData();
  setupFilters();
  bindEvents();
  renderLibrary();
  renderPractice();
  renderStudy();
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("service-worker.js");
  }
}

init().catch((error) => {
  document.body.innerHTML = `<main class="app-shell"><div class="empty">Не удалось загрузить данные: ${escapeHtml(error.message)}</div></main>`;
});
