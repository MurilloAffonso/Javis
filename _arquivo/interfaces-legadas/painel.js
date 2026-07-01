// Painel do Jamba — consome os endpoints do backend e atualiza a cada 10s.
const API = "http://localhost:8000";

// Relógio ao vivo
function tickClock() {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toLocaleTimeString("pt-BR");
}
setInterval(tickClock, 1000);
tickClock();

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

async function getJSON(path) {
  const res = await fetch(API + path, { signal: AbortSignal.timeout(6000) });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

function setConn(ok) {
  const dot = document.getElementById("conn-dot");
  const lbl = document.getElementById("conn-lbl");
  if (dot) dot.classList.toggle("on", ok);
  if (lbl) lbl.textContent = ok ? "conectado ao Jamba" : "servidor offline";
}

// ── Lembretes ──
async function loadReminders() {
  const box = document.getElementById("reminders");
  try {
    const { pending } = await getJSON("/reminders");
    document.getElementById("r-rem").textContent = pending.length;
    if (!pending.length) { box.innerHTML = '<div class="empty">Nenhum lembrete pendente, senhor.</div>'; return; }
    box.innerHTML = pending.map(p => `
      <div class="item">
        ${esc(p.text)}
        <div class="meta">em <span class="accent">${p.falta_min} min</span></div>
      </div>`).join("");
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

// ── Memória ──
async function loadMemory() {
  const box = document.getElementById("memory");
  try {
    const { facts } = await getJSON("/profile");
    if (!facts.length) { box.innerHTML = '<div class="empty">Ainda não sei nada sobre o senhor.</div>'; return; }
    box.innerHTML = facts.map(f => `<div class="item">${esc(f)}</div>`).join("");
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

// ── Serviços ──
async function loadServices() {
  const box = document.getElementById("services");
  try {
    const { services } = await getJSON("/status");
    setConn(true);
    const entries = Object.entries(services || {});
    box.innerHTML = entries.map(([name, s]) => `
      <div class="svc">
        <span class="svc-dot ${s.status === "online" ? "on" : ""}"></span>
        <span class="svc-name">${esc(name)}</span>
        <span class="svc-port">:${s.port}</span>
      </div>`).join("");
  } catch { setConn(false); box.innerHTML = '<div class="empty">—</div>'; }
}

// ── Integrações ──
const INTEG_LABELS = {
  youtube: "YouTube", google: "Google", spotify: "Spotify",
  canva: "Canva", openweather: "Clima", telegram: "Telegram",
};
async function loadIntegrations() {
  const box = document.getElementById("integrations");
  try {
    const data = await getJSON("/integrations");
    const keys = Object.keys(INTEG_LABELS);
    let on = 0;
    box.innerHTML = keys.map(k => {
      const active = !!data[k];
      if (active) on++;
      return `<span class="chip ${active ? "on" : ""}"><span class="c-dot"></span>${INTEG_LABELS[k]}</span>`;
    }).join("");
    document.getElementById("r-integ").textContent = on;
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

// ── Histórico ──
async function loadHistory() {
  const box = document.getElementById("history");
  try {
    const { history } = await getJSON("/history");
    document.getElementById("r-msgs").textContent = history.length;
    const last = history.slice(-10).reverse();
    if (!last.length) { box.innerHTML = '<div class="empty">Nenhuma conversa ainda.</div>'; return; }
    box.innerHTML = last.map(h => {
      const resp = (h.response || "").replace(/<[^>]+>/g, "").slice(0, 160);
      return `
        <div class="item">
          <div class="h-user">${esc(h.user || "")}</div>
          <div class="h-bot">${esc(resp)}</div>
          <div class="meta">
            ${h.intent ? `<span class="tag">${esc(h.intent)}</span>` : ""}
            ${h.brain ? `<span class="tag">🧠 ${esc(h.brain)}</span>` : ""}
            ${h.ms != null ? `${h.ms}ms` : ""}
          </div>
        </div>`;
    }).join("");
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

// ── Agentes (só o total para o resumo) ──
async function loadAgents() {
  try {
    const { total } = await getJSON("/agents");
    document.getElementById("r-agents").textContent = total ?? "—";
  } catch {}
}

function refreshAll() {
  loadServices();
  loadReminders();
  loadMemory();
  loadIntegrations();
  loadHistory();
  loadAgents();
}

refreshAll();
setInterval(refreshAll, 10000);
