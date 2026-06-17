# Frente 1 — Memória unificada + interface proativa (17/06, manhã/tarde)

**Contexto:** Murillo voltou pra produzir e apontou que a interface não é
proativa e que o Javis "não sabe o que a gente fez" — ao perguntar sobre o
projeto, ele não tinha entendimento, não recebia com "olá senhor, ontem o
orquestrador fez tal". Pediu plano de reestruturação/organização.

**Decisões do Murillo (via pergunta):**
1. Prioridade: **memória + proatividade** primeiro.
2. Divisão: **Codex autônomo em paralelo** numa frente isolada.
3. "Cérebro na nuvem": **melhorar a ponte Telegram** (já existe) em vez de
   expor o servidor web pra fora.

## Diagnóstico real (verificado no código, não chute)

A causa da queixa: o cérebro de voz/chat recebia só o **histórico de chat
recente** como contexto. Nunca lia `_estado/estado-atual.md`, os `_logs/`
nem as decisões. A tool `buscar_conhecimento` (RAG) só dispara se o LLM
resolver usá-la — e mesmo assim não cobria bem logs/estado. Resultado: o
Javis não conseguia te contar o que foi feito.

Outras constatações:
- Três memórias separadas que não conversam: `_memoria/` + `embeddings.jsonl`
  (MemoryBridge), `knowledge.py` (RAG próprio) e a memória do Claude Code.
  Obsidian no repo mas sem ponte automática.
- Cérebro Claude "na nuvem" JÁ existe e funciona: `claude_brain.py` roda
  Opus 4.8 pela assinatura (sem gastar API), em streaming por voz — mas roda
  LOCAL (subprocesso), e só em perguntas "profundas", e SEM contexto do
  projeto.
- ~6 scripts de rascunho soltos no backend (`_debug_*`, `_read_*`, `_run_*`,
  `_test_openrouter`).

## O que fiz (Frente 1 — eu, Claude)

**`briefing.py` (NOVO)** — ponte de estado. Lê estado atual, último log,
decisões e pendências (`- [ ]`) e monta um resumo factual conciso (linhas de
sessão truncadas a 170 chars, cacheado 15s). Funções: `estado_resumido()`,
`saudacao_proativa()`, `briefing_dict()`.

**Injeção no cérebro:**
- `agent._system()` agora anexa o bloco "Estado atual do projeto Javis" →
  TODO cérebro (voz e chat) passa a conhecer o estado sem depender de
  acionar ferramenta.
- `server.py` (fluxo de voz profundo `claude_brain`) também recebe o estado
  no contexto, além do histórico.

**Endpoint `/briefing`** + **saudação proativa no frontend**: ao abrir, o
Javis mostra "Boa tarde, senhor. No nosso último trabalho (data), ..." num
balão violeta destacado (`.msg-briefing`). `app.js` `loadBriefing()`,
estilo em `style.css`.

**Pendências reais convertidas pra `- [ ]`** em `proximos-passos.md`
(ElevenLabs, Figma, resumir vídeos, voz, proatividade extra) — pra o
briefing capturá-las e o Javis cobrar.

## Verificação real (não "deve funcionar")
- Saudação testada no **browser via Playwright**: renderizou com acentuação
  correta ("Boa tarde, senhor. No nosso último trabalho (2026-06-17), sessão
  noturna de orquestração — Javis ↔ Cérebro Jampa."), estilo violeta
  aplicado. Único erro de console é `favicon.ico` 404 (pré-existente).
- `agent._system()` confirmado incluindo o bloco de estado (2393 chars).
- **Teste end-to-end real** (`POST /chat`): perguntei "o que a gente fez e o
  que está pendente?" → respondeu "Na última sessão, orquestramos o Javis com
  o Cérebro Jampa e fechamos o backlog do Codex." E depois listou as
  pendências reais (ElevenLabs, Figma, vídeos, voz). Antes ele não sabia.
- Suíte `tests/`: **54/54 passando**. `import server` limpo.

Nota: o terminal Windows (cp1252) NÃO consegue exibir UTF-8 — todo print de
acento aparece como mojibake/`�`, mas os dados estão corretos (comprovado no
browser e via `json.load` sem erro). Não é bug do projeto, é limitação do
console; sempre validar no browser, não no stdout do terminal.

## Frente paralela (Codex, `codex exec`, SEM commit)
Codex organizou o backend em background: moveu os 6 scripts de rascunho pra
`backend/_scratch/` (+ README) e criou `backend/ARQUITETURA.md` documentando
cada módulo de produção. Validei: acentuação correta (32 acentos, 0
mojibake), não tocou nos meus arquivos, **não commitou** (HEAD intacto).
Adicionei `briefing.py` ao ARQUITETURA.md eu mesmo (módulo novo).

## Próximo (não feito ainda)
- Frente 2+: feed do "que o orquestrador fez" na UI (além da saudação).
- Frente 3: afinar voz (wake word, latência, ASR).
- Conectar de fato as 3 memórias + Obsidian num índice só (hoje o briefing
  resolve a exatidão prática, mas a unificação dos índices ainda é tema).
- Melhorar a ponte Telegram (decisão do Murillo de priorizar isso pro
  celular).

**Nenhum commit/push. Murillo revisa e comita.**

---

## Aba "Mente" — organograma dos agentes (mesmo dia, pedido do Murillo)

Murillo enviou foto de um board FigJam "AI Agents for Sales" e pediu pra
recriar a hierarquia dos agentes do Javis. Caminho:
1. Montei a spec da hierarquia em `_prompts/figma-hierarquia-agentes-javis.md`
   a partir do `GALLERY_AGENTS` real (12 agentes).
2. Codex (que TEM o MCP Figma, eu não) criou o board:
   `https://www.figma.com/design/oQy33GZs5cHe4me4N1k5pj?node-id=4-2` na conta
   affonsomurillo17@gmail.com. RESSALVA honesta: saiu como PNG (não cards
   editáveis) porque o conector `use_figma` foi cancelado, e bateu no limite
   do plano Starter — não consegui ver o render pra garantir qualidade.
3. Murillo então pediu pra fazer **nativo na interface** ("na mente"). Criei
   a aba **Mente** 🧠 (sidebar entre Agentes e Workflows): organograma em
   árvore CSS (técnica clássica de conectores com bordas), card por agente
   (emoji, nome, @papel, tag de esquadrão colorida, status dot, borda
   colorida por squad), clicável → `openAgentChat()`.
   - Arquivos: `index.html` (botão + view-mente), `app.js` (`ORG_TREE`,
     `renderOrgChart`, hook no `switchView`, `VIEW_TITLES`), `style.css`
     (bloco `.org-chart`/`.org-card`).
   - Hierarquia: Orion (raiz) → Titan/Vera/Dara/Recap → Vendas
     (Khan/Phantom/Blade/Brief) sob Titan, Dados (Intel/Prism/Ana) sob Dara.
   - **Verificado no browser (Playwright):** 12 cards, raiz Orion, árvore
     correta, zero erro novo (só favicon 404 pré-existente). Screenshot em
     `_outbox/2026-06-17_aba-mente-organograma.png`.

Lição: fazer nativo na UI > imagem estática no Figma — interativo, testável,
sem limite de plano externo. O Figma fica como referência/export, não como
o produto.
