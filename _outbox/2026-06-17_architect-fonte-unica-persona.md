# Architect (agente do Javis) — design da correção da dupla fonte de verdade

_Gerado pelo agente Architect via /agents/run (skill + RAG + Claude). Teste real 17/06._

---

## Architect — Correção da dupla fonte de verdade

**Objetivo:** Eliminar a duplicação de persona entre `specialized.py` (string `system_prompt`) e `_skills/agente-<id>.md`, definindo uma única fonte que governa o comportamento do agente.

**Reúso (o que já existe):**
- `agents/specialized.py:65-71` — `Architect.system_prompt` (persona em string) + `AgentMeta` (id/name/role/icon/color).
- `agent_runner.py:17-28` — `_load_skill()` já lê o `.md` e remove frontmatter.
- `agent_runner.py:31-40` — `_persona()` já puxa `name` + `system_prompt` do registro.
- `agent_runner.py:60-63` — já compõe `system = base_prompt + skill`. **A composição já existe — o problema é que `base_prompt` repete o que o `.md` diz.**

### Quem manda: o `.md` (`_skills/agente-<id>.md`)

Razão: é editável sem mexer em código, é onde mora a capacidade real (skill), e o `agent_runner` já o trata como autoridade ("siga à risca"). O Python vira **só metadados + fallback mínimo**.

```
Hoje (duas verdades):                  Alvo (uma verdade):

specialized.py                          specialized.py
  ├ AgentMeta  (id,name,role…)            └ AgentMeta  (id,name,role…)   ← só isto
  └ system_prompt: persona LONGA   ✗      └ system_prompt: 1 linha de meta (fallback)
_skills/agente-architect.md              _skills/agente-architect.md  ← FONTE
  └ persona + skill (repete persona) ✗     └ persona + skill (única)
```

### Estrutura (responsabilidades)

| Parte | Faz | NÃO faz |
|---|---|---|
| `_skills/agente-<id>.md` | persona + comportamento completos (fonte) | — |
| `specialized.py / AgentMeta` | identidade visível (id, name, role, icon, color) | não guarda persona longa |
| `specialized.py / system_prompt` | **1 linha** derivada da meta — só fallback se `.md` sumir | não duplica a skill |
| `agent_runner.py` | compõe `system` = header curto (meta) + skill (`.md`) | não inventa persona |

### Conexões

`run_agent` → `_persona()` devolve `name` + prompt-mínimo-da-meta → `_load_skill()` devolve o `.md` → `system = header + skill` → Claude/OpenAI/Ollama. Se `.md` faltar, cai no prompt-mínimo da meta (agente ainda responde, sem comportamento rico).

### O que muda

**`specialized.py`:**
- Encolher cada `system_prompt` longo para **uma linha de fallback** derivável da meta (ex.: `f"Você é o {name} do Javis — {role}. Responda em português."`). Opção mais limpa: remover as strings e gerar essa linha em `BaseAgent` a partir de `self.meta`.
- `BaseAgent.execute()` (`:35`) passa a aceitar `system: str | None = None` e usar o recebido em vez de `self.system_prompt` — assim o fallback Ollama (`agent_runner.py:95`) usa o `system` já composto (meta+skill), não a string interna.

**`agent_runner.py`:**
- `_persona()` (`:31`) retorna `name` + prompt-mínimo-da-meta (não mais o `system_prompt` longo).
- No fallback Ollama (`:91-95`), trocar `cls().execute(task, context=ctx)` por `cls().execute(task, context=rag, system=system)` — reusar o `system` já montado em `:61-63`, eliminando o `ctx = skill + rag`.

### Riscos
1. **`.md` ausente** → sem fallback, agente perde persona. Garantir o prompt-mínimo-da-meta quando `_load_skill` retorna `""`.
2. **Ollama (llama 3.2:3b) com prompt grande** → o `.md` completo pode estourar contexto/qualidade no modelo fraco. Validar que o fallback ainda responde coerente; se não, truncar skill no caminho Ollama.
3. **Os outros 16 agentes** sem `.md` ainda dependem da string — a redução só pode remover a persona longa *depois* que cada `agente-<id>.md` existir, ou manterá o fallback-mínimo (aceitável).

### Plano (pro Developer)
1. Em `BaseAgent`: gerar `system_prompt` mínimo a partir de `self.meta` (name+role) e adicionar param `system=None` em `execute()` que sobrepõe `self.system_prompt`.
2. Remover as strings `system_prompt` longas das 11 classes em `specialized.py` (a persona passa a viver só no `.md`).
3. Em `agent_runner.py`, ajustar `_persona()` para devolver o prompt-mínimo e o fallback Ollama para passar `system=system`.
4. Garantir prompt-mínimo quando `_load_skill` vazio (`:21`).
5. Teste: rodar `architect` (tem `.md`) e um agente sem `.md` (ex.: `devops`) pelos 3 brains; confirmar que persona só aparece de uma fonte e que o fallback não quebra.
6. Registrar a decisão em `_logs/2026-06-17_fonte-unica-persona-agentes.md`.

Quer que eu já abra esse `_logs/` com a decisão registrada, ou passo a bola direto pro Developer implementar?