# Decisão: RAG híbrido SQLite-nativo (FTS5 + numpy + RRF)

**Data:** 2026-07-04
**Contexto:** análise comparativa Javis × mega-brain (thiagofinch). O maior gap
do Javis era o RAG: índice JSON flat com cosine O(n) em Python puro, chunk sem
overlap, cap de 800 arquivos, sem BM25/rerank (`backend/knowledge.py`).

## O que foi decidido
Implementar retrieval **híbrido** dentro do SQLite que o Javis já usa
(`javis.db`), de forma **aditiva** (o `knowledge_index.json` continua válido):

- **Semântico**: vetores guardados em BLOB float32; cosine com **numpy**.
- **Palavra-chave**: **FTS5/BM25** embutido no SQLite (external content).
- **Fusão**: **Reciprocal Rank Fusion (RRF, K=60)** dos dois rankings.
- **Chunking com overlap** (rebuild `force=True`); overlap 150 / alvo 900 chars.
- Sem cap de 800 arquivos; limpeza de paths sumidos do disco.

## Por quê essa abordagem (e não pgvector / sqlite-vec)
SQLite já está no projeto (filosofia dual-write do `db.py`), 100% local, zero
serviço novo, mantém a economia free-first. FTS5 e numpy já disponíveis
(Python 3.14, numpy 2.4.4). pgvector adicionaria um Postgres no docker;
sqlite-vec tem atrito de carregar extensão no Windows.

## Economia
A migração inicial **reaproveita os vetores do `knowledge_index.json`** (casa por
path + texto do chunk) → primeiro build custa **zero embeddings novos**.

## Arquivos
- `backend/migrations/schema.sql` — tabelas `knowledge_chunks` + `knowledge_fts` + triggers (IF NOT EXISTS, idempotente)
- `backend/knowledge_hybrid.py` — **novo**: build + busca híbrida
- `backend/knowledge.py` — `search`/`answer_context` delegam ao híbrido com fallback; `build_index` alimenta os dois. Flag `JAVIS_RAG` (padrão `hybrid`; qualquer outro valor = só legado)
- `requirements.txt` — `numpy>=1.26`
- `tests/test_knowledge_hybrid.py` — **novo**: 8 testes (build, semântico, BM25, RRF, answer_context, incremental, blob, sanitização FTS)

## Verificação
`pytest tests/` → **150 passed** (8 novos). Testes rodam sem OpenAI (embeddings
fake) e sem tocar o vault real (DB temporário).

## Ativação (pendente — precisa do Murillo)
Rodar UM build para popular o `javis.db` a partir do JSON existente (endpoint
`POST /knowledge/reindex` ou `knowledge.build_index()`). Enquanto o `javis.db`
não tiver chunks, `available()` é False e o sistema segue no índice legado
(fallback transparente). Rollback: `JAVIS_RAG=legacy`.

## Próximos passos (roadmap mega-brain)
2. Eval de retrieval (recall@k / perguntas-douradas) — provar o ganho
3. Extração cognitiva unificada ("DNA")
4. Knowledge graph
