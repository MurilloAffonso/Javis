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

## Próximo passo
Ligar a **voz** para passar `escopo` no `answer_context` conforme a persona ativa
(Javes = excluir `vp`) — é o que efetivamente fecha o bug de identidade. Toca o
cérebro de voz (`voice_bridge`/`openrouter_voice`/`agent_runner`), feito à parte.
