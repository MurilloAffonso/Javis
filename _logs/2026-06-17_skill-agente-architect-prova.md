# Prova de conceito — agente com SKILL + cérebro forte (Architect) (17/06)

**Pergunta do Murillo:** qual o grau de treinamento dos 17 agentes? Têm contexto
ou precisam ser treinados? (+ avaliou 7 repos, gostou de mattpocock/skills).

**Resposta honesta (do código):** os 17 agentes NÃO têm treinamento. Cada um é um
`system_prompt` (persona) rodando no `llama3.2:3b` (fraco), sem memória própria nem
RAG. O trabalho pesado real é do Claude (assinatura) + Codex. O caminho certo NÃO é
fine-tuning — é **skills** (playbooks markdown) + ligar ao RAG/memória que já existe.
Javis já tem a semente: `skill_forge.py`, `_treinamento/`+`knowledge.py`, `_memoria/`.

**Decisão:** Murillo pediu minha recomendação → escolhi "provar com 1 agente" (fatia
vertical, risco mínimo, vira molde pros outros 16).

## O que foi construído
- **`_skills/agente-architect.md`** (NOVO) — skill real do Architect (formato SKILL.md:
  identidade, quando usar, processo, saída esperada, regras invioláveis).
- **`claude_brain.answer`** — ganhou parâmetros `system` (persona+skill do agente,
  sobrescreve o prompt de voz curto) e `timeout`. **BUG REAL corrigido:** o
  `subprocess.run` usava `text=True` sem `encoding` → no Windows decodificava a saída
  UTF-8 do Claude com cp1252, o que esvaziava/corrompia a resposta (foi por isso que o
  1º teste voltou vazio). Agora `encoding="utf-8", errors="replace"`.
- **`agent_runner.py`** (NOVO) — `run_agent(agent_id, task)`: carrega a skill, puxa RAG
  (`knowledge.answer_context`), monta `system = persona + skill`, e roteia o raciocínio
  em 3 níveis: **Claude (assinatura) → OpenAI gpt-4o → Ollama**. Os ids batem com
  `specialized.py` e o frontend → escala só adicionando `_skills/agente-<id>.md`.
- **`POST /agents/run`** (server.py) — `{agent_id, task}` → executa e devolve.

## Verificação real (end-to-end, via endpoint com RAG do servidor)
Tarefa: "desenhe a estrutura de uma biblioteca de skills para os 17 agentes".
Resultado: `brain=claude`, `used_skill=true`, **6673 chars**, 190s. Qualidade:
- Seguiu a skill à risca (Objetivo→Reúso→Estrutura→Conexões→Riscos→Plano).
- **Fundamentado em arquivos reais** (citou `agent_runner.py`, `specialized.py`,
  `skill_forge.py`, `test_intent_consistency.py`) — porque o `claude_brain` roda na
  pasta do projeto e o Claude lê os arquivos sozinho (tem Read/Grep; só Bash/Edit/Write
  bloqueados).
- Pegou o problema arquitetural real (dupla fonte de verdade: `system_prompt` Python vs
  skill `.md`) e um risco de bug (mover skill quebraria o `_load_skill` silenciosamente).
- `pytest tests/` → **54/54**. Server importa limpo.

## Conclusão
A arquitetura skill + cérebro forte funciona e entrega MUITO acima de um persona no
llama3.2:3b. Vira o molde pros outros 16.

## Pontas soltas (follow-up)
- **RAG retornou vazio** (`used_rag=false`) mesmo via endpoint — índice do `knowledge.py`
  pode não estar completo / threshold 0.25 alto. Não foi fatal porque o Claude lê os
  arquivos direto, mas precisa olhar pro caminho OpenAI/Ollama (que dependem do RAG).
- **Dupla fonte de verdade** (apontada pelo próprio Architect): decidir que a skill `.md`
  manda e encolher o `system_prompt` Python pra fallback mínimo, antes de escalar.
- Latência de 190s no Claude headless — ok pra "rodar agente numa tarefa", não pra voz.
- Ligar o clique no agente (UI) a esse endpoint — próximo passo de UX.

**Sem commit/push. Murillo revisa e comita.**

---

## Continuação — escala via Codex (Claude em 86%, economizando até o reset)

Murillo pediu pra delegar ao Codex (tokens de sobra) enquanto o plano Claude
não reseta. Eu só orquestrei e validei barato. Feito:

1. **Correção da dupla fonte de verdade** (implementada por mim, versão segura):
   `agent_runner._compose_system` — se há skill `.md`, ela é a fonte única (persona
   Python não entra); sem skill, usa a persona Python como fallback. `BaseAgent.execute`
   ganhou param `system`. Verificado local (architect=skill única; devops=fallback). 54/54.
2. **16 skills criadas pelo Codex** (2 lotes paralelos, sem tocar código, sem commit):
   - Especialistas: developer, ux_designer, qa, pm, po, scrum, analyst, devops, data_engineer.
   - Conclave/meta: jarvis_soul, aios_master, squad_creator, rootcause, critico, advogado, sintetizador.
   - Validei todas: frontmatter ok, seções ok, acentuação ok, zero mojibake.
   - **Total: 17/17 agentes com skill** em `_skills/agente-<id>.md`.
3. **Guardrail (Codex):** `tests/test_skills_consistency.py` — 1 teste por agente (existe +
   frontmatter + seções). Suíte subiu de 54 → **71 testes, todos verdes** (confirmei eu mesmo).
4. **Manifesto (Codex):** `_skills/_index.md` — tabela dos 17 (id/nome/papel/arquivo/status).

**Pendente pro reset (Claude no máximo):**
- Testar 2-3 skills do Codex de verdade (qualidade) — via OpenAI (barato) ou Claude.
- `_persona` resolver conclave/meta (6 não estão no AGENT_REGISTRY → papel vazio no header).
- Ligar o clique do agente na UI ao `/agents/run`.

Nenhum commit. Claude preservado a sessão toda.

---

## Continuação 2 — pós-reset (Claude no máximo, 17/06)

1. **Saúde confirmada:** `pytest tests/` → 71/71 antes de qualquer mudança nova.
2. **Fix do `_persona` (gap dos 6 conclave/meta) — feito:**
   `agent_runner._persona` agora resolve `aios_master, squad_creator, rootcause,
   critico, advogado, sintetizador` (antes só os 11 do `AGENT_REGISTRY`). Cascata:
   `AGENT_REGISTRY` → `Rootcause` (meta.py, classe real) → `_EXTRA_PERSONAS` (dict
   de rede pros 5 sem classe) → fallback genérico. Verificado: todos os 6 retornam
   nome/papel certo e `used_skill=True`.
3. **Teste de qualidade real (não só estrutural):** rodei o **Developer** via
   `/agents/run` (brain=claude, used_skill=true, used_rag=true, 3811 chars) pedindo
   pra revisar o próprio fix do `_persona`. Resultado: review grounded, achou 2
   problemas reais (não inventados):
   - `squad_creator` tinha role divergente do `META_AGENTS_INFO` ("dinamicamente" vs
     "novas") — **corrigido**, agora alinhado.
   - `rootcause` não tinha rede no `_EXTRA_PERSONAS` (dependia só do import de
     `Rootcause` funcionar) — **corrigido**, adicionado como rede de segurança.
   - Riscos restantes (não corrigidos, baixo impacto): fallback sem skill pros 5
     ainda não lê os `SYSTEM_*` reais de `meta.py`/`conclave.py` (só nome+papel);
     3º brain (Ollama) não cobre os 6 (silencioso se Claude e OpenAI caírem).
4. **Confirma:** a arquitetura skill+RAG+cérebro forte não só "funciona" — o
   Developer com skill real revisou código de produção e achou bug de verdade.

**Próximo:** ligar o clique do agente na UI (`Mente`/gallery) ao `/agents/run`.

Nenhum commit. Claude preservado.

---

## Continuação 3 — clique real na UI (17/06, mesma sessão pós-reset)

5. **`openAgentChat` (app.js) virou chamada real**, não só pré-encher input:
   clique no card → `window.prompt` pede a tarefa → mostra a pergunta no chat →
   `typing...` → `POST /agents/run {agent_id, task}` → renderiza resposta com
   `renderMarkdown` + tag de meta `🧠 <brain>`. Erro de rede/agente cai num
   `appendMsg('error', ...)` em vez de travar silenciosamente.
6. **Testado de ponta a ponta no browser (Playwright), não só lido o código:**
   abri a aba **Mente**, confirmei os 17 cards renderizados, simulei o clique no
   card **Developer** (mock de `window.prompt`) e confirmei no DOM: mensagem do
   usuário (`@Developer: ...`), resposta da skill via Claude no chat, e a tag
   `🧠 claude` no meta da bolha. Zero erro de console novo (só o 404 de favicon,
   pré-existente).
7. `node --check app.js` limpo. `pytest tests/` → 71/71 (não tocou backend).

**Os 3 pendentes do plano original estão fechados:**
qualidade real testada (Developer achou bug de verdade) ✅, gap do `_persona`
fechado ✅, clique da UI ligado ao `/agents/run` ✅.

**Sem commit/push — Murillo revisa e decide o que comita.**
