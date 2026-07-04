# Decisão: Extração cognitiva unificada — DNA (item 3 do roadmap mega-brain)

**Data:** 2026-07-04
**Contexto:** a "extração cognitiva" do Javis estava espalhada em 3 ferramentas
ad-hoc com formatos soltos: `skill_forge` (frameworks), `wa_analyzer` (voz/objeções),
`resumir_treino` (aprendizados). O mega-brain faz isso como UM pipeline estruturado
("DNA cognitivo" em N dimensões).

## O que foi decidido
`backend/dna_extractor.py` — pipeline ÚNICO que extrai as **10 dimensões** do DNA
cognitivo de qualquer texto (transcrição, export WhatsApp, material de estudo):
filosofias, modelos_mentais, frameworks, heurísticas, valores, voz_tom,
objecoes_respostas, gatilhos_decisao, vocabulario, anti_padroes.

- Uma chamada LLM → **JSON estruturado** (parsing robusto: tolera cercas ```json,
  texto ao redor, vírgula pendente; sentinela "sem cérebro" → erro limpo).
- Normaliza sempre as 10 dimensões (ausente → lista vazia; nunca inventa).
- Grava **dossiê JSON + card Markdown** em `_memoria/dna/` → entra no RAG sozinho.
- **Free-first**: `llm_providers.call_claude` (Claude assinatura + fallback OpenRouter).
- **Reusa parsers existentes** em vez de duplicar: `from_whatsapp` chama
  `wa_analyzer.parse_export`/`_sample`. NÃO deletei as 3 ferramentas (elas seguem
  com seus outputs específicos); o DNA é a camada estruturada unificada.

## Arquivos
- `backend/dna_extractor.py` — **novo**: extract / from_whatsapp / from_transcript / save / extract_and_index
- `backend/server.py` — **novo endpoint** `POST /knowledge/dna` (body: text, fonte, tema, fonte_tipo)
- `tests/test_dna_extractor.py` — **novo**: 8 testes (parse, normalização, clamp, indisponível, save+card, reuso WhatsApp, export inválido, reindex)

## Verificação
`pytest tests/` → **162 passed** (+8). Tudo com LLM monkeypatchado — zero chamada real.

## Ativação (pendente — Murillo)
`POST /knowledge/dna` com `{"text": "...", "fonte_tipo": "whatsapp"|"transcricao"|""}`.
O dossiê aparece em `_memoria/dna/` e vira contexto do RAG.

## Próximo / futuro
- Item 4: knowledge graph (ligar entidades/claims entre dossiês DNA).
- Futuro: agregação/merge dos dossiês num "DNA-mestre" do Murillo (mega-brain faz isso).
