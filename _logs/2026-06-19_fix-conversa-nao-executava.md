# Fix: conversa prometia executar mas nunca agia — 19/06

## Sintoma (relato do Murillo)

Mandou comandos pro Javis pra fazer o 80/20 da Vem Passear (analisar projetos,
abrir o Fluxograma.pdf em Downloads/estudo). O Javis ficava em loop: "vou pedir
pra parte executora abrir o arquivo" → "ainda não, vou pedir" → "a bola está com
a parte executora". Nunca executava de fato. Sensação de "manda pro comando,
manda pra outro, não dá resposta exata, sem orquestramento".

Evidência: `_data/chat_history.json`, conversa de hoje 17:05–17:27 (20 msgs).
Todas as respostas do assistente eram promessas de acionar a execução, nenhuma
ação real.

## Causa raiz

Dois fatores:

1. **Bug estrutural em `server.py:_brain()` (passo 3)** — toda mensagem de
   `intent in ("conversa", "desconhecido")` ia DIRETO pro `claude_brain.answer()`,
   que é o cérebro de RACIOCÍNIO, com persona fixa: "Não use ferramentas nem
   edite arquivos — apenas raciocine. NUNCA afirme que executou/iniciou/criou".
   Esse caminho retornava o texto e dava `return` na hora — **nunca chegava no
   passo 4 (`agent.respond`, o único que de fato chama ferramentas)**. Resultado:
   pedido de ação classificado como "conversa" só gerava promessa, nunca ação.
   O cérebro de raciocínio até era HONESTO ("eu só penso, vou pedir pra
   executora") — mas o pedido pra executora nunca era emitido por código nenhum.

2. **Cota semanal da assinatura estourou hoje** (reset 20/06 09h). Como em 18/06
   migramos tudo pra assinatura, sem OpenAI de fallback, quando a cota acaba só
   resta Ollama (offline). Agravou a sensação de travamento. (Não é o bug em si,
   mas some o efeito.)

## O que foi feito

- **`server.py:_brain()`** — removido o passo 3 (atalho `claude_brain.answer`
  pra conversa). Agora `conversa`/`desconhecido` flui pro `agent.respond()`
  (passo que virou o único caminho de cérebro), que sabe:
  - conversar normal (retorna texto se nenhuma ferramenta serve),
  - AGIR de verdade: `programar` → `brain_switch.dispatch` → `claude_exec.dispatch`
    (dispara `claude` headless em background que edita arquivos/roda comandos),
  - `pensar_profundo` quando precisa de raciocínio fundo (preserva o que o
    passo 3 dava de bom, mas só quando faz sentido),
  - `buscar_conhecimento`, `lembrar_fato`, `analisar_arquivo`, etc.
  - O estado do projeto continua injetado: `agent._system()` já chama
    `briefing.estado_resumido()`, então não se perde contexto.

## Cadeia de execução confirmada (lendo o código, não mock)

`agent.respond` → `_respond_claude_subscription` decide tool via JSON →
`_exec_tool("programar", ...)` → `brain_switch.dispatch` → `claude_exec.dispatch`
→ `threading.Thread(_run_bg)` rodando `claude -p` headless pela assinatura. É
execução real em background, não promessa.

## Verificação

- `python -m py_compile server.py` — OK.
- Cadeia do executor lida ponta a ponta (brain_switch/claude_exec) — confirmada real.
- **Pendente: teste ao vivo** — NÃO rodado agora pra não queimar a cota apertada
  da assinatura (estourou hoje). Validar amanhã 19/06 após reset 09h: mandar no
  chat um pedido de ação ("abre o Fluxograma.pdf em Downloads/estudo e me diz o
  que tem") e confirmar que o agente chama `programar`/executor em vez de só
  prometer.

## Observação pro Murillo (trade-off de arquitetura)

A migração 100% assinatura (18/06) tem custo: latência alta (cérebro ~48s,
Conclave ~154s — testado ontem) E agora dependência de cota semanal única. Sem
OpenAI de reserva, quando a cota estoura o Javis fica sem cérebro bom. Vale
conversar se quer manter uma reserva (OpenAI ou Ollama mais forte) só pra não
ficar mudo quando a assinatura zerar. Não mexi nisso — é decisão dele.

**Sem commit/push — Murillo revisa e decide.**
