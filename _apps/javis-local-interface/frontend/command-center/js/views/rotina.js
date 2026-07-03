// Rotina — briefing, histórico e lembretes (leitura) — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, $, state, BACKEND, tryJson, _esc } from "../../app.js";

// Read-only: /briefing (sob demanda), /history e /reminders. Treino/scout tem
// aba própria ("Treino"); aqui só apontamos para ela, sem duplicar.
function viewRotina(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">Resumo do dia do Javes — leitura. O status de treino/scout fica na aba <b>Treino</b>.</div>`));
  if (!state.online) { body.appendChild(h(`<div class="banner">⚠️ Backend offline — conecte o servidor em <code>:8000</code> para ver a rotina.</div>`)); return; }

  // Briefing (sob demanda)
  body.appendChild(h(`<div class="section-h">👋 Briefing</div>`));
  const brWrap = h(`<div class="ro-card"><button class="op-btn" id="ro-brief-btn">Carregar briefing</button><div id="ro-brief" class="ro-brief"></div></div>`);
  body.appendChild(brWrap);
  brWrap.querySelector("#ro-brief-btn").onclick = roLoadBriefing;

  // Histórico
  body.appendChild(h(`<div class="section-h" style="margin-top:20px">🕑 Histórico de conversa</div>`));
  body.appendChild(h(`<div id="ro-history" class="ro-card"><div class="card-sub">Carregando histórico…</div></div>`));

  // Lembretes
  body.appendChild(h(`<div class="section-h" style="margin-top:20px">⏰ Lembretes</div>`));
  body.appendChild(h(`<div id="ro-reminders" class="ro-card"><div class="card-sub">Carregando lembretes…</div></div>`));

  roLoadHistory();
  roLoadReminders();
}

async function roLoadBriefing() {
  const host = $("ro-brief");
  if (!host) return;
  host.textContent = "carregando…";
  try {
    const b = await tryJson(BACKEND + "briefing");
    host.textContent = b && b.saudacao ? b.saudacao : "Sem briefing agora.";   // textContent = seguro
  } catch (e) { host.textContent = "Não consegui carregar o briefing."; }
}

async function roLoadHistory() {
  const host = $("ro-history");
  if (!host) return;
  let items = [];
  try {
    const d = await tryJson(BACKEND + "history");
    items = Array.isArray(d) ? d : (d.history || d.messages || []);
  } catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar o histórico.</div>`; return; }
  if (!items.length) { host.innerHTML = `<div class="op-empty">Sem histórico ainda.</div>`; return; }
  host.innerHTML = "";
  items.slice(-30).forEach((it) => {
    const role = it.role || it.actor || "—";
    const txt = it.content || it.text || it.message || "";
    const when = it.ts || it.time || it.created_at || "";
    const row = h(`<div class="ro-hrow"><div class="ro-hmeta"><span class="ro-role">${_esc(role)}</span>${when ? "<span class='ro-when'>" + _esc(String(when)) + "</span>" : ""}</div><div class="ro-htext"></div></div>`);
    row.querySelector(".ro-htext").textContent = String(txt);
    host.appendChild(row);
  });
  host.scrollTop = host.scrollHeight;
}

async function roLoadReminders() {
  const host = $("ro-reminders");
  if (!host) return;
  let items = [];
  try { items = (await tryJson(BACKEND + "reminders")).pending || []; }
  catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar os lembretes.</div>`; return; }
  if (!items.length) { host.innerHTML = `<div class="op-empty">Nenhum lembrete pendente.</div>`; return; }
  host.innerHTML = "";
  items.forEach((r) => {
    const row = h(`<div class="ro-rem"><span class="ro-rem-txt"></span><span class="ro-rem-when">${r.falta_min != null ? "em " + _esc(String(r.falta_min)) + " min" : _esc(String(r.due || ""))}</span></div>`);
    row.querySelector(".ro-rem-txt").textContent = r.text || "(lembrete)";
    host.appendChild(row);
  });
}

export { viewRotina };
