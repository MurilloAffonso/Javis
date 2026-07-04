// Estúdio de Conteúdo — view do Command Center (tema MegaBrain: preto quente + laranja).
// Área guiada e MUITO didática pra Murillo CRIAR e PUBLICAR conteúdo da agência
// (Vem Passear Jampa). Compositor à esquerda (passos → canal → título → texto →
// IA → upload → ações) e Biblioteca à direita (cards com status).
//
// Estado local em memória (não persiste): a biblioteca vive só nesta sessão.
// A ÚNICA escrita real é a geração com IA via POST /chat. Salvar/Publicar apenas
// adicionam um card à biblioteca local (sem endpoint). Todo texto do usuário é
// escapado com _esc antes de ir pro HTML. CSS injetado de forma idempotente.
import { h, $, state, BACKEND, tryJson, _esc, opToast } from "../../app.js";

// ---------- Estado local (só em memória, reseta ao recarregar) ----------
let _projeto = "vempassear"; // default: Vem Passear
let _canal = "instagram";
let _arquivos = []; // [{ nome, url|null, tipo }]

// Cada projeto tem sua própria voz (contexto injetado na IA) e sua própria biblioteca.
const PROJETOS = [
  { id: "vempassear", label: "Vem Passear", ic: "🌊",
    voz: "Escreva no contexto da Vem Passear Jampa (agência de passeios de praia em João Pessoa), tom animado e convidativo de turismo." },
  { id: "pessoal", label: "Javes (pessoal)", ic: "⚡",
    voz: "Escreva no contexto pessoal/profissional do Murillo (criador do assistente de IA Javis), tom direto e técnico-acessível." },
];
const projById = (id) => PROJETOS.find((p) => p.id === id) || PROJETOS[0];
const CANAIS = [
  { id: "instagram", label: "Instagram", ic: "📸" },
  { id: "blog",      label: "Blog",      ic: "📝" },
  { id: "whatsapp",  label: "WhatsApp",  ic: "💬" },
  { id: "youtube",   label: "YouTube",   ic: "▶️" },
];
const canalLabel = (id) => (CANAIS.find((c) => c.id === id) || {}).label || id;

const STATUS_META = {
  rascunho:  { label: "rascunho",  cls: "ct-st-draft" },
  agendado:  { label: "agendado",  cls: "ct-st-sched" },
  publicado: { label: "publicado", cls: "ct-st-pub" },
};

// Biblioteca inicial — uma lista por projeto (em memória).
const _bibliotecas = {
  vempassear: [
    { id: "b1", titulo: "Pôr do Sol do Jacaré: o vídeo que viralizou", canal: "youtube",   status: "publicado" },
    { id: "b2", titulo: "Carrossel: 5 motivos pra conhecer Areia Vermelha", canal: "instagram", status: "agendado" },
    { id: "b3", titulo: "Roteiro de 1 dia em João Pessoa", canal: "blog", status: "rascunho" },
    { id: "b4", titulo: "Promo relâmpago: passeio de catamarã no fim de semana", canal: "whatsapp", status: "rascunho" },
  ],
  pessoal: [
    { id: "p1", titulo: "Como montei meu assistente de IA (Javis)", canal: "blog", status: "publicado" },
    { id: "p2", titulo: "Thread: economia de tokens com Codex", canal: "instagram", status: "agendado" },
    { id: "p3", titulo: "Bastidores do projeto Javis", canal: "youtube", status: "rascunho" },
  ],
};
const biblioteca = () => (_bibliotecas[_projeto] || (_bibliotecas[_projeto] = []));

// ---------- CSS (injetado 1x, idempotente, prefixo ct-) ----------
function ensureStyles() {
  if (document.getElementById("conteudo-styles")) return;
  const st = document.createElement("style");
  st.id = "conteudo-styles";
  st.textContent = `
  .ct-wrap { display:grid; grid-template-columns:1fr 340px; gap:18px; align-items:start; }
  @media (max-width: 980px) { .ct-wrap { grid-template-columns:1fr; } }

  .ct-intro { font-size:13px; color:var(--muted); margin-bottom:14px; line-height:1.5; }
  .ct-intro b { color:var(--text); }

  /* Trilha de passos */
  .ct-steps { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:18px; }
  .ct-step { display:flex; align-items:center; gap:8px; padding:7px 12px; border-radius:99px;
    background:var(--card); border:1px solid var(--border); color:var(--muted); font-size:12.5px; font-weight:600; }
  .ct-step .ct-step-n { width:19px; height:19px; border-radius:50%; display:grid; place-items:center;
    background:var(--border-2); color:var(--text); font-size:11px; font-weight:700; }
  .ct-step.active { background:var(--accent-soft); border-color:transparent; color:#ffd9b3; }
  .ct-step.active .ct-step-n { background:var(--accent); color:#1a0f06; }
  .ct-step-sep { color:var(--muted-2); font-size:15px; }

  /* Cartão do compositor */
  .ct-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:18px; }
  .ct-block { margin-bottom:16px; }
  .ct-label { display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:4px; letter-spacing:.2px; }
  .ct-hint { font-size:11.5px; color:var(--muted-2); margin:2px 0 8px; line-height:1.4; }

  /* Chips de canal */
  .ct-chips { display:flex; gap:8px; flex-wrap:wrap; }
  .ct-chip { display:flex; align-items:center; gap:6px; padding:7px 12px; border-radius:var(--radius-sm);
    background:var(--card); border:1px solid var(--border-2); color:var(--muted); font-size:12.5px; font-weight:600;
    cursor:pointer; transition:border-color .15s, color .15s, background .15s; font-family:var(--font); }
  .ct-chip:hover { border-color:var(--accent); color:var(--text); }
  .ct-chip.active { background:var(--accent-soft); border-color:transparent; color:#ffd9b3; }

  /* Inputs */
  .ct-input, .ct-textarea { width:100%; box-sizing:border-box; background:var(--bg); color:var(--text);
    border:1px solid var(--border-2); border-radius:var(--radius-sm); padding:10px 12px; font-size:13px;
    font-family:var(--font); outline:none; transition:border-color .15s; }
  .ct-input:focus, .ct-textarea:focus { border-color:var(--accent); }
  .ct-input::placeholder, .ct-textarea::placeholder { color:var(--muted-2); }
  .ct-textarea { min-height:200px; resize:vertical; line-height:1.55; }

  /* Botões */
  .ct-btn { display:inline-flex; align-items:center; gap:7px; padding:9px 15px; border-radius:var(--radius-sm);
    font-size:12.5px; font-weight:700; cursor:pointer; font-family:var(--font); border:1px solid transparent;
    transition:filter .15s, background .15s, border-color .15s; }
  .ct-btn:disabled { opacity:.6; cursor:default; }
  .ct-btn-ai { background:linear-gradient(135deg, var(--accent), var(--accent-2)); color:#1a0f06; }
  .ct-btn-ai:hover:not(:disabled) { filter:brightness(1.08); }
  .ct-btn-primary { background:var(--accent-soft); color:#ffd9b3; border-color:transparent; }
  .ct-btn-primary:hover:not(:disabled) { background:var(--accent); color:#1a0f06; }
  .ct-btn-ghost { background:var(--card); color:var(--text); border-color:var(--border-2); }
  .ct-btn-ghost:hover:not(:disabled) { border-color:var(--accent); }
  .ct-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:6px; }

  /* Dropzone de upload */
  .ct-drop { border:2px dashed var(--border-2); border-radius:var(--radius-sm); padding:22px 16px; text-align:center;
    color:var(--muted); cursor:pointer; transition:border-color .15s, background .15s; background:var(--bg); }
  .ct-drop:hover, .ct-drop.drag { border-color:var(--accent); background:var(--accent-soft); color:#ffd9b3; }
  .ct-drop .ct-drop-ic { font-size:24px; display:block; margin-bottom:6px; }
  .ct-drop .ct-drop-sub { font-size:11.5px; color:var(--muted-2); margin-top:3px; }
  .ct-drop input[type=file] { display:none; }

  .ct-thumbs { display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
  .ct-thumb { width:78px; }
  .ct-thumb img, .ct-thumb .ct-thumb-ph { width:78px; height:78px; border-radius:var(--radius-sm); object-fit:cover;
    border:1px solid var(--border-2); background:var(--card-hover); display:grid; place-items:center; font-size:22px; color:var(--muted-2); }
  .ct-thumb .ct-thumb-nome { font-size:10px; color:var(--muted-2); margin-top:4px; white-space:nowrap; overflow:hidden;
    text-overflow:ellipsis; }

  /* Biblioteca */
  .ct-lib-h { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
  .ct-lib-title { font-size:13px; font-weight:700; color:var(--text); }
  .ct-count { background:var(--accent-soft); color:#ffd9b3; border-radius:99px; padding:1px 9px; font-size:11px; font-weight:700; }
  .ct-lib-list { display:flex; flex-direction:column; gap:10px; }
  .ct-lib-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius-sm); padding:12px 13px;
    transition:border-color .15s, transform .15s; }
  .ct-lib-card:hover { border-color:var(--border-2); transform:translateY(-1px); }
  .ct-lib-card.ct-new { border-color:var(--accent); animation:ct-pop .5s ease; }
  @keyframes ct-pop { from { opacity:0; transform:translateY(-6px); } to { opacity:1; transform:none; } }
  .ct-lib-card .ct-lc-title { font-size:12.5px; font-weight:600; color:var(--text); line-height:1.35; margin-bottom:7px; }
  .ct-lc-foot { display:flex; align-items:center; justify-content:space-between; gap:8px; }
  .ct-lc-canal { display:flex; align-items:center; gap:6px; font-size:11px; color:var(--muted); }
  .ct-lc-canal .ct-dot { width:7px; height:7px; border-radius:50%; background:var(--accent); }
  .ct-tag { font-size:10.5px; font-weight:700; padding:2px 9px; border-radius:99px; letter-spacing:.3px; text-transform:uppercase; }
  .ct-st-draft { background:var(--card-hover); color:var(--muted); border:1px solid var(--border-2); }
  .ct-st-sched { background:var(--accent-soft); color:#ffd9b3; }
  .ct-st-pub   { background:rgba(123,209,74,.15); color:var(--ok); }
  `;
  document.head.appendChild(st);
}

// ---------- View principal ----------
export function viewConteudo(body) {
  ensureStyles();

  const root = h(`<div>
    <div class="ct-intro">🎬 <b>Estúdio de Conteúdo.</b> Aqui você <b>escreve, monta e organiza</b> os posts.
      Escolha o projeto, siga os 3 passos: escreva o texto (a IA ajuda), revise e então salve ou agende. Nada é publicado nas redes automaticamente — você tem sempre a palavra final.</div>
    <div class="ct-projsel"></div>
    <div class="ct-wrap">
      <div class="ct-col-left"></div>
      <div class="ct-col-right"></div>
    </div>
  </div>`);
  body.appendChild(root);

  root.querySelector(".ct-projsel").appendChild(buildProjetoSel());
  root.querySelector(".ct-col-left").appendChild(buildCompositor());
  root.querySelector(".ct-col-right").appendChild(buildBiblioteca());

  carregarBackend(); // puxa o que já foi salvo no servidor pro projeto ativo
}

// ---------- Seletor de projeto (define voz da IA + biblioteca ativa) ----------
function buildProjetoSel() {
  const wrap = h(`<div class="ct-block">
    <label class="ct-label">Projeto</label>
    <div class="ct-hint">Define a "voz" que a IA usa e qual biblioteca de conteúdos aparece à direita.</div>
    <div class="ct-chips ct-proj-chips"></div>
  </div>`);
  const chips = wrap.querySelector(".ct-chips");
  PROJETOS.forEach((p) => {
    const chip = h(`<button class="ct-chip${p.id === _projeto ? " active" : ""}">${p.ic} ${_esc(p.label)}</button>`);
    chip.onclick = () => {
      if (_projeto === p.id) return;
      _projeto = p.id;
      chips.querySelectorAll(".ct-chip").forEach((el) => el.classList.remove("active"));
      chip.classList.add("active");
      renderLibList(); // troca a biblioteca exibida
      carregarBackend(); // e puxa os salvos desse projeto (1x)
    };
    chips.appendChild(chip);
  });
  return wrap;
}

// ---------- Trilha de passos ----------
function buildSteps(activeIdx) {
  const wrap = h(`<div class="ct-steps"></div>`);
  const passos = ["Escrever", "Revisar", "Publicar"];
  passos.forEach((p, i) => {
    if (i > 0) wrap.appendChild(h(`<span class="ct-step-sep">→</span>`));
    wrap.appendChild(h(`<div class="ct-step${i === activeIdx ? " active" : ""}"><span class="ct-step-n">${i + 1}</span>${_esc(p)}</div>`));
  });
  return wrap;
}

// ---------- Compositor (coluna esquerda) ----------
function buildCompositor() {
  const card = h(`<div class="ct-card"></div>`);
  card.appendChild(buildSteps(0)); // passo atual: 1 Escrever

  // Canal
  const blkCanal = h(`<div class="ct-block">
    <label class="ct-label">1. Escolha o canal</label>
    <div class="ct-hint">Onde este conteúdo vai ser publicado? Isso ajusta o tom que a IA usa.</div>
    <div class="ct-chips"></div>
  </div>`);
  const chips = blkCanal.querySelector(".ct-chips");
  CANAIS.forEach((c) => {
    const chip = h(`<button class="ct-chip${c.id === _canal ? " active" : ""}">${c.ic} ${_esc(c.label)}</button>`);
    chip.onclick = () => {
      _canal = c.id;
      chips.querySelectorAll(".ct-chip").forEach((el) => el.classList.remove("active"));
      chip.classList.add("active");
    };
    chips.appendChild(chip);
  });
  card.appendChild(blkCanal);

  // Título
  const blkTitulo = h(`<div class="ct-block">
    <label class="ct-label" for="ct-titulo">2. Título do conteúdo</label>
    <div class="ct-hint">Uma frase curta que resume o post (ex.: "Passeio de escuna ao pôr do sol").</div>
    <input id="ct-titulo" class="ct-input" placeholder="digite um título..." />
  </div>`);
  card.appendChild(blkTitulo);

  // Corpo do post
  const blkTexto = h(`<div class="ct-block">
    <label class="ct-label" for="ct-texto">3. Texto do post</label>
    <div class="ct-hint">Escreva o rascunho aqui — ou deixe uma ideia solta e peça pra IA desenvolver no botão abaixo.</div>
    <textarea id="ct-texto" class="ct-textarea" placeholder="Escreva o corpo do post... (dica: quanto mais contexto, melhor a IA ajuda)"></textarea>
  </div>`);
  card.appendChild(blkTexto);

  // Botão IA
  const blkIA = h(`<div class="ct-block ct-actions"></div>`);
  const btnAI = h(`<button class="ct-btn ct-btn-ai" type="button">✨ Escrever com IA</button>`);
  btnAI.onclick = () => gerarComIA(btnAI);
  blkIA.appendChild(btnAI);
  card.appendChild(blkIA);

  // Upload
  card.appendChild(buildUpload());

  // Ações finais
  const blkAcoes = h(`<div class="ct-block">
    <label class="ct-label">4. Finalizar</label>
    <div class="ct-hint">Salve como rascunho pra continuar depois, ou agende/publique pra mandar pra fila.</div>
    <div class="ct-actions"></div>
  </div>`);
  const acoes = blkAcoes.querySelector(".ct-actions");
  const bDraft = h(`<button class="ct-btn ct-btn-ghost" type="button">💾 Salvar rascunho</button>`);
  bDraft.onclick = () => salvarItem("rascunho");
  const bPub = h(`<button class="ct-btn ct-btn-primary" type="button">📤 Agendar / Publicar</button>`);
  bPub.onclick = () => salvarItem("agendado");
  acoes.append(bDraft, bPub);
  card.appendChild(blkAcoes);

  return card;
}

// ---------- Upload (dropzone + preview local) ----------
function buildUpload() {
  const blk = h(`<div class="ct-block">
    <label class="ct-label">Imagens (opcional)</label>
    <div class="ct-hint">Anexe fotos dos passeios. Ficam só aqui na tela (pré-visualização) — não sobem pra nenhum servidor.</div>
    <label class="ct-drop">
      <span class="ct-drop-ic">🖼️</span>
      <span>Arraste imagens ou clique pra escolher</span>
      <span class="ct-drop-sub">JPG, PNG — várias de uma vez</span>
      <input type="file" accept="image/*" multiple />
    </label>
    <div class="ct-thumbs"></div>
  </div>`);
  const drop = blk.querySelector(".ct-drop");
  const input = blk.querySelector("input[type=file]");
  const thumbs = blk.querySelector(".ct-thumbs");

  const addFiles = (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    files.forEach((f) => {
      const isImg = (f.type || "").startsWith("image/");
      _arquivos.push({ nome: f.name, tipo: f.type, url: isImg ? URL.createObjectURL(f) : null });
    });
    renderThumbs(thumbs);
    opToast(`${files.length} arquivo(s) anexado(s).`, "ok");
  };

  input.onchange = () => { addFiles(input.files); input.value = ""; };
  ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("drag"); }));
  drop.addEventListener("drop", (e) => { addFiles(e.dataTransfer && e.dataTransfer.files); });

  renderThumbs(thumbs);
  return blk;
}

function renderThumbs(host) {
  host.innerHTML = "";
  _arquivos.forEach((a) => {
    const t = h(`<div class="ct-thumb"></div>`);
    if (a.url) {
      const img = h(`<img alt="" />`);
      img.src = a.url;
      t.appendChild(img);
    } else {
      t.appendChild(h(`<div class="ct-thumb-ph">📄</div>`));
    }
    const nome = h(`<div class="ct-thumb-nome"></div>`);
    nome.textContent = a.nome;
    nome.title = a.nome;
    t.appendChild(nome);
    host.appendChild(t);
  });
}

// ---------- Geração com IA (POST /chat) ----------
async function gerarComIA(btn) {
  if (!state.online) {
    opToast("Pra escrever com IA você precisa do backend ligado (:8000).", "warn");
    return;
  }
  const titulo = ($("ct-titulo").value || "").trim();
  const rascunho = ($("ct-texto").value || "").trim();
  const prompt =
    `${projById(_projeto).voz}\n` +
    `Escreva um conteúdo pronto para o canal ${canalLabel(_canal)}, em português do Brasil, com chamada para ação.\n` +
    `Título/tema: ${titulo || "(sem título — sugira um)"}\n` +
    `Rascunho/ideia do usuário: ${rascunho || "(vazio — crie do zero a partir do tema)"}\n` +
    `Devolva apenas o texto final do post, sem explicações.`;

  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = "✨ gerando…";
  try {
    const data = await tryJson(BACKEND + "chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt }),
    });
    const texto = (data && (data.response ?? data.text)) || "";
    if (texto && String(texto).trim()) {
      $("ct-texto").value = String(texto).trim();
      opToast("Texto gerado. Revise antes de publicar. ✨", "ok");
    } else {
      opToast("A IA não devolveu texto. Tente de novo com mais contexto.", "warn");
    }
  } catch (e) {
    opToast("Falhou ao gerar: " + (e && e.message ? e.message : e), "err");
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

// ---------- Salvar/Publicar na biblioteca local ----------
function salvarItem(status) {
  const titulo = ($("ct-titulo").value || "").trim();
  if (!titulo) { opToast("Dê um título ao conteúdo antes de salvar.", "warn"); return; }
  const corpo = ($("ct-texto") ? $("ct-texto").value : "").trim();
  const item = { id: "u" + Date.now(), titulo, canal: _canal, status, _novo: true };
  biblioteca().unshift(item);
  renderLibList();
  opToast(status === "rascunho" ? "Rascunho salvo na biblioteca. 💾" : "Conteúdo agendado na biblioteca. 📤", "ok");
  // Persiste no backend (não bloqueia a UI; só avisa se falhar).
  if (state.online) {
    tryJson(BACKEND + "conteudo", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: _projeto, channel: _canal, title: titulo, body: corpo, status }),
    }).catch(() => opToast("Salvo aqui, mas falhou ao gravar no servidor.", "warn"));
  }
}

// ---------- Carrega itens já salvos no backend (uma vez por projeto) ----------
const _carregado = {};
function carregarBackend() {
  if (!state.online || _carregado[_projeto]) return;
  const proj = _projeto;
  _carregado[proj] = true;
  tryJson(BACKEND + "conteudo?projeto=" + encodeURIComponent(proj)).then((d) => {
    const itens = (d.itens || []).map((r) => ({
      id: "db" + r.id, titulo: r.title || "(sem título)",
      canal: r.channel || "instagram", status: r.status || "rascunho",
    }));
    if (!itens.length) return;
    const lib = _bibliotecas[proj] || (_bibliotecas[proj] = []);
    const existentes = new Set(lib.map((x) => x.id));
    _bibliotecas[proj] = [...itens.filter((x) => !existentes.has(x.id)), ...lib];
    if (_projeto === proj) renderLibList();
  }).catch(() => {});
}

// ---------- Biblioteca (coluna direita) ----------
function buildBiblioteca() {
  const card = h(`<div class="ct-card">
    <div class="ct-lib-h">
      <span class="ct-lib-title">📚 Biblioteca</span>
      <span class="ct-count" id="ct-lib-count">0</span>
    </div>
    <div class="ct-hint" style="margin-top:-4px">Tudo o que você criou. Novos itens aparecem no topo.</div>
    <div class="ct-lib-list" id="ct-lib-list"></div>
  </div>`);
  // Adia o render pra depois de anexar (getElementById precisa estar no DOM),
  // mas como preenchemos o próprio nó aqui, montamos direto:
  fillLibList(card.querySelector("#ct-lib-list"), card.querySelector("#ct-lib-count"));
  return card;
}

function fillLibList(list, count) {
  const lib = biblioteca();
  list.innerHTML = "";
  count.textContent = String(lib.length);
  if (!lib.length) {
    list.appendChild(h(`<div class="ct-hint">Nenhum conteúdo ainda. Crie o primeiro ao lado. 👈</div>`));
    return;
  }
  lib.forEach((it) => {
    const meta = STATUS_META[it.status] || STATUS_META.rascunho;
    const card = h(`<div class="ct-lib-card${it._novo ? " ct-new" : ""}">
      <div class="ct-lc-title"></div>
      <div class="ct-lc-foot">
        <span class="ct-lc-canal"><span class="ct-dot"></span><span class="ct-lc-canal-nome"></span></span>
        <span class="ct-tag ${meta.cls}">${_esc(meta.label)}</span>
      </div>
    </div>`);
    card.querySelector(".ct-lc-title").textContent = it.titulo;
    card.querySelector(".ct-lc-canal-nome").textContent = canalLabel(it.canal);
    list.appendChild(card);
    it._novo = false; // destaque só na primeira renderização
  });
}

// Re-render da lista quando algo muda (usa os nós já no DOM).
function renderLibList() {
  const list = $("ct-lib-list"), count = $("ct-lib-count");
  if (list && count) fillLibList(list, count);
}
