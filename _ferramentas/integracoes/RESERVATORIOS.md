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

## Como decidir tecnicamente

`backend/integrations.py` já tem `available()` que detecta quais keys existem no `.env`. Conforme você for plugando, cada ação tenta a API e cai no fallback se não houver key — então dá pra crescer aos poucos sem quebrar nada.

**Fontes da pesquisa:**
- [public-apis/public-apis (GitHub)](https://github.com/public-apis/public-apis)
- [20 Most Popular APIs 2026 (API League)](https://apileague.com/articles/most-popular-apis/)
- [Best Free AI APIs 2026](https://crazyburst.com/best-free-ai-apis-2026/)
- [rezaulhreza/jarvis](https://github.com/rezaulhreza/jarvis) · [Srijan-D/Jarvis](https://github.com/Srijan-D/Jarvis-AI-Assistant) · [isair/jarvis](https://github.com/isair/jarvis) · [OpenJarvis](https://github.com/open-jarvis/OpenJarvis)
