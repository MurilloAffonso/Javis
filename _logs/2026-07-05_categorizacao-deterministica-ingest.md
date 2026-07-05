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

## Próximo passo
Melhorias 2 e 3 do roadmap de RAG: **rerank** (precisão pós-RRF) e **grafo
LazyGraphRAG**. Ambas se apoiam nesta categorização.
