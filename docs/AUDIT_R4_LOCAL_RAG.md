# Auditoria R4 — RAG local offline

Data: 2026-07-09
Branch: `hardening/r4-local-rag`

## Decisão

O RAG ganhou uma interface de embedder selecionada por `JAVIS_RAG_EMBEDDER`:

- `openai` continua sendo o default, para não mudar o comportamento atual.
- `local` usa um embedder puro-Python, determinístico e offline.

## O que muda

- `build_index()` e `search()` passam a consultar o embedder selecionado.
- Com `JAVIS_RAG_EMBEDDER=local`, não há chamada de rede para embeddings.
- O gate de rota continua igual; a mudança é só de custo e dependência de rede.

## Propriedades do embedder local

- sem dependência nova;
- sem rede;
- determinístico entre execuções;
- adequado para provar a arquitetura e destravar a etapa seguinte.

## Próximo passo futuro

Plugar um modelo local real, como Ollama/nomic, atrás da mesma interface de embedder.
Isso deve acontecer sem reabrir o contrato de rota nem a política de gates.

