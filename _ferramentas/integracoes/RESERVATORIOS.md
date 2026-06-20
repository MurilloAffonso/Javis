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
