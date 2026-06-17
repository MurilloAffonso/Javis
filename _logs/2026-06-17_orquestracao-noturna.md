# Decisão: Sessão noturna de orquestração — Javis ↔ Cérebro Jampa

**Data:** 2026-06-17 (madrugada, autorização total de Murillo: "não vai precisar da minha aprovação... depois eu comito")

## O que foi decidido e feito

Murillo pediu pra trazer a estrutura do projeto Vem Passear (Cérebro Jampa) pro
Javis com orquestração real, deixar a interface mais tecnológica com quadro de
orquestramento, criar repositório de treinamento por área conectado a
NotebookLM, acionar o Codex quando fizer sentido, e avaliar Figma. Tudo sem
pedir aprovação a cada passo — review e commit ficam pra Murillo de manhã.

### 1. Registry real conectando CEREBRO.JAMPA (`backend/project_registry.py`)
Lê (somente leitura) `project-manifest.json` e `skills/manifest.json` do
projeto real em `Documents\CEREBRO.CLAUDE\CEREBRO.JAMPA` — sem cópia, sem
absorção. Endpoint novo `/projects/registry`. Frontend (`renderProjects` em
`app.js`) agora hidrata o card "Cérebro Jampa" com dados reais: fase atual,
skills ativas (20/21), data da última atualização da FONTE-DA-VERDADE.
**Achado:** já existia `jampa_squad.py` apontando pro vault real (sessão
anterior já tinha resolvido a conexão squad-a-squad) — não dupliquei, só
completei a parte de metadados de projeto que faltava.

### 2. Quadro de orquestramento real (`backend/mission_board.py`)
A view Workflows usava `MISSIONS`/`WF_NODES` 100% hardcoded (fake). Agora
`mission_board.py` parseia o backlog real do Codex
(`_apps/javis-local-interface/_data/codex_backlog.md`) e transforma cada seção
`## ...` em missão, cada `- [ ]`/`- [x]` em node. Endpoints novos:
`/missions` (lista) e `/missions/{id}/nodes` (tarefas). Frontend separa
fetch de render (`renderMissionsList` / `renderCanvasForMission`) pra clicar
numa missão não resetar o estado vindo do backend.

### 3. Polish visual (via Codex CLI, `codex exec`)
Acionei o Codex diretamente (não o `codex_orchestrator.py`, que auto-commita —
queria controle manual esta noite) pra reforçar a estética sci-fi: grid
animado no canvas de Workflows, glow/scanline em nodes `running`/`online`,
glow nas bordas de `project-card` online. CSS validado (chaves balanceadas),
servidor respondendo normal depois.

### 4. `_treinamento/` por área + ponte com NotebookLM
Criei `_treinamento/{vendas,conteudo,tecnico,estrategia}/{_entrada,_resumos}/`
com README explicando o fluxo: Murillo joga material bruto em `_entrada`,
hoje cola manualmente o resumo do NotebookLM em `_resumos`, e isso entra
automaticamente no RAG do Javis — adicionei `_treinamento` à lista de pastas
indexadas em `knowledge.py`. Endpoint `/treinamento/status` + painel "Áreas de
Estudo" na view Treino (dados reais, hoje zerado — pasta acabou de nascer).
**Não inventei integração com API do NotebookLM** — não existe hoje; o fluxo
é manual até ter API/plugin confirmado.

### 5. Figma — verificado, não executado
Perguntei direto pro Codex (CLI) se ele tem acesso a Figma: **confirmou que
sim, plugin/MCP oficial do Figma conectado** (eu, Claude Code, não tenho
acesso a Figma nesta sessão). Não criei nada no Figma porque não sei em qual
time/arquivo Murillo quer o quadro de orquestramento — criar um arquivo novo
às ciegas na conta dele é a única ação desta sessão que considero arriscada
o suficiente pra esperar uma palavra dele (qual workspace/arquivo Figma usar).
Próximo passo natural: Murillo aponta o arquivo/time Figma e eu acordo o
Codex pra montar o board lá.

## Por quê (visão geral)
Decisão de arquitetura já fixada antes desta sessão: Javis é orquestrador
mestre que CONECTA projetos externos por registry/pointer, não absorve. Esta
sessão materializou isso em código real (antes só estava em planejamento/
memória) e trocou os 3 maiores blocos de dado falso da interface (projetos,
missões, treino) por dados vindos do disco de verdade.

## Não fiz (por design)
- Nenhum `git add`/`commit`/`push` — Murillo revisa e comita.
- Nenhuma vistoria/limpeza do Cérebro Jampa real foi tocada nesta sessão
  (ficou pendente de antes — ver [[javis-cerebro-jampa-real]]).
- Nenhuma criação em Figma (ver seção 5).

## Próximo passo
1. Murillo revisa o diff inteiro, decide o que comitar.
2. Murillo diz qual workspace/arquivo Figma usar → acordo o Codex.
3. Retomar a vistoria/limpeza do Cérebro Jampa real (pendente de antes).
4. Quando o NotebookLM tiver API/plugin confirmado, automatizar o passo
   manual de `_treinamento/*/_resumos`.

---

## Continuação (mesma madrugada): esquadrões de estudo + quadro de projeto inteiro

Murillo pediu explicitamente pra continuar sem parar e expandir: "bote os
esquadrões pra estar estudando, coletando vídeo de tendência, olhando
repositório" e que o workflow seja "de todo o projeto".

### 6. Esquadrão de estudo real (`backend/trend_scout.py`, NOVO)
Cada área (`vendas`, `conteudo`, `tecnico`, `estrategia`) tem buscas reais
(YouTube Data API via `integrations.youtube_search_many`, GitHub via API
pública `integrations.github_search_repos`) que jogam o achado em
`_treinamento/<área>/_entrada/` como `.md` com fonte/data, sem duplicar
(dedupe por URL). Endpoints `POST /treinamento/scout/{area}` e
`POST /treinamento/scout-all`. Testado ao vivo (curl + clique real no
Playwright): rodou as 4 áreas, 24 itens novos coletados (vídeos + repos),
um deles literalmente um vídeo sobre "NotebookLM API Enterprise-Only Access"
— relevante pro gap documentado no passo 4. Botão "🔍 buscar tendência" por
área + "Esquadrões: buscar tudo" na view Treino, testados clicando de verdade
no browser (Playwright), sem erros novos no console.

### 7. Quadro de orquestramento agora cobre o projeto inteiro
`mission_board.py` ganhou 2 missões sintéticas (derivadas de dado real, não
de checklist): `esquadrao-de-estudo` (status de `_treinamento` por área) e
`projetos-externos` (status do registry — Cérebro Jampa). Endpoint `/missions`
agora devolve 5 missões: as 3 do backlog do Codex + essas 2 novas. Testado no
browser: lista renderiza, clique troca o canvas e desenha os nodes certos.
Centralizei a contagem de `_treinamento` em `trend_scout.all_status()` (antes
duplicada dentro do server.py) pra não ter duas fontes de verdade divergindo.

### Ainda não fiz (mesmos motivos de antes)
- Nenhum commit/push.
- Nada no Figma (sem saber workspace/arquivo).
- NotebookLM continua manual — o esquadrão só coleta matéria-prima, não resume.

---

## Continuação: tarefa real do backlog concluída (5 roteiros de Reel) + ElevenLabs

### 8. Backlog do Codex — "5 roteiros de Reel" concluído de verdade
Acionei `codex exec` pra tarefa real `_data/codex_backlog.md`. 1ª tentativa
(timeout 180s meu, não dele) matou o processo antes de escrever o arquivo —
não inventei sucesso, confirmei que o arquivo não existia e tentei de novo
em background sem timeout. 2ª tentativa terminou, mas **saiu sem acentuação
em português** (bug de encoding na execução via PowerShell do Codex — só 2
caracteres acentuados no arquivo todo, contra 44 no arquivo de referência da
sessão anterior). Mandei o Codex reler e corrigir a acentuação — voltou bom
(61 caracteres acentuados), MAS super-corrigiu e colocou acento DENTRO das
hashtags (`#JoãoPessoa`), o que quebra a convenção real do projeto (hashtags
sem acento — confirmei comparando com `legendas-instagram-01.md`:
`#JoaoPessoa`, `#Picaozinho` etc., sem acento). Corrigi eu mesmo com um
script Python cirúrgico que tira acento SÓ dentro das linhas `**Hashtags:**`,
preservando a acentuação correta no resto do texto. Resultado final:
`_projetos/cerebro-jampa/posts/roteiros-reel-01.md` (155 linhas, 5 roteiros
completos) — texto correto, hashtags no padrão certo. Marquei `[x]` no
backlog (`_data/codex_backlog.md`) porque a tarefa foi de fato executada e
verificada — missão "Conteúdo Vem Passear Jampa" no quadro de orquestramento
subiu de 25% pra 50% automaticamente (confirmado via `/missions`).

**Lição:** Codex via `codex exec` redirecionado por shell no Windows pode
perder acentuação. Sempre verificar contagem de caracteres acentuados
(`grep -c "ã\|ç\|é..."`) contra um arquivo de referência antes de considerar
uma tarefa de conteúdo em PT-BR como concluída — e cuidado com correções
automáticas "passando demais" (acento dentro de hashtag).

### 9. ElevenLabs — pesquisa real na org do GitHub (a pedido de Murillo)
Murillo pediu pra olhar github.com/elevenlabs pra melhorar comando de voz e
avaliar conexão com Codex/Claude no orquestrador. Mapeei a org via
`gh api orgs/elevenlabs/repos` (não inventei nada — dados reais). 3 achados
concretos:
- `elevenlabs-mcp` (1.4k⭐) — MCP server oficial; eu/Codex podemos usar TTS,
  clonagem de voz, STT como ferramenta direta na sessão.
- `claude-plugins` (elevenlabs-stt) — plugin oficial de Claude Code, STT por
  hotkey — Murillo fala direto comigo sem teclar.
- `packages` (ElevenAgents SDK) — Conversational AI real-time com
  function-calling nativo — é o caminho real pra "raciocinar através da fala
  em tempo real" que Murillo descreveu, mas exige criar um Agent no painel
  deles (decisão/conta dele).

**Preparei o terreno (inerte sem key):** `.env` com `ELEVENLABS_API_KEY=`
pronto; `backend/voice_elevenlabs.py` (NOVO) — adaptador TTS/STT/voices no
mesmo padrão de degradação elegante do resto do projeto; `integrations.available()`
agora reporta `elevenlabs`. Documentado com detalhe em
`_ferramentas/integracoes/RESERVATORIOS.md` (seção D, nova).

**Decisão que só Murillo pode tomar:** pegar a key grátis e escolher entre
upgrade simples de voz vs. redesenho completo pra Conversational AI em tempo
real (mais trabalho, mais perto do que ele descreveu).

### 10. Mais 2 itens reais do backlog concluídos
- **Templates de WhatsApp** (`codex exec`, background, sem timeout artificial)
  — saiu certo de primeira (acentuação correta, sem hashtag no arquivo, então
  não havia o risco de over-correction da vez passada). Salvo em
  `_projetos/cerebro-jampa/posts/templates-whatsapp.md` (5 categorias:
  primeiro contato, maré/horário, preço, confirmação, pós-passeio).
- **`renderAgentGallery()` (Interface Javis)** — fiz eu mesmo direto em
  `frontend/app.js` (não pedi pro Codex, já estava com o arquivo aberto e é
  trabalho de UI que prefiro controlar): adicionei a cada agente `lastActivity`
  e `queue` (dados ainda mock, mesma natureza dos outros campos dessa galeria
  fictícia), badge "🕓 há Xmin", indicador "📥 N tarefas", e botão **Convocar**
  que faz `switchView('chat')` + preenche `@Nome ` no input — função nova
  `convocarAgente()`, sem tocar em `openAgentChat()` existente. CSS novo
  (`.gc-footer`, `.gc-convocar-btn` etc.) seguindo o padrão visual já usado.
  Testado de verdade no Playwright: clique no botão troca a view, preenche o
  input corretamente, `stopPropagation()` funciona (não abre o chat genérico
  do card por baixo), zero erros no console.

Quadro de orquestramento confirma o avanço real via `/missions`: "Conteúdo
Vem Passear Jampa" 75% (3/4), "Interface Javis" 100% (1/1), "Projetos
Externos" 100%. Restam: SEO checklist (Cérebro Jampa) e o esquadrão de
estudo (que já está rodando, mas ainda não tem nenhum resumo no RAG).

### 11. SEO checklist concluído + 3 melhorias visuais/UX reais (último item do backlog)

**SEO checklist** (`codex exec`, background) — `_projetos/cerebro-jampa/seo-checklist.md`,
10.4KB, 5 quick wins do `seo-plano.md` transformados em passo a passo
específico (GBP, Instagram, WhatsApp Business) com responsável (Murillo/Nova/
Midas) e tempo estimado por etapa. Acentuação validada (56/46/28 ocorrências
de ã/ç/é) — saiu certo de primeira, sem necessidade de correção.

**3 melhorias visuais/UX** (último checkbox do backlog, item "Interface
Javis" da seção Conteúdo) — fiz eu mesmo direto em `app.js`/`style.css`,
sem acionar o Codex:
1. Fade-in suave ao trocar de view (`@keyframes view-fade-in`, opacity+translateY,
   0.22s) — antes a troca de view era instantânea/seca.
2. `:focus-visible` global (outline violeta) — gap real de acessibilidade,
   nenhum elemento tinha indicador de foco visível pra navegação por teclado
   além dos poucos inputs que já tratavam isso manualmente.
3. Estado vazio em `renderAgentGallery()` (`.gallery-empty`) — defensivo, pra
   quando um filtro de esquadrão não tiver nenhum agente, em vez de grid
   em branco sem explicação.

Cheguei a suspeitar de um bug real (`\${m.tasks_total}` aparentemente escapado
na linha do `mi-meta`) — investiguei com `sed -n | cat -A` no arquivo real e
confirmei que era só artefato de exibição da minha ferramenta de busca, não
um bug de verdade. Não mudei nada ali; lição: sempre confirmar no arquivo
bruto antes de "corrigir" algo que pareceu suspeito.

Todas as 3 melhorias testadas de verdade no Playwright (animação aplicada,
regra de CSS presente no documento, filtro funcionando), zero erros novos
no console.

**Resultado: backlog do Codex 100% concluído.** `/missions` confirma:
"Conteúdo Vem Passear Jampa" 100% (4/4), "Interface Javis" 100% (1/1),
"Cérebro Jampa — SEO" 100% (1/1), "Projetos Externos" 100%. Só o "Esquadrão
de Estudo" continua em 0% (não é backlog — é status do RAG, que depende do
passo manual do NotebookLM que Murillo ainda não fez).

### 12. Agendamento da continuação (a pedido de Murillo)
Murillo avisou que a cota de uso desta sessão Claude vai esgotar em breve e
pediu um agendamento pra retomar o ciclo automaticamente às 2h da madrugada
de quarta (17/06). Criei via `CronCreate` (one-shot, `durable: true`) —
job `9749522d`, cron `4 2 17 6 *`. **Ressalva importante:** o próprio
`CronList` reportou o job como `[session-only]` mesmo com `durable: true`
pedido — ou seja, não há garantia de que sobrevive se o processo do Claude
Code for encerrado de verdade (só se a sessão ficar "viva" esperando).
Avisei o Murillo disso diretamente e disse que, se não disparar, ele mesmo
pode abrir uma sessão nova e pedir "continua de onde parou" — este log e a
memória têm contexto suficiente pra eu retomar sem perda nenhuma.

### Estado final desta madrugada (16→17/06)
- Backlog do Codex: **100% concluído**, todo conteúdo validado manualmente
  (acentuação + convenção de hashtag) antes de marcar `[x]`.
- Quadro de orquestramento: reflete o projeto inteiro (Codex + esquadrão de
  estudo + projetos externos), dado real em todas as 5 missões.
- Esquadrão de estudo: rodando e coletando (24 itens em `_entrada` nas 4
  áreas), mas RAG ainda zerado — depende do passo manual do NotebookLM.
- ElevenLabs: pesquisado e documentado, terreno preparado no código, decisão
  de conta/key pendente do Murillo.
- Nenhum commit/push feito. Nada criado no Figma.

### 13. Esquadrão de estudo: de 0% pra 100% (sessão retomada via cron às 2h de 17/06)

Cron `9749522d` disparou (ou a sessão foi retomada manualmente — de toda
forma, contexto recuperado 100% via este log + memória, sem perda).

**Achado real de qualidade ao revisar os 8 repos coletados:** 2 deles
(`AyushmanTyagi/Decentralized-Finance-It-s-use-cases` e
`sanchitapatil/SwiggySalesUserAnalytics`, ambos na área "estratégia") eram
completamente irrelevantes — um sobre DeFi/criptomoeda, outro sobre
analytics de delivery indiano. Causa raiz: a query do GitHub pra
"estratégia" em `trend_scout.py` era genérica demais (`"business strategy
dashboard open source"`), trazendo ruído de repositórios de estudante sem
relação com turismo/negócio local. Corrigi a query pra
`"small business growth strategy playbook"` + `"tourism business analytics
dashboard"` e re-rodei o scout só dessa área — trouxe 3 repos genuinamente
relevantes (CRM/growth playbook, análise de dados de turismo, dashboard de
turismo do Havaí com forecasting).

**Resumos reais escritos (eu, Claude, lendo README/descrição real de cada
repo via `gh api` — não fabriquei conteúdo de vídeo que não vi):**
- Técnico: crewAI, Haystack (referência de arquitetura multi-agente/RAG).
- Conteúdo: AI Marketing Automation, PNBS Instagram Pipeline (referência de
  pipeline de conteúdo automatizado/monitoramento de concorrência).
- Vendas: Agentic GTM Automation, Smart WhatsApp AI CRM (referência de
  automação de follow-up e atendimento).
- Estratégia: Hawaii Tourism Dashboard (referência de dashboard preditivo
  pra turismo local — contexto de negócio mais parecido com o Vem Passear
  Jampa até agora).

**Decisão deliberada de não fabricar:** os 20 stubs de vídeo no `_entrada`
continuam sem resumo — só tenho o título deles, não o conteúdo/transcript,
então escrever um "resumo" seria inventar. Esse passo continua manual via
NotebookLM, como já estava documentado. Só resumi repositórios, onde eu
realmente consegui ler a fonte primária (README/descrição via API).

**Resultado:** `/missions` confirma "Esquadrão de Estudo" 0% → 100% (4/4
áreas com pelo menos 1 resumo real). Verificado também na UI ao vivo
(view Treino, Playwright): Vendas 7 entrada/2 resumidos, Conteúdo 7/2,
Técnico 6/2, Estratégia 11/1 — bate exatamente com os arquivos criados.
Zero erros de console.

**Backlog 100% + Esquadrão 100% + Interface 100% + SEO 100% + Projetos
Externos 100% = as 5 missões do quadro de orquestramento em 100%.**

Ainda pendentes (não fazem parte de nenhuma missão, dependem do Murillo):
decisão sobre profundidade da integração ElevenLabs (precisa de
`ELEVENLABS_API_KEY`); criação de board no Figma (precisa de Murillo
apontar workspace/arquivo); resumir os 20 vídeos coletados (passo manual
do NotebookLM).

### 14. Tentativa real de automatizar resumo de vídeo (parcialmente bloqueada — documentando com honestidade)

Investiguei se dava pra fechar de verdade o gap dos 20 vídeos sem depender
do NotebookLM: `youtube-transcript-api` já estava instalado no ambiente.
Adicionei `integrations.youtube_transcript(url)` (degrada pra `None` sem
quebrar nada, mesmo padrão das outras funções do arquivo) e testei —
**funcionou de verdade**: busquei a legenda real de um vídeo
("AGENTES DE IA: como criar...") e recebi 25k caracteres de transcript em
português correto. Rodei a checagem de disponibilidade nos 20 vídeos
coletados: 18/20 tinham legenda real disponível (2 sem legenda).

**Mas ao tentar buscar o texto completo dos 18 em sequência rápida pra
escrever os resumos, o YouTube bloqueou o IP** (`IpBlocked` — rate limit
da própria API não-oficial de transcript, esperado pra esse tipo de
ferramenta sem chave). Não force-tentei de novo em loop (evitar bater
repetidamente num serviço externo que já sinalizou bloqueio). Resultado
honesto: a capacidade está construída, testada e funcionando (`requirements.txt`
atualizado com `youtube-transcript-api>=1.2`), mas os resumos dos vídeos
NÃO foram escritos nesta sessão — ficam pendentes pra uma próxima rodada,
espaçada (poucos vídeos por vez, não os 18 de uma vez), quando o bloqueio
de IP expirar. Suíte de testes seguiu 54/54 depois dessa mudança.

**Por que isso importa:** antes a única forma de resumir vídeo era manual
via NotebookLM. Agora existe um caminho automatizável real (buscar
transcript → eu leio e resumo de verdade, sem inventar) — só precisa rodar
com calma (1-2 vídeos por sessão, não em lote) pra não disparar o bloqueio
de IP do YouTube.
