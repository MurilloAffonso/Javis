# Reservatórios de Tendência — curadoria para o Jamba

Pesquisa de junho/2026 das fontes (APIs e repositórios) mais acessadas, **pontuadas pelo encaixe no projeto Jamba** (assistente JARVIS pessoal, voz, multi-cérebro Claude+OpenAI, Ollama local, Windows, memória Obsidian).

Escala de encaixe: 🟢 alto · 🟡 médio · ⚪ baixo (por enquanto)

---

## A) APIs mais acessadas — o que cada uma desbloqueia no Jamba

| API | Encaixe | O que dá por voz | Esforço | Custo |
|-----|:---:|------------------|---------|-------|
| **OpenWeather** | 🟢 | "que tempo faz hoje, senhor?" | Fácil (1 key) | Grátis |
| **Telegram Bot** | 🟢 | Controlar o Jamba pelo **celular** (mandar comando, receber resposta) | Fácil (1 token) | Grátis |
| **NewsAPI** | 🟢 | Resumo diário de notícias ("o que tá rolando?") | Fácil (1 key) | Grátis (100/dia) |
| **ElevenLabs** | 🟢 | Voz **ainda mais humana** (e clonável) — upgrade do TTS atual | Fácil (1 key) | Free tier |
| **YouTube Data v3** | 🟢 | Tocar a música **exata** (já estruturado) | Fácil (1 key) | Grátis |
| **GitHub API** | 🟡 | Acompanhar repos/commits (você é dev) | Fácil (token) | Grátis |
| **Google Calendar/Gmail** | 🟡 | Agendar, ler e-mails por voz | Médio (OAuth) | Grátis |
| **Notion API** | 🟡 | Ler/escrever notas e bancos de dados | Fácil (token) | Grátis |
| **Unsplash** | 🟡 | Imagens p/ os entregáveis (landing pages que o Jamba gera) | Fácil (key) | Grátis |
| **Mapbox / Google Maps** | 🟡 | Localização, rotas, clima local | Médio | Free tier |
| **Spotify** | 🟡 | Música no player do Spotify (alternativa ao YouTube) | Médio (OAuth) | Premium p/ playback |
| **CoinGecko / CoinMarketCap** | ⚪ | Cripto/finanças (não é foco do projeto) | Fácil | Grátis |

**Fonte-mãe:** o repositório [public-apis/public-apis](https://github.com/public-apis/public-apis) (lista coletiva de centenas de APIs grátis) — bom para garimpar quando surgir necessidade nova.

---

## B) Repositórios JARVIS open-source — reservatórios de ideias/código

Projetos em alta que valem como referência de arquitetura (não para copiar, mas para inspirar padrões):

| Repo | Encaixe | Por que olhar |
|------|:---:|---------------|
| **rezaulhreza/jarvis** | 🟢 | Local-first com **Ollama**, criação de skills em runtime, **visualizador de onda de voz**, web UI com WebSocket. Quase o gêmeo do Jamba. |
| **Srijan-D/Jarvis-AI-Assistant** | 🟢 | "play Faded on youtube", automação de **WhatsApp/YouTube**, hotword tipo "Alexa". Bate direto com seus objetivos de tocar música e controle por voz. |
| **isair/jarvis** | 🟡 | 100% privado/offline, controla o Chrome, checa a web, **tools via MCP** sem "context rot". Boa referência de arquitetura de ferramentas. |
| **OpenJarvis (Stanford SAIL)** | 🟡 | Pesquisa "Intelligence Per Watt", **descoberta de skills** por agentes, digest matinal, Google Drive. Referência de coordenação de agentes. |

---

## C) Recomendação — o que faz sentido plugar AGORA

Pelo encaixe + esforço baixo, a ordem que eu sugiro, senhor:

1. **Telegram Bot** 🟢 — falar com o Jamba pelo celular de qualquer lugar. Token grátis em 2 min (@BotFather).
2. **OpenWeather** 🟢 — clima por voz. Fecha o "kit mordomo" (hora + clima + notícias).
3. **YouTube Data v3** 🟢 — destrava tocar a música exata (já está codado, falta só a key).
4. **ElevenLabs** 🟢 — se quiser a voz no nível "humano de verdade", além do onyx atual.

Depois (mais trabalho, mais valor): **Google Calendar/Gmail** para virar um assistente de agenda completo.

---

## D) ElevenLabs — aprofundado a pedido de Murillo (16/06, madrugada)

Murillo pediu pra olhar a org `github.com/elevenlabs` direto e ver se dá pra
plugar no orquestrador (Codex/Claude), não só no TTS do app. Mapeei os
repositórios reais da org (`gh api orgs/elevenlabs/repos`) e achei 3 encaixes
concretos, cada um resolvendo uma parte diferente do pedido:

| Repo | O que resolve | Encaixe no Javis |
|------|----------------|-------------------|
| **[elevenlabs-mcp](https://github.com/elevenlabs/elevenlabs-mcp)** (1.4k⭐) | MCP server oficial — TTS, clonagem de voz, STT, soundscapes | Conecta DIRETO em mim (Claude Code) e no Codex como ferramenta MCP. Eu/Codex passamos a poder gerar voz de verdade, clonar, transcrever — sem precisar do backend do Javis no meio. `uvx elevenlabs-mcp` + `ELEVENLABS_API_KEY` no config do client MCP. |
| **[plugins (elevenlabs-stt)](https://github.com/elevenlabs/claude-plugins)** | Plugin oficial de Claude Code — STT por hotkey (Ctrl+Shift+Space) | Murillo fala DIRETO comigo (Claude Code) sem teclar — `/plugin marketplace add elevenlabs/claude-plugins` + `/plugin install elevenlabs-stt`. |
| **[packages — ElevenAgents SDK](https://github.com/elevenlabs/packages)** | `@elevenlabs/client`/`react` — Conversational AI real-time (WebRTC), function-calling nativo (client tools), baixa latência | É o caminho pra "captar e raciocinar através da fala em tempo real" que Murillo descreveu — um agente de voz configurado no painel do ElevenLabs que chama as MESMAS tools do Javis (`agent.py`) como "client tools". Maior esforço: precisa criar o Agent no dashboard ElevenLabs (agentId) e migrar o front de Whisper+TTS-OpenAI pra esse SDK. |

**O que já preparei no código (sem key, então tudo inerte até Murillo plugar):**
- `.env`: bloco `ELEVENLABS_API_KEY=` comentado, pronto pra receber a key.
- `backend/voice_elevenlabs.py` (NOVO): adaptador `text_to_speech`,
  `speech_to_text`, `list_voices` — mesmo padrão de degradação elegante do
  `integrations.py` (sem key → `None`/`[]`, sem quebrar nada).
- `integrations.available()` agora reporta `elevenlabs: bool` (aparece no
  `/painel` quando a key existir).

**O que falta SER DECISÃO do Murillo (não posso fazer sozinho):**
1. Criar a conta ElevenLabs + pegar a key grátis (10k créditos/mês) →
   colar em `.env`.
2. Decidir se quer só upgrade de voz (fácil, já preparado) ou o redesenho
   completo pra Conversational AI em tempo real com tool-calling (precisa
   criar um Agent no dashboard deles, é mais trabalho, mas é o que bate
   exatamente com "raciocinando através da fala em tempo real").
3. Se quiser eu/Codex usando ElevenLabs como ferramenta MCP (gerar/clonar voz
   direto nas nossas sessões), aí é configurar o `elevenlabs-mcp` no
   `claude_desktop_config.json` (ou no MCP do Codex) com a mesma key.

## Como decidir tecnicamente

`backend/integrations.py` já tem `available()` que detecta quais keys existem no `.env`. Conforme você for plugando, cada ação tenta a API e cai no fallback se não houver key — então dá pra crescer aos poucos sem quebrar nada.

**Fontes da pesquisa:**
- [public-apis/public-apis (GitHub)](https://github.com/public-apis/public-apis)
- [20 Most Popular APIs 2026 (API League)](https://apileague.com/articles/most-popular-apis/)
- [Best Free AI APIs 2026](https://crazyburst.com/best-free-ai-apis-2026/)
- [rezaulhreza/jarvis](https://github.com/rezaulhreza/jarvis) · [Srijan-D/Jarvis](https://github.com/Srijan-D/Jarvis-AI-Assistant) · [isair/jarvis](https://github.com/isair/jarvis) · [OpenJarvis](https://github.com/open-jarvis/OpenJarvis)

---

## E) Motores & Voz — OpenRouter / Gemini / SillyTavern (estudo 21/06)

Murillo pediu uma análise de especialista entrando no **OpenRouter** (modelos,
rankings, apps, "Fusão", chat, voz), no **Descript** e no **SillyTavern**, pra
decidir o custo-benefício dos reservatórios de **voz, inteligência e motor** — e
avaliar a jogada de plugar o **Gemini grátis** como motor/voz.

> **Achado-âncora:** o OpenRouter **já está no código** como último fallback da
> cascata (`backend/agent.py` → `_respond_openrouter`, usando
> `meta-llama/llama-3.3-70b-instruct:free`). Cascata atual de tool-use:
> **Claude assinatura → OpenAI → Claude API → OpenRouter**. Então "plugar
> OpenRouter" é **aprofundar uma rota que já existe**, não criar do zero.

### E.1 — OpenRouter como HUB (1 key: inteligência + voz)

Surpresa que muda a conta: o OpenRouter **não é só texto** — desde 2026 tem
endpoint `/api/v1/audio/speech` (OpenAI-compatível) pra **TTS de voz** e STT.
Dá pra usar **uma chave só** como hub de voz + inteligência + motor.

| Eixo | O que o OpenRouter oferece | Encaixe |
|------|-----------------------------|:---:|
| **Inteligência (texto)** | 26 modelos **grátis** (Llama 3.3 70B, Qwen3 Coder 1M ctx, Gemma 4 31B, GPT-OSS 120B, Nemotron). Mercado jun/2026: DeepSeek 16,3% do volume, Claude 2º, Google 13,2%, chineses 45%+. Free tier ~20 req/min, 200/dia, **sem cartão**. | 🟢 |
| **Voz (TTS/STT)** | `/audio/speech`: **Grok Voice TTS** (5 vozes, 20+ idiomas), Gemini Flash TTS, Voxtral Mini, GPT-4o mini TTS + STT. Mesma key, mesmo billing do texto. | 🟢 |

**Custo-benefício:** consolida o que hoje está espalhado (Whisper STT + TTS
OpenAI/ElevenLabs + multi-cérebro) sob 1 key/fatura. Esforço baixo (a rota já
existe). Limite: modelos grátis têm rate-limit e o billing é da conta do Murillo.

### E.2 — Fusão (Fusion) = o Conclave, gerenciado

`openrouter/fusion`: um painel de modelos responde em paralelo e um **juiz**
sintetiza — consenso, contradições, cobertura parcial, insights únicos, pontos
cegos. **É conceitualmente o `consultar_especialistas`/Conclave do Javis.**

- Custo: ~**4-5×** uma chamada única (N do painel + 1 juiz).
- Ganho: painel **barato** (Gemini 3 Flash + Kimi K2.6 + DeepSeek V4) **supera
  modelos de fronteira** isolados nos benchmarks deles.
- **Encaixe 🟡** — não substituir o Conclave; usar como referência de design, ou
  como rota opcional do `pensar_profundo` quando a pergunta valer o custo 5×.

### E.3 — Gemini grátis como motor

Gemini 3 Flash: **1.500 req/dia grátis, sem cartão** (10 req/min, 250k tok/min).
Atenção: os **Pro viraram pagos em abr/2026** e o 2.0 Flash é deprecado em
01/06/2026 — usar a linha 3.x Flash/Flash-Lite. Endpoint OpenAI-compatível.

- **Encaixe 🟢** — motor de raciocínio/conversa **quase-zero-custo**. Entra na
  cascata como rota nova (`_respond_gemini`, entre OpenAI e OpenRouter), com a
  mesma degradação elegante do `integrations.py` (sem key → pula a rota).
- Bônus: a mesma família tem TTS (Gemini Flash TTS) — dá pra testar voz Google
  grátis também, direto ou via OpenRouter.

### E.4 — SillyTavern (referência, NÃO adoção)

Frontend local multi-backend (OpenRouter, Claude, OpenAI, Mistral, Kobold…) com
extensão de **TTS**, **persona/character cards** e **lorebooks/WorldInfo**. Foco
em roleplay, 300+ contribuidores, sem tracking.

- **Encaixe 🟡** — referência de arquitetura pro **front do Javis**: como trocar
  de backend sem reescrever, como encaixar camada de voz como extensão, como
  modelar persona/memória. Não adotar: Javis é assistente **operacional**, não RP.

### E.5 — Descript / criativo (reservatório do "Estúdio")

Descript: editor de **vídeo/podcast** com IA, **#1 na categoria criativa** do
OpenRouter, 17 modelos, 2 trilhões de tokens desde jun/2025. Ecossistema criativo
do OpenRouter: imagem (**Nano Banana Pro** = Gemini 3 Pro), vídeo (Grok Imagine,
Veo/Sora via MCP).

- **Encaixe ⚪→🟡** — padrão de **roteamento multi-modelo** (modelo barato pra
  rascunho, forte pro acabamento) que serve de molde pro pipeline **Estúdio** mais
  à frente. Nada a plugar agora; lembrar que criativo visual aqui passa por plugin
  Adobe/Canva (regra do projeto), não por geração solta.

### E.6 — Custo-benefício consolidado (voz / inteligência / motor)

| Opção | Voz | Inteligência | Motor (execução) | Esforço | Custo |
|-------|:---:|:---:|:---:|---------|-------|
| **OpenRouter hub** | 🟢 TTS/STT | 🟢 grátis+pagos | 🟡 (tool-use ok) | Baixo (já wired) | Free tier → pago por uso |
| **Gemini grátis** | 🟡 Flash TTS | 🟢 3 Flash | 🟡 | Médio (rota nova) | **Grátis** 1.5k/dia |
| **Fusão** | — | 🟢 (juiz) | ⚪ | Médio | ~5× a chamada |
| **Claude assinatura (atual)** | — | 🟢 | 🟢 melhor | — (default) | Assinatura |
| **SillyTavern** | 🟡 ref. | — | — | Alto (adotar) | Grátis (local) |
| **Descript/criativo** | — | — | — | — | (referência) |

**Ordem recomendada de teste (custo-benefício decrescente):**
1. **Gemini grátis na cascata** — maior ganho/custo: motor de conversa grátis,
   alivia a cota da assinatura nos turnos leves. Rota `_respond_gemini` no padrão
   de fallback existente.
2. **OpenRouter como hub de voz** — testar `/audio/speech` (Grok/Gemini/Voxtral)
   com a key que já existe; comparar com o TTS atual (OpenAI/ElevenLabs).
3. **Teste vivo do site** (precisa do login do Murillo): em openrouter.ai/chat
   rodar o mesmo prompt em 2-3 grátis + Fusão, anotar latência/qualidade.
4. **Estúdio** — só depois, usar Descript/Nano Banana como referência de
   roteamento, respeitando a regra de criativo via plugin.

> **Nota de execução:** Claude (eu) não consigo "testar o chat" interativo sem o
> login/credenciais do Murillo (gasta crédito da conta dele). Posso conduzir o
> teste vivo via browser se ele logar, ou rodar contra a `OPENROUTER_API_KEY` do
> `.env` se ele autorizar.

**Fontes (jun/2026):**
- [OpenRouter — Models](https://openrouter.ai/models) · [Rankings](https://openrouter.ai/rankings) · [Apps](https://openrouter.ai/apps) · [Fusion](https://openrouter.ai/fusion) · [TTS docs](https://openrouter.ai/docs/guides/overview/multimodal/tts)
- [Descript no OpenRouter](https://openrouter.ai/apps/descript) · [SillyTavern (GitHub)](https://github.com/SillyTavern/SillyTavern)
- [OpenRouter Free Models — costgoat (jun/2026)](https://costgoat.com/pricing/openrouter-free-models) · [Most popular models on OpenRouter — officechai](https://officechai.com/miscellaneous/these-are-the-most-popular-ai-models-on-openrouter-june-2026/)
- [Gemini API Free Tier 2026 — TokenMix](https://tokenmix.ai/blog/gemini-api-free-tier-limits) · [Gemini rate limits — Google](https://ai.google.dev/gemini-api/docs/rate-limits)
