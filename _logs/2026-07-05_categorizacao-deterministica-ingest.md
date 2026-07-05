# Decisão — Categorização determinística de escopo no RAG

Data: 2026-07-05

## O que foi decidido
Cada chunk do RAG passa a ser rotulado, de forma **determinística** (sem modelo,
sem latência), em uma de três categorias de **escopo**:

- `pessoal` — DNA cognitivo do Murillo (`_memoria/dna/`).
- `projeto` — conhecimento operacional do Javis (default interno).
- `vp` — projeto externo Vem Passear Jampa (Cérebro Jampa), **por registro**.

O sinal é o **path** do chunk (já carrega a fronteira: `_relpath` prefixa vaults
externos com `[NomeDoVault]`). A fronteira VP vem do `project_registry`
(`"categoria": "vp"`), não de hardcode — casa com o CLAUDE.md ("externos só por
registro").

A busca (`knowledge_hybrid.search`/`answer_context`) ganhou parâmetro
`escopo=None` que filtra por categoria.

## Por quê
1. **Mata o bug de identidade** — com escopo, a voz pode excluir `vp` quando o
   Javes fala como si mesmo; ele deixa de puxar contexto de VP e "virar a empresa".
2. **Determinística e grátis** — zero custo de latência/modelo; respeita free-first
   e a sensibilidade de latência da voz.
3. **Fundação** — rerank e grafo (próximas melhorias) se apoiam nela (filtrar/rankear
   por categoria).

## Arquivos
- **novo** `backend/categoria.py` — classificador puro `de_path(path) -> str`.
- **novo** `tests/test_categoria.py` — 14 casos determinísticos (14/14 PASS).
- `backend/migrations/schema.sql` — coluna `categoria TEXT` em `knowledge_chunks`.
- `backend/db.py` — migração aditiva idempotente `ALTER TABLE ... ADD COLUMN categoria`.
- `backend/project_registry.py` — `"categoria": "vp"` na entrada cerebro-jampa.
- `backend/knowledge_hybrid.py` — `build_index` carimba cada chunk; `backfill_categoria()`
  preenche DB já populado sem re-embedar; `search`/`answer_context` filtram por `escopo`.

## Verificação
- `test_categoria.py`: 14/14.
- DB real: partição completa (vp:1868 · projeto:1808 · pessoal:40, zero NULL).
- `backfill_categoria()` provado (path zerado → repreenchido corretamente).
- Suíte: 23/25 arquivos OK. As 2 falhas (`test_command_router`, `test_voice_bridge`)
  são **pré-existentes** (roteamento de intent "tocar_musica"), confirmado via
  `git stash` — falham idêntico sem estas mudanças.

## Alternativas consideradas
- Rerank primeiro: adiado — é incremento sobre um retriever já híbrido+RRF e custa
  latência na voz.
- Grafo LazyGraphRAG: adiado — maior R&D, mais especulativo.
- Classificação por LLM no ingest: rejeitada — não-determinística, com custo/latência.

## Fase 2 — Voz ligada ao escopo (fecha o bug de identidade)
Feito no mesmo dia. A voz agora passa `escopo` no RAG:

- `knowledge.answer_context(query, k, escopo=None)` propaga o escopo pro híbrido; o
  fallback legado (índice JSON) filtra por `categoria.de_path` — fronteira mantida
  mesmo sem o híbrido.
- `server.py`: `_menciona_vp()` (regex `\b(vem\s*passear|vp|jampa)\b`) + `_escopo_voz()`.
  Regra: **por padrão a voz exclui `vp`** (`["projeto","pessoal"]`); só libera VP
  (`escopo=None`) quando a pergunta nomeia VP. Aplicado em `_add_voice_grounding`.
- Efeito: o Javes, falando como si mesmo, não puxa mais contexto de VP → não "vira"
  a empresa. Quando Murillo pergunta de VP explicitamente, o contexto VP volta.

Verificado ao vivo no DB real:
- `escopo="vp"` → 6 hits, todos vp (CEREBRO.JAMPA).
- `escopo=["projeto","pessoal"]` numa pergunta sobre VP → 6 hits, **zero vp** vazou.
- Regra `_escopo_voz`: 5/5 casos (perguntas neutras excluem vp; "VP"/"Jampa"/"Vem
  Passear" liberam).
- Suíte: 23/25 arquivos OK (as 2 falhas seguem pré-existentes).

## Fase 3 — Rerank (medido e descartado) + portão de relevância apertado

### Rerank: medido, PIORA, mantido off
Implementado `_rerank` (fusão de scores normalizados sem/kw) + flag `rerank=` em
`search`/`answer_context` + modo `reranked` em `knowledge_eval`.

**Armadilha pega no meio do caminho:** os scripts standalone não carregavam o `.env`,
então rodavam SEM `OPENAI_API_KEY` → semântico morto → tudo BM25 (todo `sem=0.000`).
A 1ª medição ("rerank é no-op") era inválida. Re-medido carregando o `.env`:

| métrica (k=5) | RRF puro | reranked |
|---|---|---|
| hit_rate | 1.000 | 1.000 |
| mrr | **0.958** | 0.828 (−0.13) |

O RRF+híbrido já é quase perfeito (relevante no topo); o rerank por fusão só
desarruma. **Fica off.** Código mantido como estágio togglável p/ medir cross-encoder
futuro (onnxruntime já instalado; sentence-transformers/torch não).

### Portão de relevância do answer_context (apertado com guard)
Golden com embeddings: chunks RELEVANTES têm sem>=0.47 (mediana 0.62); kw-only com
sem~0 é ruído (5/5 não-relevantes). O gate antigo (`sem>=0.15 OU kw`) deixava esse
ruído passar. Novo gate: `sem>=0.35 OU (kw E sem>=0.25)`, com **guard**: se o
embedding estiver morto (sem key em runtime, todo sem=0), volta ao gate legado pra
NÃO zerar o grounding (evita reabrir o bug de alucinação).

Verificado: retenção do relevante **16/16** com embeddings, **zero contexto vazio**;
degradado sem key também mantém grounding (BM25). Suíte 23/25 (2 falhas pré-existentes).

## Próximo passo
Item 3 do roadmap: **grafo LazyGraphRAG** sobre `knowledge_graph.py`. Ou curar um
golden set mais ambíguo p/ reavaliar cross-encoder ONNX. Retriever atual já é forte
(mrr 0.958), então o teto de ganho em ordenação é baixo — o grafo é a aposta maior.
