# Arquitetura do Backend

Documento de referência rápida para os módulos Python de produção do backend. As descrições abaixo foram derivadas das docstrings ou comentários iniciais dos próprios arquivos; scripts de rascunho, depuração e teste não entram aqui.

## Servidor e rotas

- `server.py` — servidor FastAPI do Javis v2; serve o frontend e expõe endpoints como `/chat`, `/status`, `/agents` e `/history`.

## Cérebros e LLM

- `claude_brain.py` — cérebro síncrono de raciocínio do Jamba via Claude Code pela assinatura, usado para decisões estratégicas e análises profundas sem executar tarefas.
- `claude_exec.py` — motor de execução via Claude Code headless para tarefas no projeto, com ferramentas permitidas, escopo restrito ao Javis e sem commit automático.
- `agent.py` — cérebro com tool-use/function calling que decide ferramentas, entende intenção e encadeia ações, com fallback quando não há chave de API.
- `llm_providers.py` — camada de provedores LLM para Claude, OpenAI e Ollama, com fallback local quando as chaves externas não estão disponíveis.
- `conclave.py` — sistema de debate autônomo com três agentes, no fluxo Crítico, Advogado e Sintetizador, em uma ou várias rodadas.

## Memória e conhecimento

- `knowledge.py` — RAG sobre arquivos do Obsidian e do projeto, indexando `.md` e `.txt` com embeddings e busca semântica.
- `briefing.py` — ponte de ESTADO do projeto: lê estado atual, último log, decisões e pendências e monta um resumo factual injetado no system prompt do cérebro (voz e chat) e servido em `/briefing` para a saudação proativa.
- `agents/memory_bridge.py` — ponte de leitura e escrita da memória persistente do Javis, integrando `_memoria/` e `chat_history.jsonl`.
- `profile.py` — memória de personalização que guarda fatos sobre Murillo e injeta esse contexto no prompt do agente.
- `history_store.py` — salva e carrega o histórico de chat entre sessões em armazenamento JSON simples.
- `vp_store.py` — armazenamento local em JSON do painel Vem Passear, persistente entre sessões e sem banco de dados.

## Voz

- `voice_bridge.py` — classifica e executa transcrições de voz, usando o cérebro do servidor para intents seguros conforme a fase indicada no arquivo.

## Integrações e ações

- `integrations.py` — conectores de APIs externas, como YouTube e Google, com degradação elegante quando não há chave no `.env`.
- `actions.py` — executa ações locais da whitelist, sem shell arbitrário.
- `app_launcher.py` — abre aplicativos e recursos do Windows por aliases conhecidos, URIs de sistema ou `start <nome>`.
- `telegram_bridge.py` — controla o Jamba pelo Telegram via long polling, roteando mensagens para ações locais ou para o cérebro principal.
- `browser.py` — oferece busca web e leitura de páginas.
- `site_analyzer.py` — busca uma URL, extrai estrutura e gera análise com esqueleto HTML/CSS similar sem clonar conteúdo protegido.
- `file_analyzer.py` — converte e analisa arquivos com markitdown e LLM, incluindo PDF, Office, CSV, TXT, HTML e imagens.
- `social_reader.py` — lê redes sociais e fóruns sem API paga, usando Reddit JSON público e busca do YouTube via `yt-dlp`.

## Orquestração

- `mission_board.py` — monta o quadro real de orquestramento a partir do backlog do Codex e do log de execução, sem dados inventados.
- `project_registry.py` — registra projetos externos por ponteiros somente leitura, sem absorver nem alterar esses projetos.
- `trend_scout.py` — coleta matéria-prima de estudo por área, buscando vídeos de tendência e repositórios relevantes para `_treinamento/`.
- `code_agent.py` — dispara tarefas de programação para o Codex CLI em segundo plano e notifica quando termina.
- `skill_forge.py` — pipeline Nero que transforma transcrição de especialista em rascunho de `SKILL.md`, com Score de Fidelidade e aprovação humana.
- `jampa_squad.py` — runtime de agentes nomeados do Jampa Jarvis, carregando skills do vault CEREBRO.JAMPA em modo somente leitura.
- `orchestrator.py` — roteador por LLM com multi-brain e squad autônomo, escolhendo entre main, conclave, squad e memory.
- `agents/meta.py` — camada de meta-agentes do Javis, com AIOS Master, Squad Creator e Rootcause coordenando outros agentes.
- `agents/specialized.py` — grade de agentes especializados do Javis, incluindo especialistas, referências ao conclave e meta-agentes.
- `agents/squad.py` — execução colaborativa multiagente com análise individual, debate cruzado e síntese.
- `agents/__init__.py` — ponto de exportação do pacote `agents`, reunindo especialistas, meta-agentes, squad e ponte de memória.

## Utilitários

- `logger.py` — grava eventos em JSONL com rotação diária em `logs/actions-YYYY-MM-DD.jsonl`.
- `command_router.py` — classifica intenções por palavras-chave, sem LLM.
- `reminders.py` — gerencia lembretes e timers em JSON, com fila de vencidos para interface e envio opcional pelo Telegram.
