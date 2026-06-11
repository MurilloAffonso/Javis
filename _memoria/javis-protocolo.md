---
tags: [memoria, protocolo, sessao, javis]
---

# Protocolo de Sessão do Javis

## Abrir Sessão (`/abrir-sessao`)

1. Ler `_estado/estado-atual.md` — o que está rodando
2. Ler `_estado/proximos-passos.md` — o que fazer
3. Checar `_inbox/` — entradas novas
4. `ctx_knowledge(action="wakeup")` — surfaçar achados anteriores
5. Criar `_sessoes/YYYY-MM-DD_HHhMM_slug.md` com objetivo e contexto

## Fechar Sessão (`/fechar-sessao`)

1. `ctx_session(action="decision", content="o que foi feito + próximos passos")`
2. Completar arquivo da sessão: arquivos lidos/modificados, ferramentas usadas, estimativa de economia
3. Atualizar `_estado/estado-atual.md`
4. Atualizar `_estado/proximos-passos.md`
5. Atualizar `_logs/token-economy.md`
6. Rodar testes: `python -m pytest _apps/javis-local-interface/tests/ -v`

## Economia de tokens

- Usar `ctx_read` (modo `signatures` ou `map`) em vez de ler arquivos inteiros
- Usar `ctx_search` em vez de grep
- Usar `codegraph_explore` para entender código sem ler arquivo
- Meta: manter compressão acima de 70%

## Sessões registradas

- [[2026-06-11_04h30_intent-consistency-audit]] — auditoria de intents, 189/189 testes

---
Relacionado: [[javis-ferramentas]] · [[javis-regras]] · [[murillo]] · [[JAVIS-CEREBRO]]
