# Token Economy — Javis

Registro acumulado de economia de tokens via LeanCTX.
Atualizar ao fechar cada sessão (via `_skills/fechar-sessao.md`).

---

## Totais Acumulados (lean-ctx gain)

| Data | Tokens salvos | Compressão | USD economizado | Score |
|------|--------------|------------|-----------------|-------|
| 2026-06-10 | 924K | 88% | $2.38 | 52/100 Lv3 |
| 2026-06-11 (audit) | 1.0M | 79.7% | $2.73 | 48/100 Lv3 |
| 2026-06-11 (sessão) | 1.0M | 79% | $2.74 | — |

> Fonte: `lean-ctx gain --deep` rodado manualmente.
> O score varia porque reflete janelas de tempo diferentes (--deep analisa sessões recentes).

---

## Detalhamento 2026-06-11 (lean-ctx gain --deep)

```
Tokens salvos:    1.0M
Compressão:       79.7%
Comandos totais:  368
USD economizado:  $2.73 (71.6% de redução vs sem lean-ctx)

Top ferramentas:
  ctx_read     60 chamadas  — $1.11 de processamento
  ctx_shell    87 chamadas  — $0.69 de processamento
  ctx_tree     14 chamadas
  ctx_search   15 chamadas
  ctx_edit      5 chamadas
  ctx_session   1 chamada

Heatmap (arquivo mais lido):
  javis-local-interface/... → 31.3K tokens, 91% compressão
```

---

## Registro por Sessão

| Data | Sessão | Estimativa de economia | Ferramentas usadas |
|------|--------|----------------------|-------------------|
| 2026-06-10 | Setup inicial, Open WebUI, modelos | ~924K tokens acum. | ctx_read, ctx_shell, ctx_tree |
| 2026-06-11 | Auditoria de economia de tokens | +~76K tokens (delta) | ctx_read, ctx_shell, codegraph_explore |
| 2026-06-11 | intent-consistency-audit | +~10K tokens (sessão curta) | ctx_read signatures, ctx_shell, ctx_session |

---

## Como atualizar

```bash
# Ver economia atual
lean-ctx gain --deep

# Atualizar este arquivo com os novos totais
# (manualmente, ao fechar sessão com /fechar-sessao)
```
