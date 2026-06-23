# OpenRouter Bench — aplicabilidade e protocolo seguro para o Javis

> Consolidação local em 22/06/2026. As seções 1–10 foram reconstituídas
> exclusivamente do estudo de 21/06 preservado em
> `_ferramentas/integracoes/RESERVATORIOS.md`. Nenhum dado de mercado foi
> pesquisado ou revalidado durante esta consolidação.

## 1. Objetivo

Avaliar OpenRouter, Gemini e referências adjacentes como reservatórios de voz,
inteligência e motor para o Javis, preservando o desenho local-first, a aprovação
humana para ações e o controle explícito de custo.

O estudo não recomenda substituir o cérebro atual de imediato. A proposta é
medir alternativas em uma cascata controlada e decidir com dados de qualidade,
latência, tool-use e custo.

## 2. Resumo executivo do estudo anterior

- OpenRouter já aparecia como opção de integração de baixo esforço por usar API
  OpenAI-compatível e reunir modelos de vários provedores sob uma chave.
- Gemini Flash foi apontado como candidato de baixo custo para turnos leves, mas
  exigiria uma rota nova.
- Fusion foi tratado como referência para o Conclave, não como substituição
  automática.
- SillyTavern foi considerado referência de arquitetura multi-backend/persona,
  sem recomendação de adoção.
- Descript e o ecossistema criativo foram considerados referências futuras para
  o Estúdio, não dependências imediatas.
- O estudo recomendou benchmark pequeno antes de qualquer mudança de roteamento.

## 3. OpenRouter como hub

O valor proposto do OpenRouter é concentrar acesso a múltiplos modelos por uma
interface compatível com o SDK OpenAI. Para o Javis, isso reduz o esforço de
adaptação de texto e tool-use, mas não elimina diferenças reais entre modelos.

O estudo registrou opções gratuitas e pagas, limites de uso e capacidade
multimodal. Esses números pertencem ao levantamento de 21/06 e não foram
revalidados nesta consolidação.

Aplicabilidade pretendida:

- fallback de conversa/tool-use;
- comparação de modelos sem trocar o restante do backend;
- eventual hub de voz, após benchmark separado;
- telemetria única de modelo, tokens, latência, erro e custo.

## 4. Voz: TTS e STT

O estudo registrou endpoints de TTS/STT e modelos de voz acessíveis pelo
ecossistema OpenRouter. A oportunidade seria reduzir integrações dispersas, mas
voz não deve compartilhar automaticamente a mesma política de fallback do chat.

Qualquer avaliação de voz precisa medir separadamente:

- latência até o primeiro áudio;
- qualidade em português do Brasil;
- custo por texto/áudio;
- estabilidade e formato retornado;
- privacidade do conteúdo enviado.

Voz fica fora da primeira alteração de código deste relatório.

## 5. Fusion e relação com o Conclave

`openrouter/fusion` foi descrito como painel paralelo de modelos com um juiz de
síntese, conceitualmente próximo do Conclave do Javis.

Conclusão preservada:

- usar como referência de design ou rota opcional de análise profunda;
- não substituir o Conclave local sem benchmark;
- assumir custo multiplicado pelo painel mais a síntese;
- exigir aprovação específica antes de um teste pago.

## 6. Gemini como rota futura

Gemini Flash foi apontado como candidato de baixo custo para conversa e
raciocínio leve. No desenho proposto, seria uma rota nova
`_respond_gemini`, usando interface OpenAI-compatível quando possível.

O estudo anterior dizia “entre OpenAI e OpenRouter”. A validação real da seção 11
mostra que essa posição precisa considerar também a rota Claude API existente.
Nenhuma implementação Gemini faz parte desta preparação.

## 7. SillyTavern como referência

SillyTavern foi analisado por seu frontend multi-backend, camada de voz,
personas e lorebooks. O encaixe é apenas como referência:

- troca de backend sem reescrever a interface;
- separação entre persona, memória e provedor;
- voz tratada como extensão.

Não há recomendação de instalar ou incorporar SillyTavern ao Javis.

## 8. Descript e pipeline criativo

Descript e ferramentas criativas do ecossistema foram registrados como
reservatório para o Estúdio: modelo barato para rascunho e modelo forte para
acabamento.

Não há integração proposta agora. O fluxo criativo do Javis continua sujeito às
regras do projeto e às ferramentas aprovadas por Murillo.

## 9. Recomendação arquitetural

Não criar `model_router.py` durante esta preparação. Quando aprovado, o local
proposto é:

`_apps/javis-local-interface/backend/model_router.py`

Responsabilidade inicial:

- conter somente a política de seleção/fallback;
- receber adaptadores existentes sem conhecer chaves;
- devolver metadados de roteamento e fallback;
- não executar tools nem ações locais;
- não se confundir com `command_router.py`, `orchestrator.py` ou
  `brain_switch.py`.

A adoção deve começar em `agent.respond()` e só depois alcançar streaming,
`llm_providers.py` e voz.

## 10. Protocolo de benchmark A–E

O benchmark fica dividido para que falhas de engenharia sejam resolvidas offline
antes de qualquer chamada cobrada:

| Etapa | Objetivo | Rede | Regra de segurança |
|---|---|---:|---|
| **A** | Ausência de chave e seleção da cascata | Não | mocks + socket bloqueado |
| **B** | Timeout e erro de provedor | Não | exceções simuladas |
| **C** | Tool-use e formato OpenAI-compatível | Não | cliente fake; tool local interceptada |
| **D** | Uma resposta curta e um tool-use read-only no OpenRouter | Sim, futura | aprovação explícita, modelo em allowlist e tokens baixos |
| **E** | Comparativo final de qualidade/latência/custo | Sim, futura | parar antes de US$ 0,10; sem Fusion/voz no primeiro lote |

Guardrails obrigatórios para D–E:

1. orçamento máximo configurado em `0.10` USD e limite operacional de parada em
   `0.08` USD para margem;
2. execução live bloqueada por padrão e liberada apenas por flag explícita;
3. nenhuma chave, prompt sensível ou header nos logs;
4. telemetria por chamada com modelo solicitado/resolvido, provedor, tokens,
   custo estimado, latência, erro e fallback;
5. interrupção imediata se custo não puder ser estimado;
6. sem Fusion, voz, imagem ou vídeo no primeiro lote;
7. aprovação humana imediatamente antes das etapas D–E.

Fontes preservadas do estudo de 21/06:

- documentação de Models, Rankings, Apps, Fusion e TTS do OpenRouter;
- documentação de rate limits do Gemini;
- repositório SillyTavern;
- página do Descript no OpenRouter;
- referências secundárias registradas em
  `_ferramentas/integracoes/RESERVATORIOS.md`.

## 11. Validação no workspace real do Javis

### Escopo e pasta inspecionada

A validação foi feita em `C:\Users\noteacer\Desktop\javis`, raiz confirmada por
`git rev-parse --show-toplevel`. O aplicativo ativo está em
`_apps/javis-local-interface/`.

A cópia de `OPENROUTER_BENCH_JAVIS.md` não existia nesta raiz nem no histórico Git
local antes desta validação. Para não refazer a pesquisa de mercado, as seções
1–10 foram consolidadas exclusivamente do estudo preservado na seção **E) Motores
& Voz — OpenRouter / Gemini / SillyTavern** de
`_ferramentas/integracoes/RESERVATORIOS.md`.

O conteúdo de `.env` não foi lido e nenhuma chave foi exibida ou testada.

### Arquivos relevantes encontrados

- `_apps/javis-local-interface/backend/agent.py`: contém `_respond_openrouter`,
  `_respond_openai`, `_respond_claude`, `_respond_claude_subscription` e a cascata
  `respond()`; não contém `_respond_gemini`.
- `_apps/javis-local-interface/backend/llm_providers.py`: hoje usa Claude pela
  assinatura como cérebro único; `call_openai` é apenas alias de `call_claude` e
  não há fallback Ollama ativo.
- `_apps/javis-local-interface/backend/orchestrator.py`: roteia entre `main`,
  `conclave`, `squad` e `memory`, mas não escolhe provedores/modelos reais.
- `_apps/javis-local-interface/backend/brain_switch.py`: escolhe Claude Code ou
  Codex para tarefas de programação; não é um roteador de modelos de conversa.
- `_apps/javis-local-interface/backend/server.py`: carrega o `.env` da raiz e
  possui caminhos que usam OpenAI diretamente, especialmente recursos de voz.
- `_apps/javis-local-interface/backend/logger.py`: registra ações em JSONL com
  rotação diária e faz dual-write em SQLite. `agent.py` também registra uso de
  tokens em `_apps/javis-local-interface/_data/token_usage.jsonl`.
- `_apps/javis-local-interface/logs/`: contém logs diários de ações e histórico
  de chat.
- `_apps/javis-local-interface/tests/`: contém 16 arquivos de teste, incluindo
  `test_llm_fallback_offline.py`, que cobre ausência de chave, ordem da cascata,
  timeout, erro, tool-use, sanitização e bloqueio de sockets.
- `_apps/javis-local-interface/backend/_scratch/_test_openrouter.py`: script
  manual live agora bloqueado por padrão; exige flag explícita e orçamento entre
  US$ 0,01 e US$ 0,10, e nunca imprime chave nem prefixo.
- `.env` e `.env.example`: ambos existem. O exemplo ainda cita Ollama, não
  documenta `OPENROUTER_API_KEY`/`JAVIS_OPENROUTER_MODEL` e contém descrições que
  já não refletem toda a cascata atual.
- `_ferramentas/integracoes/`: existe e contém `APIS.md`,
  `RESERVATORIOS.md` e esta validação.
- `_apps/javis-local-interface/backend/ARQUITETURA.md`: existe, mas sua descrição
  de `llm_providers.py` ainda fala em OpenAI/Ollama e fallback local, divergindo do
  código atual.

### O que o estudo anterior acertou

- OpenRouter já está implementado; não é uma integração a começar do zero.
- `_respond_openrouter` usa o SDK OpenAI com `base_url` do OpenRouter, suporta
  tool-use e seleciona o modelo por `JAVIS_OPENROUTER_MODEL`.
- No caminho `agent.respond()`, OpenRouter é o último fallback.
- Gemini seria uma rota nova: `_respond_gemini` ainda não existe.
- A ideia de aproveitar o formato OpenAI-compatível encaixa na estrutura atual e
  permite evolução incremental, desde que a compatibilidade de tools seja testada.

### O que precisa ser ajustado ao código real

- Não existe `model_router.py` nem um roteador de provedores reutilizável. A
  seleção está embutida em `agent.respond()`.
- A cascata não é universal: `agent.respond()` tem quatro etapas;
  `stream_text()` usa Claude assinatura → OpenAI; `llm_providers.py` usa somente
  Claude assinatura; e partes de voz em `server.py` chamam OpenAI diretamente.
- A ordem real inclui Claude API entre OpenAI e OpenRouter. Portanto, “Gemini
  entre OpenAI e OpenRouter” precisa definir se significa antes ou depois de
  Claude API, em vez de presumir uma sequência de três provedores.
- Ollama/local não está ativo no backend atual: foi removido por decisão de
  19/06. As menções em `.env.example` e `ARQUITETURA.md` são documentação obsoleta.
- A presença de `.env` não comprova que OpenRouter esteja configurado; isso não
  foi verificado para preservar segredo e evitar consumo.
- A telemetria OpenRouter foi adicionada a `_log_usage` com modelo solicitado,
  modelo resolvido, provedor, tokens, custo estimado, latência, erro sanitizado e
  indicador de fallback.
- Os testes offline da seleção/falha dos provedores agora existem e bloqueiam
  `socket.connect`, `connect_ex` e `create_connection`.

### Resultado da preparação offline

- `_scratch/_test_openrouter.py` não executa por padrão e não imprime segredo.
- `tests/test_llm_fallback_offline.py`: **9 testes aprovados**, sem rede.
- O custo usa, nesta ordem: valor reportado pelo provedor, zero para modelo
  `:free`, ou rates fornecidos explicitamente por ambiente. Sem uma dessas
  fontes, fica `null` e o protocolo manda interromper o lote.
- Nenhum `.env` real foi lido pelos testes.
- Nenhum provedor externo foi chamado.

### Cascata existente

No fluxo de tool-use de `agent.respond()`, a cascata atual é:

1. Claude pela assinatura (`_respond_claude_subscription`);
2. OpenAI API (`_respond_openai`), se houver configuração;
3. Claude/Anthropic API (`_respond_claude`), se houver configuração;
4. OpenRouter (`_respond_openrouter`), se houver configuração.

Ela é uma cascata de fallback por disponibilidade/erro, não um roteador que escolhe
modelo por custo, latência, tipo de tarefa ou orçamento.

### Onde entraria `model_router.py`

O local coerente é
`_apps/javis-local-interface/backend/model_router.py`, ao lado de `agent.py` e
`llm_providers.py`. Ele deveria começar extraindo apenas a política de seleção hoje
embutida em `agent.respond()`, mantendo os adaptadores `_respond_*` e a execução de
tools em `agent.py`. Depois, poderia ser adotado gradualmente por `stream_text()` e
`llm_providers.py`.

Não deve ser misturado com `command_router.py` (roteamento de intenção),
`orchestrator.py` (seleção de fluxo/agentes) nem `brain_switch.py` (Claude/Codex
para programação).

### Riscos antes de implementar

- Criar mais uma camada sem unificar os caminhos paralelos pode produzir duas
  políticas de fallback contraditórias.
- Modelos OpenAI-compatíveis podem divergir no suporte e no formato de tool calls.
- Fallback automático pode consumir crédito sem ficar evidente, especialmente
  quando uma rota anterior falha.
- Telemetria local é controle de observabilidade, não garantia de cobrança:
  o teto rígido precisa existir também na conta/provedor antes de D–E.
- A flag live evita execução acidental, mas não substitui aprovação humana.
- Documentação/configuração obsoleta pode reintroduzir Ollama ou flags que o código
  já não respeita.
- Uma refatoração ampla de `agent.py`, `llm_providers.py`, streaming e voz de uma
  vez teria alto risco de regressão.

### Próximos 3 passos seguros

1. Rodar A–C offline quando necessário; já estão cobertos pela suíte mockada.
2. Antes de D–E, configurar/confirmar no provedor um limite rígido de US$ 0,10 e
   verificar a allowlist de modelos/preços sem expor a chave.
3. Com aprovação humana específica, habilitar a flag live, usar limite operacional
   de US$ 0,08 e interromper se `estimated_cost_usd` vier `null`.

### Parecer de aplicabilidade

O estudo anterior continua válido em direção e não precisa de nova pesquisa de
mercado. A–C já podem rodar com segurança offline. D–E ficaram protegidos contra
execução acidental e têm telemetria adequada, mas um teto **rígido** de US$ 0,10
não pode ser garantido apenas pelo código local depois que a requisição sai.
Portanto, o benchmark A–E completo pode rodar somente após confirmar o limite de
gasto na conta do provedor e receber aprovação humana imediatamente antes da
execução. Sem essas duas condições, o parecer é **não executar D–E**.
