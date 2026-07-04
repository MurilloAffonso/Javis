# Decisão: Eval de retrieval (item 2 do roadmap mega-brain)

**Data:** 2026-07-04
**Contexto:** depois do RAG híbrido (item 1, ver `_logs/2026-07-04_rag-hibrido-sqlite.md`),
faltava **medir** o ganho — senão a melhoria é fé, não número.

## O que foi decidido
Harness de avaliação que roda um **golden set** (perguntas → paths esperados) em
cada retriever e compara **híbrido × legado** com hit@k, recall@k, precision@k, MRR.

- Um hit conta se algum trecho de `relevant` aparece no path do resultado.
- Retriever legado é forçado desligando `JAVIS_RAG` temporariamente (sem refatorar
  `knowledge.search`).
- Leve de propósito: sem RAGAS/LLM-judge (custo/dependência). Recall@k + MRR já
  bastam pra provar A/B e pegar regressão.

## Arquivos
- `backend/knowledge_eval.py` — **novo**: `evaluate()`, `load_golden()`, CLI `python knowledge_eval.py [k]`
- `backend/server.py` — **novo endpoint** `GET /knowledge/eval?k=5`
- `_memoria/rag_eval_golden.example.json` — **novo**: exemplo (renomear p/ `rag_eval_golden.json` e curar)
- `tests/test_knowledge_eval.py` — **novo**: 4 testes (métricas, no_golden, matemática recall/precision, integração híbrido>legado)

## Verificação
`pytest tests/` → **154 passed**. O teste de integração prova, com corpus sintético
e embeddings fake, **híbrido hit_rate=1.0 vs legado 0.0** numa query cujo alvo só é
recuperável por BM25 (termo raro, vetor semântico nulo).

## Ativação (pendente — Murillo)
1. Curar `_memoria/rag_eval_golden.json` com perguntas reais do vault (base: o `.example.json`).
2. Popular o índice (`POST /knowledge/reindex`) — vale pro item 1 e 2.
3. `GET /knowledge/eval` → ver o delta híbrido−legado nos seus dados reais.

## Próximos passos
3. Extração cognitiva unificada ("DNA")
4. Knowledge graph
