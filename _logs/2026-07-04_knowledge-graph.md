# Decisão: Knowledge graph sobre os dossiês de DNA (item 4 do roadmap mega-brain)

**Data:** 2026-07-04
**Contexto:** último item do roadmap de adoção mega-brain. Os dossiês de DNA
(item 3) eram ilhas; faltava LIGAR os conceitos entre eles pra ver os temas
centrais emergirem.

## O que foi decidido
`backend/knowledge_graph.py` — grafo de **co-ocorrência** sobre `_memoria/dna/*.json`:
- **Nó** = um conceito (uma "ideia" de qualquer dimensão do DNA), com `mentions`
  (em quantos dossiês aparece) e proveniência (`sources`).
- **Aresta** = dois conceitos no MESMO dossiê (não-direcionada, src<dst), com `weight`
  que acumula quando o par reaparece.
- Conceito que reaparece em vários dossiês vira hub (grau alto) → é o tema central.

**Determinístico, sem custo de LLM** (opera sobre o JSON já estruturado). SQLite-nativo,
aditivo, reconstrução idempotente (limpa só kg_*). Reusa `dna_extractor.DIMENSOES/_slug`.

## Arquivos
- `backend/migrations/schema.sql` — tabelas `kg_nodes` + `kg_edges` (+ índices)
- `backend/knowledge_graph.py` — **novo**: build_from_dna / neighbors / top_concepts / stats
- `backend/server.py` — endpoints `POST /knowledge/graph/build` e `GET /knowledge/graph?q=&depth=`
- `tests/test_knowledge_graph.py` — **novo**: 7 testes (build, mentions compartilhado, travessia de vizinhança, termo inexistente, idempotência, stats/top, dir vazio)

## Verificação
`pytest tests/` → **169 passed** (+7). Dossiês sintéticos, DB isolado, sem LLM.

## Ativação (pendente — Murillo)
1. Gerar alguns dossiês via `POST /knowledge/dna` (item 3).
2. `POST /knowledge/graph/build` → constrói o grafo.
3. `GET /knowledge/graph` (stats + conceitos centrais) · `GET /knowledge/graph?q=escassez` (vizinhança).

## Futuro (opcional)
- Relações TIPADAS via LLM (causa→efeito, parte→todo) em vez de só co-ocorrência.
- Visualização do grafo no frontend.
- Merge dos dossiês num "DNA-mestre" do Murillo.
