# Auditoria de conexão da interface — design

**Data:** 2026-07-14
**Autor:** Murillo + Javes (Claude Code)
**Status:** aprovado, pronto para executar

## Objetivo

Descobrir, com evidência, quais telas do Command Center estão de fato
**conectadas e funcionando** ponta a ponta com o backend, e quais só *parecem*
conectadas (respondem, mas com dado falso, ou renderizam nada). O produto é um
**mapa de saúde** — não consertos. Consertos viram um plano à parte, priorizado
a partir deste mapa.

## Contexto

Inventário inicial (feito antes deste spec) mostrou que **as 15 telas chamam
endpoints que existem de verdade** no `server.py` — não há tela batendo em rota
fantasma. Logo, "conectar a interface" **não é** um trabalho de fiação nova. O
gap real é de **saúde**: no nível de rota está ligado, mas falta medir se o dado
é real, se a tela renderiza, e se há fallback silencioso mascarando quebra.

Três modos de falha que o inventário de rota não pega:
1. **Stub** — endpoint responde 200 com dado hardcoded / lista vazia / placeholder.
2. **Botão morto** — a view chama o endpoint mas não usa a resposta.
3. **Fallback silencioso** — `app.js` (`loadData`) e a Vem Passear caem em "dados
   sintéticos" quando o backend falha, sem sinalizar — a tela parece viva estando morta.

## Método

Dois sinais por tela, cruzados:

### Sinal 1 — backend real
Subir o server em `:8000` (via `.venv_chainlit`, Python 3.11, por causa do bug do
Starlette no 3.14) e bater em cada endpoint que a UI usa, com token local.
Classificar a resposta:
- 🟢 **real** — dado vivo do sistema
- 🟡 **stub/vazio** — 200 com dado hardcoded, lista vazia ou placeholder
- 🔴 **quebrado** — erro, 404, exceção

### Sinal 2 — frontend renderiza
Ler o código de cada view e verificar se ela **usa** a resposta (renderiza) ou se
ignora (botão morto).

### Veredito cruzado
| Backend | Render | Veredito |
|---------|--------|----------|
| 🟢 real | ✅ sim | **viva** |
| 🟡 stub | ✅ sim | **fachada** |
| 🟢 real | ❌ não | **muda** |
| 🔴 quebra | — | **morta** |

## Entregável

Um documento `docs/.../2026-07-14-mapa-saude-interface.md` com uma tabela:

```
Tela        | Endpoint          | Backend | Render | Veredito | Nota
------------|-------------------|---------|--------|----------|------
operação    | approvals/pending | 🟢 real | ✅ sim | viva     |
máquina     | maquina/stats     | 🟡 stub | ✅ sim | fachada  | stats fixos
```

Mais um resumo executivo: quantas vivas / fachada / mudas / mortas, e as 3
correções de maior impacto.

## Escopo

**Dentro:** as 15 telas do Command Center (chat, conclave, config, conteúdo,
exec, ingestão, máquina, missões, operação, painel, rotina, tarefas, treino,
vempassear, madrugada).

**Fora (próxima rodada, decidida a partir do mapa):**
- Consertar qualquer stub, botão morto ou quebra.
- Mexer no backend.
- Redesenhar UI ou fluxo.
- Comando de voz e redução de token (threads separados que o Murillo levantou).

## Critério de pronto

Toda tela tem um veredito com evidência (resposta do endpoint + trecho do render).
Nenhum "não sei". O resumo aponta as 3 correções prioritárias.
