# Auditoria de Economia de Tokens — Javis

**Data:** 2026-06-11 04:23 UTC
**Auditor:** Claude Code — Auditor de Economia de Tokens

---

## ETAPA 2 — Ferramentas ativas: evidências objetivas

### 1. LeanCTX disponível?

✅ **SIM — ativo e funcionando**

- Versão: 3.7.5
- Localização: `C:\Users\noteacer\AppData\Roaming\npm\lean-ctx.cmd`
- MCP configurado em: `C:\Users\noteacer\.claude.json`
- Doctor: 25/26 checks (único aviso: alias PowerShell — cosmético, sem impacto)
- Plan mode Claude Code: OK (`mcp__lean-ctx__ctx_shell` na allowlist de `javis/.claude/settings.local.json`)
- Shell allowlist: 202 comandos

---

### 2. CodeGraph disponível?

✅ **SIM — indexado e operacional**

- Files indexed: 13
- Total nodes: 177 (funções, variáveis, importações, constantes)
- Total edges: 315
- DB size: 40 MB (SQLite WAL + FTS5)
- Linguagens: Python (10), JavaScript (1), YAML (2)
- Prova de uso nesta sessão: `codegraph_explore("command_router RISK_MAP ACTION_MAP route")` retornou 3 arquivos completos em 1 chamada

---

### 3. `lean-ctx gain` funcionando?

✅ **SIM — dados reais medidos**

```
Tokens salvos:  1.0M
Compressão:     79.7%
USD economizado: $2.73 (71.6% redução vs sem lean-ctx)
Comandos:       368
Streak:         2 dias
Score:          48/100 Lv3 Architect
```

---

### 4. Hooks LeanCTX ativos no projeto Javis?

⚠️ **PARCIALMENTE**

- `javis/.claude/settings.local.json` tem `mcp__lean-ctx__ctx_shell` na allowlist
- Sem hooks automáticos de pré/pós-sessão
- Sem regra de exigir ctx_* no `.claude/` local do Javis
- A regra vem do CLAUDE.md **global** (`C:\Users\noteacer\.claude\CLAUDE.md`)
  que importa `@rules/lean-ctx.md` — funciona, mas só se esse arquivo estiver ativo

---

### 5. `.claude/rules/lean-ctx.md` dentro de javis/?

❌ **NÃO existe dentro de javis/**

- Existe globalmente em `C:\Users\noteacer\.claude\rules\lean-ctx.md`
- Javis só tem `.claude/settings.local.json`
- Se alguém abrir javis/ em outro perfil sem o CLAUDE.md global, as regras LeanCTX se perdem

---

### 6. `.claude/settings.local.json` dentro de javis/?

✅ **SIM**

```json
{ "permissions": { "allow": ["mcp__lean-ctx__ctx_shell", ...playwright...] } }
```

---

### 7. AGENTS.md com referência LeanCTX?

✅ **SIM — seção completa**

- "Economia de Tokens — Regras para Agentes" mapeando ctx_* vs nativos
- Fluxo padrão orient → locate → read → edit → verify → record
- Prioridade 2: Headroom (documentado mas não instalado)

---

### 8. Protocolo `/abrir-sessao` e `/fechar-sessao`?

❌ **NÃO — apenas documentado no AGENTS.md como fluxo geral**

- Sem `_skills/abrir-sessao.md` (criado agora nesta auditoria)
- Sem `_skills/fechar-sessao.md` (criado agora nesta auditoria)
- Sem `_sessoes/` — nenhuma sessão foi registrada
- `ctx_session` chamado apenas 1x no histórico total

---

## ETAPA 3 — Uso real: medições

| Item | Status | Evidência |
|------|--------|-----------|
| LeanCTX usado nas últimas sessões | ✅ SIM | 60 ctx_read, 87 ctx_shell, 14 ctx_tree, 15 ctx_search |
| CodeGraph usado nas últimas sessões | ⚠️ HOJE | 1ª evidência documentada: nesta auditoria |
| Relatório de economia em arquivo | ❌ NÃO | Não existia `_logs/token-economy.md` (criado nesta auditoria) |
| "LeanCTX savings" por sessão | ❌ NÃO | Só visível via `lean-ctx gain`, não nos logs do Javis |
| Sessões registram economia | ❌ NÃO | Nenhum log menciona tokens |
| `_sessoes/` existe e está em uso | ❌ NÃO | Diretório não existia |
| `_estado/estado-atual.md` | ❌ NÃO | Não existia (criado nesta auditoria) |
| `_estado/proximos-passos.md` | ❌ NÃO | Não existia (criado nesta auditoria) |

---

## ETAPA 4 — Diagnóstico honesto

### Resultado: **B) Ferramentas instaladas e em uso, mas economia não está sendo medida/registrada**

Mais precisamente, o Javis está em **estado B+ (quase C em termos de protocolo)**:

**O que está realmente funcionando:**
- LeanCTX salva tokens automaticamente — sem esforço, sem configuração extra
- `lean-ctx gain` prova isso com dados reais: 1M tokens, $2.73
- As ferramentas ctx_* são usadas nas sessões (60 leituras, 87 shells)
- CodeGraph está indexado e funciona quando chamado

**O que está só documentado, mas não operacional:**
- Protocolo de sessão (abrir/fechar) — estava no AGENTS.md mas sem skills
- `_sessoes/` — não existia
- `_estado/` — não existia
- Registro de economia por sessão — invisível para Murillo
- CodeGraph sem uso sistemático em sessões anteriores (só hoje)
- `.claude/rules/lean-ctx.md` não está dentro do projeto Javis

**Conclusão:** A economia está acontecendo (LeanCTX é automático), mas é invisível.
Murillo não sabe quanto economizou por sessão. O protocolo de sessão é documentação sem prática.

---

## ETAPA 5 — Protocolo mínimo implementado

Os seguintes arquivos foram criados nesta auditoria:

| Arquivo | Descrição |
|---------|-----------|
| `_estado/estado-atual.md` | Estado atual de todos os módulos e ferramentas |
| `_estado/proximos-passos.md` | Próximos passos priorizados com contexto |
| `_logs/token-economy.md` | Registro acumulado de economia de tokens |
| `_skills/abrir-sessao.md` | Skill para iniciar sessão estruturada |
| `_skills/fechar-sessao.md` | Skill para fechar sessão com registro completo |

**Não criado (requer aprovação de Murillo):**
- `_sessoes/` com primeiro registro — Murillo deve criar usando `/abrir-sessao`
- Nenhuma mudança de código, configuração, commit ou push

---

## ETAPA 6 — Teste rápido: resultado

### CodeGraph

```
codegraph_explore("command_router RISK_MAP ACTION_MAP route")
→ Retornou 3 arquivos (command_router.py, app.js, main.py) em 1 chamada
→ 177 nós totais indexados, 315 arestas
→ Funciona: SIM
```

### LeanCTX ctx_read (modo signatures)

```
ctx_read("command_router.py", "signatures")
→ 134 linhas → 5 linhas de output:
   "fn ⊛ route(text:s) → dict @L73-90"
   "fn _classify(text:s) → str @L93-106"
   ...
→ Compressão estimada: ~96% no modo signatures
→ Funciona: SIM
```

### Comparação (mesmo arquivo)

| Método | Output | Custo estimado |
|--------|--------|---------------|
| Read nativo | 134 linhas (~670 tokens) | ~$0.007 |
| ctx_read signatures | 5 linhas (~25 tokens) | ~$0.0003 |
| **Economia** | **96%** | **~$0.007 por leitura** |

---

## ETAPA 7 — Relatório final

### 1. LeanCTX está ativo?
**SIM** — v3.7.5, MCP configurado, 1.0M tokens salvos, 79.7% compressão, $2.73 economizados.
Evidência: `lean-ctx gain --deep` + 60 chamadas ctx_read + 87 ctx_shell no histórico.

### 2. CodeGraph está ativo?
**SIM** — 13 arquivos, 177 nós, 315 arestas indexados. Demonstrado nesta sessão com
`codegraph_explore` retornando 3 arquivos completos em 1 chamada. Sem evidência de uso
sistemático em sessões anteriores.

### 3. Existe medição real de economia?
**NÃO (antes desta auditoria)** — LeanCTX mede internamente mas o Javis não tinha
`_logs/token-economy.md` nem registro por sessão. Agora existe `_logs/token-economy.md`.

### 4. Existe protocolo de sessão real?
**NÃO (antes desta auditoria)** — estava documentado no AGENTS.md mas sem skills,
sem `_sessoes/`, sem `_estado/`. Agora existem `_skills/abrir-sessao.md` e
`_skills/fechar-sessao.md`. Ainda falta Murillo usar pela primeira vez.

### 5. O que está só documentado, mas não operacional

- `_sessoes/` — nunca usado (diretório não existia)
- Protocolo abrir/fechar sessão — estava no AGENTS.md mas sem execução real
- Headroom — instalação falhou, aguardando aprovação do workaround
- `.claude/rules/lean-ctx.md` dentro de javis/ — existe só no perfil global

### 6. O que precisa virar obrigatório

1. **Toda sessão começa com `/abrir-sessao`** — carrega contexto, cria registro
2. **Toda sessão termina com `/fechar-sessao`** — registra economia, atualiza estado
3. **CodeGraph antes de ler código** — `codegraph_explore` antes de `ctx_read` para arquivos não familiares
4. **`_estado/estado-atual.md` atualizado** ao final de qualquer fase de mudança

### 7. Próximo passo mínimo para ativar a economia de verdade

**Uma ação para Murillo:**

> Na próxima sessão, digitar `/abrir-sessao` antes de começar.
> Ao final, digitar `/fechar-sessao`.
>
> Isso fecha o loop: economia medida → registrada → visível → repetível.

O resto já está funcionando. LeanCTX já economiza. CodeGraph já indexou.
O único passo que falta é o hábito humano de abrir e fechar sessão.

---

## Confirmações finais

- ✅ Nada foi instalado
- ✅ Execução por voz não foi alterada (dry_run=True permanece)
- ✅ Nenhum commit foi feito
- ✅ Nenhum push foi feito
- ✅ Nenhum arquivo foi apagado
- ✅ Open WebUI não foi tocado
- ✅ Docker não foi tocado
- ✅ Nenhuma arquitetura nova foi criada
- ✅ Apenas arquivos markdown foram criados (5 arquivos, todos seguros)
