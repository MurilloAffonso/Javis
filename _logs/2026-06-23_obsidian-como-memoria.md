# Decisão: notas do Obsidian como memória (ampliar RAG)

## O que foi decidido
O vault Obsidian do Murillo **é o próprio diretório `javis/`** (tem `.obsidian/`
na raiz). O RAG (`knowledge.py`) já indexava as notas dele, mas só de 10 pastas
com prefixo `_`. Ampliei a cobertura pra incluir **`_docs/` e `_sessoes/`**, que
estavam de fora.

Mantive **`_referencias/` (232 .md) fora de propósito** — é majoritariamente doc
de bibliotecas de terceiros (ECC, silero-vad) que poluiria a busca semântica.
Decisão do Murillo: incluir só `_docs/` + `_sessoes/`, sem pasta nova.

## Por quê
"Usar as notas do Obsidian como memória" já acontecia para o vault, mas notas
escritas fora das pastas `_memoria/_logs/_projetos/...` ficavam invisíveis pro
cérebro. `_docs/` em particular tinha conteúdo do próprio Murillo (ex.:
`JAVIS-VISAO-OPERACIONAL.md`) que não era recuperável.

## Como foi feito
- `knowledge.py`: adicionado `"_docs", "_sessoes"` a `_KNOWLEDGE_DIRS` + comentário
  explicando por que `_referencias/` fica fora.
- Re-indexação incremental: 1.346 → **1.441 chunks**. `_docs` entrou com 69
  chunks, `_sessoes` com 4.
- Prova end-to-end: busca semântica por "visão operacional do Javis" retorna
  `_docs\JAVIS-VISAO-OPERACIONAL.md` no topo (score 0.730) — antes invisível.

## Fluxo "escrever nota no Obsidian → virar memória"
1. Murillo escreve/edita `.md` em qualquer pasta indexada (via Obsidian ou
   qualquer editor — o RAG lê o arquivo, não o app).
2. Re-indexação dispara em: (a) boot do servidor (`start_background_index`),
   ou (b) `POST /knowledge/reindex` (incremental, barato — só re-embeda o que
   mudou por mtime).
3. A nota fica recuperável via tool `buscar_conhecimento` no cérebro.

Esclarecimento importante: o Javis **não integra com o app Obsidian** (não lê
tags, backlinks nem metadados do `.obsidian/` — essa pasta está em `_SKIP_DIRS`).
Ele lê o **texto** dos `.md`. Obsidian e Javis compartilham o mesmo chão de
arquivos; um não depende do outro.

## Comando de voz/texto: "atualiza a memória"
Adicionado intent `atualizar_memoria` pra disparar o reindex falando, sem abrir
endpoint na mão. Tocado em 4 lugares (padrão dos outros intents):
- `command_router.py`: RULES (frases "atualiza a memória", "reindexa as notas",
  "sincroniza a memória", etc.), RISK_MAP (`low`/`False`), ACTION_MAP
  (`reindex_memory`), _reason.
- `actions.py`: handler `_reindex_memory` → `knowledge.build_index(force=False)`,
  devolve resumo falado ("X arquivo(s) reindexado(s), Y trechos").
- `config/commands.yaml`: bloco documentando o intent (consistência testada).
- `server.py`: incluído no `FAST_PATH` (roda sem gastar LLM).

Validado: roteamento certo (e "atualiza o site" NÃO colide → vai pra conversa),
handler reindexa ao vivo, `test_intent_consistency` passa, suíte 138/138.

## Próximo passo
Frente ativa segue livre. Se aparecerem notas novas em pastas ainda fora do
índice, reavaliar caso a caso (evitar `_referencias/` e clones de terceiros).
