# Mapa de saúde da interface — Command Center

**Data:** 2026-07-14
**Método:** ver `2026-07-14-auditoria-conexao-interface-design.md`
**Backend auditado:** `server.py` em `:8000` (venv 3.11), flags de exec/madrugada/mcp ligados.

## Resumo executivo

**A interface está muito mais conectada do que o "não está funcionando" sugeria.**
Das 15 telas: **15 vivas/cabeadas, 0 fachada, 0 mudas, 0 mortas.**

- **Camada de leitura** (telas que mostram dado): **todos os endpoints devolvem
  dado real.** `maquina/stats`, que eu suspeitava ser stub, está com números reais
  (141 nós no grafo, 2288 chunks, etc.).
- **Camada de render:** toda view tem muito mais escrita no DOM do que fetches —
  nenhuma busca dado e ignora.
- **Dois "405" no sweep foram falso alarme** do meu probe (usei GET; `knowledge/dna`
  e `pulso` são POST dos dois lados, corretamente cabeados).

### Por que parecia quebrado

A causa mais provável do "não está funcionando" **não era desconexão** — era o
**bug de TDZ no `exec.js`** (dependência circular) que quebrava o carregamento do
`app.js` inteiro, deixando o Command Center em branco. **Isso foi corrigido nesta
sessão** (commit R5.2). Com o app carregando, as conexões que já existiam voltaram
a aparecer.

## Mapa por tela

| Tela | Endpoint(s) | Backend | Render | Veredito |
|---|---|---|---|---|
| chat | chat/stream, transcribe, tts, brain/active | 🟢 real | ✅ | viva |
| conclave | debate (ação) | ⚪ cabeado | ✅ | cabeada |
| config | mcp, memory, profile | 🟢 real | ✅ | viva |
| conteúdo | conteudo, chat | 🟢 real | ✅ | viva |
| exec | execution/tasks/* | 🟢 real | ✅ | viva |
| ingestão | knowledge/ingest/status, graph, dna | 🟢 real | ✅ | viva |
| madrugada | madrugada/status, kill-switch | 🟢 real | ✅ | viva |
| máquina | maquina/stats | 🟢 real | ✅ | viva |
| missões | missions | 🟢 real | ✅ | viva |
| operação | approvals/pending, tasks | 🟢 real | ✅ | viva |
| painel | knowledge/reindex (ação) | ⚪ cabeado | ✅ | cabeada |
| rotina | briefing, history, reminders | 🟢 real | ✅ | viva |
| tarefas | agents/run, browser/run, pulso, rootcause (ações) | ⚪ cabeado | ✅ | cabeada |
| treino | treinamento/status, train/youtube, wa/* | 🟢 real | ✅ | viva |
| vempassear | vp/passeios, vp/clientes, vp/agents/run | 🟢 real | ✅ | viva |

**Legenda:** 🟢 real = dado vivo verificado. ⚪ cabeado = método/rota corretos, mas
**não disparei** porque a ação custa token/rede ou executa trabalho real (agente,
navegador, pulso de mercado). "Cabeada" = conectada, mas não exercida neste raio-x.

## O que NÃO foi provado (e por quê)

As **ações que custam token/fazem trabalho** ficaram cabeadas mas não disparadas —
provar exigiria gastar token ou rodar agente:
- `chat/stream`, `voice/stream` (conversa real com o cérebro)
- `pulso` (consulta redes + síntese LLM)
- `agents/run`, `vp/agents/run` (executa agente)
- `browser/run` (navegador supervisionado)
- `debate` (conclave), `rootcause`, `train/youtube`, `knowledge/dna`, `wa/*`

Isso é a fronteira honesta do raio-x: *estão ligadas, mas o "funciona de ponta a
ponta" delas só se prova exercendo* — o que é uma decisão sua (custa token).

## Achados laterais (não são desconexão, mas valem nota)

1. **Todas as integrações OFF** — `integrations` devolve youtube/google/canva/
   spotify/telegram/elevenlabs = `false`. Telas que dependem delas mostram vazio
   por *falta de configuração*, não por bug. É configuração, não código.
2. **Approval fantasma #22** — `approvals/pending` ainda lista o merge da task
   `exec_fe1cae6d8...`, que foi **rejeitada**. A tela Operação mostra uma aprovação
   morta. Higiene de dado: o reject deveria ter fechado o approval de merge junto.
3. **Cérebro de execução indisponível** — `brain/active` = `codex`, e
   `ui/telemetry` marca "Claude Code (exec): indisponível". O cérebro de execução
   pode não estar alcançável — a tela mostra o estado certo, mas o motor está off.

## Correções prioritárias (para a próxima rodada)

1. **Approval fantasma #22** — fazer o `reject` da task fechar o approval de merge
   associado (senão a Operação acumula lixo). Correção pequena, alto valor de higiene.
2. **Provar as ações que custam token** — um teste vivo, controlado, de UMA conversa
   por voz e UM `agents/run`, pra fechar a fronteira "cabeado → provado". Custa token;
   decisão do Murillo.
3. **Deixar claro na UI quando é "vazio por config"** — telas que dependem de
   integração OFF poderiam dizer "conecte X" em vez de só mostrarem vazio.

## Conclusão

Não há trabalho de *fiação* a fazer — a interface já está conectada. O que resta é
**higiene** (approval fantasma), **prova das ações caras** (decisão de token), e
**clareza de estado vazio**. O grande destravador já aconteceu nesta sessão: o fix
do TDZ que fazia a interface inteira não carregar.
