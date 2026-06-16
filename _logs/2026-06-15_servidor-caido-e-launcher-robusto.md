# 2026-06-15 — Servidor caído ao atualizar + launcher robusto

## Contexto
Murillo fechou o Javis para "dar uma atualizada" e ele não voltou a abrir.
Print da interface mostrava o orbe travado em `PROCESSANDO… raciocinando… /
OUVINDO aguardando voz…`. Relatou também: (a) responde uma vez e depois quebra /
"vaza o raciocínio"; (b) o botão "site" não avisa nada.

## Diagnóstico
- **Causa raiz:** o backend estava **caído** — porta 8000 livre, nenhum processo
  Python rodando. O `import server` roda sem erro (testado), então não era bug de
  código: o servidor simplesmente não tinha sido iniciado de novo.
- O `javis-start.bat` antigo checava a porta com
  `netstat -an | findstr ":8000 "` e, se achasse **qualquer** coisa na porta
  (inclusive estado preso/TIME_WAIT), pulava o boot e só reabria o browser —
  apontando para um servidor morto. Subia o server com `/MIN` (janela escondida),
  dificultando ver erro.
- **Sintomas (a) e (b):** muito provavelmente reflexo do servidor morto
  (respondia do cache e quebrava). O botão "site" está **correto por design**:
  ao clicar, preenche `analisa o site ` no campo e espera a URL; sem URL,
  `site_analyzer.analyze` retorna *"Não achei uma URL…"*. Não reproduzido ao vivo.

## O que foi feito
1. **Subi o servidor** (`backend/server.py`): porta 8000 LISTENING,
   `Application startup complete`, HTTP `/` → 200.
2. **Reescrevi `javis-start.bat`** para ser robusto:
   - Health check real via `curl -s -o nul -m 2 http://localhost:8000/`
     (em vez de só checar a porta). `curl` confirmado em `System32\curl.exe`.
   - Se não responder: sobe o server em **janela visível** (sem `/MIN`) e faz
     **polling de até ~25s** até responder antes de abrir o browser.
   - Não gera processo duplicado: só inicia quando o health check falha.

## Por quê
O launcher antigo dava a falsa impressão de que o Javis estava no ar quando o
servidor não estava respondendo. O novo garante que o browser só abre depois que
o backend responde de fato.

## Verificação
- `curl http://localhost:8000/` → `status=200` (antes e depois da reescrita).
- `import server` → `IMPORT OK` (sem erro de startup).
- `curl` disponível: `C:\Windows\System32\curl.exe`.

## Parte 2 — Análise da conversa real (chat_history.json) e correções

Murillo pediu para auditar a conversa salva. O histórico mostrava o Jamba
**recusando ações** ("não consigo abrir sites/YouTube") em frases naturais,
enquanto comandos curtos exatos ("abre o projeto") funcionavam.

### Diagnóstico
- **Recusas eram de servidor em estado quebrado** (código velho / fallback sem
  ferramentas). Testado AO VIVO com o código atual: gpt-4o-mini chama as
  ferramentas certas para todas as frases que antes recusavam
  (`abrir_navegador`, `abrir_site`, `abrir_youtube`, `tocar_musica`,
  `analisar_site`). O agente está saudável.
- **Bug real nº 1 — pasta nomeada:** "abre minha pasta de documentos" caía em
  `abrir_app("explorador de arquivos")` genérico → Explorer no lugar padrão.
- **Bug real nº 2 — análise de site:** a ferramenta disparava, mas:
  - o nome próprio "Vem Passear" sem URL não resolvia;
  - o modelo às vezes passava TLD errado (`vempassear.com.br`, que não resolve);
  - **causa raiz:** `llm_providers.call_claude` → Anthropic retorna **400 "credit
    balance too low"** (chave SEM CRÉDITO) → caía no **Ollama (offline)** →
    timeout de 30s → erro "não consegui acessar o site". Atingia TUDO que usa
    `call_claude` (análise de site, conclave, main brain de reserva).

### Correções aplicadas (nada commitado)
1. `app_launcher.py`: nova `open_folder(nome)` + `KNOWN_FOLDERS`
   (Documentos/Downloads/Imagens/Vídeos/Música/Desktop → caminho real do perfil,
   com fallback OneDrive) + helper `_norm` (sem acento).
2. `agent.py`: nova ferramenta `abrir_pasta(nome)` + dispatch em `_exec_tool`.
3. `site_analyzer.py`: `KNOWN_SITES` ("vem passear" → https://vempassearjampa.com)
   com **prioridade máxima** em `_extract_url` (corrige TLD errado); User-Agent de
   browser real + Accept-Language.
4. `llm_providers.py`: `call_claude`/`stream_claude` agora caem em **OpenAI**
   (cérebro configurado, com saldo) antes do Ollama; timeout do Ollama 30s→8s
   (`JAVIS_OLLAMA_TIMEOUT`). Erro do provedor agora é logado (`[llm] …`).

### Verificação (parte 2)
- `open_folder`: documentos/downloads/imagens/desktop/música resolvem para dirs
  existentes; desconhecida → erro amigável.
- `_extract_url`: "Vem Passear", "vempassearjampa.com.br" e
  "https://www.vempassearjampa.com.br/" → todos `https://vempassearjampa.com`;
  github.com/stripe.com preservados.
- Agente escolhe `abrir_pasta` para as 3 frases de pasta.
- `_brain('Analise meu site Vem Passear')` → análise real do site (via fallback
  OpenAI), `status=agent`, `tools=['analisar_site']`.
- **54 testes passando** (pytest) após todas as mudanças.

### ⚠️ Achado importante para o Murillo
- **ANTHROPIC_API_KEY está SEM CRÉDITO** (400). O Javis vinha dependendo de um
  provedor morto e caindo no Ollama offline. Agora o fallback é OpenAI (tem
  saldo). Decisão: comprar crédito Anthropic OU seguir 100% OpenAI.
- A análise de site com `generate_code=True` leva ~24s (tenta Anthropic, falha,
  faz 2 chamadas OpenAI: análise + esqueleto HTML). Lento para voz — avaliar
  desligar a geração de código no fluxo de voz depois.

## Parte 3 — Decisão: 100% OpenAI

Murillo decidiu seguir **100% OpenAI**. Implementado em `llm_providers.py`:
- Gate `_anthropic_enabled()` — Anthropic só roda se `JAVIS_USE_ANTHROPIC=1` E
  houver `ANTHROPIC_API_KEY`. **Default = OpenAI direto** (não bate mais na
  Anthropic, elimina o 400 + o ~1s desperdiçado por chamada).
- `call_claude` → `call_openai` direto quando desabilitada.
- `stream_claude` → novo `_stream_openai` (streaming real de tokens via OpenAI).
- `.env.example` reescrito: OpenAI como provedor padrão; Anthropic opcional/desligada.
- Verificado: `call_claude` 3,6s sem tocar Anthropic; análise de site `status=ok`;
  **54 testes passando**.

Reversível: `JAVIS_USE_ANTHROPIC=1` religa o Claude se ele comprar crédito.

## Pendências / próximo passo
- **Confirmar com o Murillo** se, com o servidor de pé, os sintomas (a)
  "vazar o raciocínio"/resposta dupla e (b) botão "site" persistem. Se sim,
  investigar `/chat/stream` em `server.py`. Sem reproduzir, não dá para corrigir.
- Servidor foi subido por dentro da sessão remota; Murillo deve rodar o
  `javis-start.bat` uma vez para deixá-lo independente.
- Nada commitado — `javis-start.bat` modificado, aguardando aprovação.
