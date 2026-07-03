// Treino — status de treinamento por área — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, state, BACKEND, tryJson, renderCanvas } from "../../app.js";

function viewTreino(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:16px">Pipeline: <b>_entrada</b> (vídeos/repos/PDFs, coletados ou manuais) → resumo no <b>NotebookLM</b> → <b>_resumos</b> entra na base RAG do Javes.</div>`));

  // Treinar direto de um vídeo do YouTube (transcrição → doc → reindexa o RAG).
  body.appendChild(h(`<div class="section-h">📺 Treinar de um vídeo do YouTube</div>`));
  const yt = h(`<div class="demanda" style="max-width:640px">
    <div class="card-sub" style="margin-bottom:8px">Cola a URL: o Javes extrai a transcrição, salva como material de treino e reindexa o RAG na hora.</div>
    <input id="yt-url" class="cs-input" style="width:100%;margin-bottom:8px" placeholder="https://youtube.com/watch?v=…" />
    <div style="text-align:right"><button class="btn ok" id="yt-run">📺 Treinar do vídeo</button></div>
    <div class="yt-out card-sub" style="margin-top:8px"></div>
  </div>`);
  body.appendChild(yt);
  yt.querySelector("#yt-run").onclick = async () => {
    const url = (yt.querySelector("#yt-url").value || "").trim();
    const out = yt.querySelector(".yt-out");
    if (!url) { out.textContent = "Cola a URL do vídeo primeiro."; return; }
    if (!state.online) { out.textContent = "Backend offline."; return; }
    const btn = yt.querySelector("#yt-run"); btn.disabled = true; out.textContent = "Extraindo transcrição e indexando (pode levar ~30s)…";
    try {
      const r = await tryJson(BACKEND + "train/youtube", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
      if (r.error) out.textContent = "⚠️ " + r.error;
      else out.textContent = `✅ "${r.title}" (${r.channel || "canal"}) · ${r.chars} chars → ${r.file}. Reindexando o RAG.`;
    } catch (e) { out.textContent = "Falhou: " + e.message; }
    btn.disabled = false;
  };

  body.appendChild(h(`<div class="section-h" style="margin-top:20px">🎓 Áreas de treino</div>`));
  if (!state.training.length) { body.appendChild(h(`<div class="empty-state">Sem dados de treinamento (backend offline?).</div>`)); return; }
  const grid = h(`<div class="grid cols-2"></div>`);
  state.training.forEach((a) => {
    const ent = a.entrada || 0, res = a.resumos || 0;
    const pc = ent ? Math.round((res / ent) * 100) : 0;
    const card = h(`
      <div class="card">
        <div class="card-head"><div class="card-icon">🎓</div><div><div class="card-title" style="text-transform:capitalize">${a.area}</div><div class="card-sub">${ent} entrada · ${res} resumos</div></div></div>
        <div class="skill-bar" style="margin:6px 0 4px"><div class="skill-fill" style="width:${pc}%"></div></div>
        <div class="card-sub">${pc}% resumido (no RAG)</div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn ok btn-scout">📥 Coletar (YouTube + GitHub)</button>
          <button class="btn no btn-resumir">✍️ Resumir pendentes (Claude)</button>
        </div>
        <div class="scout-out card-sub" style="margin-top:8px"></div>
      </div>`);
    card.querySelector(".btn-scout").onclick = async (e) => {
      const out = card.querySelector(".scout-out");
      e.target.disabled = true; out.textContent = "Coletando matéria-prima (consultando YouTube e GitHub)...";
      if (!state.online) { out.textContent = "Backend offline."; return; }
      try {
        const r = await tryJson(`${BACKEND}treinamento/scout/${a.area}`, { method: "POST" });
        const n = (r.results && r.results.length) || r.coletados || r.total || 0;
        out.textContent = `✅ Coleta concluída. Confira _treinamento/${a.area}/_entrada e suba no NotebookLM.`;
        try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; renderCanvas(); } catch (_) {}
      } catch (err) { out.textContent = "Falhou: " + err.message; e.target.disabled = false; }
    };
    card.querySelector(".btn-resumir").onclick = async (e) => {
      const out = card.querySelector(".scout-out");
      e.target.disabled = true; out.textContent = "Resumindo pendentes com o Claude (pode levar um pouco)...";
      if (!state.online) { out.textContent = "Backend offline."; e.target.disabled = false; return; }
      try {
        const r = await tryJson(`${BACKEND}treinamento/resumir/${a.area}`, { method: "POST" });
        if (r.error) { out.textContent = "⚠️ " + r.error; }
        else { out.textContent = `✅ ${r.resumidos} resumo(s) gerado(s) → entraram no RAG. Pendentes restantes: ${r.pendentes_restantes}.`; }
        try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; renderCanvas(); } catch (_) {}
      } catch (err) { out.textContent = "Falhou: " + err.message; e.target.disabled = false; }
    };
    grid.appendChild(card);
  });
  body.appendChild(grid);
  body.appendChild(h(`<div class="card-sub" style="margin-top:18px">💡 <b>NotebookLM</b> é o passo de resumo (manual — sem API pública): suba o material do <code>_entrada</code>, gere o resumo e cole em <code>_resumos</code>. O Javes indexa automático no RAG.</div>`));
}

export { viewTreino };
