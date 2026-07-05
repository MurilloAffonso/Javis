# JAVIS — Delegação automática Claude → Codex (design)

**Data:** 2026-07-04 · **Status:** aprovado, pronto pra plano de implementação

## Contexto e problema
Murillo tem duas assinaturas: **Claude Code** (raciocínio/arquitetura) e **Codex CLI**
(execução de código). Hoje a escolha de quem executa é um **toggle manual**
(`brain_switch.set_active`, comando de voz `trocar_motor`). A visão: o **Claude é o
cérebro/arquiteto** (pensa, decide, audita) e o **Codex são as mãos** (entra na pasta,
mexe, roda, programa). O objetivo central é **economizar cota do Claude** — deixar o
trabalho pesado de execução no Codex, com o Claude só nas pontas baratas.

Falta a peça que fecha a visão: **delegação automática por tipo de tarefa** — o cérebro
reconhecer sozinho "isso é execução" e passar pro Codex, sem toggle manual.

## Decisões (definidas com o usuário)
- **Gatilho:** Claude decide sozinho (automático).
- **Divisão de trabalho:** Claude dá o objetivo → Codex faz a tarefa inteira → Claude audita.
  (Recomendação de especialista: planejamento passo a passo derrotaria a economia.)
- **Autonomia:** Codex executa livre no working tree; Claude audita depois.
- **Trava:** commit/push continuam manuais (respeita o `CLAUDE.md`), injetados como preâmbulo.
- **Abordagem:** híbrida — atalho determinístico por verbo (C) + classificação leve pro
  ambíguo (A) + política documentada numa skill (B).

## O que já existe (reusar, não reescrever)
- `code_agent.py` — roda `codex exec <tarefa>` numa pasta, streaming ao vivo, timeout 900s.
- `brain_switch.py` — `dispatch(task, pasta)` roteia pro motor ativo com fallback; e
  `_audit_after_codex` faz o Claude auditar automaticamente **depois** do Codex.
- `orchestrator.py` — `_classify()` já emite `response_type: "code"` (hoje sem destino).
- `agent.py` tool `programar`, comando de voz `trocar_motor`.

## Conceito-chave (resposta ao "o Codex é uma skill?")
- **Codex = motor/engine** (as mãos) — já plugado como tool + engine.
- **Delegação = skill** (`_skills/delegar-execucao.md`) — a *política* de quando delegar.
- **Claude = cérebro** — objetivo + auditoria.

## Arquitetura e componentes

### 1. `backend/delegacao.py` (novo) — política (atalho C)
- `enabled() -> bool` — lê o flag `JAVIS_AUTO_CODEX` (default **desligado**).
- `should_delegate(texto: str) -> bool` — casa verbos inequívocos de execução
  (ex.: "programa", "implementa", "refatora", "roda os testes", "cria o arquivo",
  "corrige o bug"). Lista **conservadora** pra minimizar falso-positivo. Mesmo estilo
  do `command_router`.
- `montar_brief(texto: str, plano: str = "") -> str` — monta o objetivo pro Codex e
  prefixa o **preâmbulo de guarda**: "não faça git commit nem push; deixe as mudanças
  no working tree para revisão". Se `plano` (do classificador) existir, inclui como contexto.

### 2. `_skills/delegar-execucao.md` (novo) — fonte-da-verdade (skill B)
Documenta a política em linguagem humana (verbos, o que vai/não vai pro Codex,
o preâmbulo de guarda). Espelha o `delegacao.py` como `commands.yaml` espelha o
`command_router`. É o arquivo que Murillo edita pra ajustar a política sem tocar código.

### 3. `backend/brain_switch.py` (editar) — override de engine
- `dispatch(task, pasta=None, engine=None)` — se `engine` for passado e válido, usa ele
  (força Codex na delegação automática); senão mantém `get_active()`. Fallback e
  `_audit_after_codex` inalterados.

### 4. `backend/orchestrator.py` (editar) — rota `exec` (A)
- No `process()`, **antes** de `_classify` (economia): se `delegacao.enabled()` e
  `delegacao.should_delegate(input)` → `return self._run_exec(input)` (nem classifica).
- **Depois** de `_classify`: se `delegacao.enabled()` e (`brain == "exec"` ou
  `response_type == "code"`) → `_run_exec(input, plano=result.plan)`.
- `_run_exec(self, text, plano="")` — `brief = delegacao.montar_brief(text, plano)`;
  chama `brain_switch.dispatch(brief, engine="codex")`; seta `result.brain="exec"`,
  `result.response` = aviso ("Codex rodando; auditoria do Claude depois"); retorna.
- Adicionar `exec` à lista de brains no `SYSTEM_ORCHESTRATOR` (pro classificador poder marcar).

## Fluxo de dados
```
input
 ├─ delegacao.enabled() && should_delegate()? ── SIM ──────────────┐  (nem classifica → economia)
 │        │ NÃO                                                     │
 ├─ orchestrator._classify()  (1 chamada leve)                      │
 │        │ brain=="exec" || response_type=="code" ────────────────┤
 │        │ senão → main/conclave/squad/memory (como hoje)          ▼
 │                                    _run_exec → brain_switch.dispatch(engine="codex")
 │                                                 └→ code_agent → `codex exec` (working tree, streaming)
 │                                                 └→ _audit_after_codex → Claude audita → notifica
```
Claude gasta cota só na classificação leve (e só pro ambíguo) e na auditoria final.

## Guardrails e tratamento de erro
- **Git**: preâmbulo de guarda em todo brief (sem commit/push).
- **Interruptor mestre**: `JAVIS_AUTO_CODEX` default desligado → comportamento atual intacto.
- **Classificador falha** → cai no `main` normal (não delega). Seguro.
- **Codex indisponível** → `brain_switch.dispatch` já faz fallback pro Claude exec.
- **Codex trava** → timeout 900s no `code_agent`.
- **Codex exit≠0 / saída ruim** → `_audit_after_codex` (Claude) audita e notifica — a rede.
- **Falso-positivo do atalho** → lista de verbos conservadora + auditoria como rede.

## Testes (offline, com mock)
- `delegacao`: verbos de execução casam; frases normais não; `montar_brief` inclui a trava de git; `enabled()` respeita o flag.
- `orchestrator`: com flag ligado, atalho roteia pro `_run_exec` **sem chamar `_classify`**
  (monkeypatch `_classify` pra falhar se chamado → prova a economia); `response_type=="code"`
  roteia pro Codex; texto normal segue igual; flag desligado → nada muda.
- `brain_switch`: `engine="codex"` força Codex; fallback quando Codex indisponível.
- Mock de `code_agent.dispatch`/`claude_exec` — nada roda de verdade.

## Escopo v1 (YAGNI)
- Pasta de trabalho = raiz do Javis (sem roteamento por projeto ainda).
- Verbos no código + documentados na skill (sem parsear a skill em runtime — fica pra depois).
- Sem UI nova (usa a aba Execução + notificações existentes).

## Futuro (fora do v1)
- Roteamento por projeto/pasta ativa.
- `delegacao.py` ler a lista de verbos direto da skill `.md`.
- Brief mais rico pro Codex em tarefas ambíguas (o Claude escreve um mini-spec).
