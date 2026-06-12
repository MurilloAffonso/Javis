# Integrações de API — Jamba

Guia das APIs que o Jamba pode usar. Cada uma é **opcional**: sem a key, o Jamba usa um fallback. Coloque as keys no arquivo `.env` na raiz do projeto.

---

## ✅ Já integrado

### YouTube Data API v3 — tocar a música exata
- **O que dá:** falar "toca [música]" e o Jamba abre o vídeo certo já tocando (não a página de busca).
- **Como pegar a key:**
  1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
  2. Crie um projeto (ou use um existente)
  3. Menu → **APIs e serviços** → **Biblioteca** → busque **YouTube Data API v3** → **Ativar**
  4. **Credenciais** → **Criar credencial** → **Chave de API** → copie
- **Onde colar:** `.env` → `YOUTUBE_API_KEY=...`
- **Custo:** grátis (cota diária de 10.000 unidades ≈ 100 buscas/dia)

---

## 🟡 Estrutura pronta (falta só ativar)

### Google Custom Search — buscar na web
- **O que dá:** o Jamba pesquisar no Google e trazer resultados.
- **Key:** [console.cloud.google.com](https://console.cloud.google.com) → ative **Custom Search API** → crie key.
- **CSE ID:** [programmablesearchengine.google.com](https://programmablesearchengine.google.com) → crie um mecanismo → copie o ID.
- **`.env`:** `GOOGLE_API_KEY=...` e `GOOGLE_CSE_ID=...`
- **Custo:** grátis até 100 buscas/dia.

### Spotify — tocar música no player do Spotify
- **O que dá:** tocar direto no Spotify (precisa Premium para controle de playback).
- **Key:** [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) → criar app → copie Client ID e Secret.
- **`.env`:** `SPOTIFY_CLIENT_ID=...` e `SPOTIFY_CLIENT_SECRET=...`
- **Obs:** requer fluxo OAuth (login uma vez). Implementação futura.

### Canva Connect API — criar designs
- **O que dá:** gerar/exportar designs no Canva por comando.
- **Key:** [canva.dev](https://www.canva.dev) → Canva Connect → criar integração (requer aprovação do app).
- **`.env`:** `CANVA_API_KEY=...`
- **Obs:** OAuth + aprovação da Canva. Mais burocrático. Implementação futura.

---

## 💡 Ideias para o futuro (ainda não estruturadas)

| API | O que desbloqueia | Dificuldade |
|-----|-------------------|-------------|
| Notion | Ler/escrever notas e bancos de dados | Fácil (token) |
| Gmail / Google Calendar | Ler e-mails, agendar eventos | Média (OAuth) |
| WhatsApp (Cloud API) | Enviar/receber mensagens | Média |
| OpenWeather | Clima por voz | Fácil (key) |
| Telegram Bot | Controlar o Jamba pelo celular | Fácil (token) |
| ElevenLabs | Voz ainda mais humana e clonada | Fácil (key) |

---

## Como o Jamba decide usar

No código (`backend/integrations.py`), a função `available()` diz quais APIs têm key configurada. Cada ação tenta a API primeiro e, se não houver key, cai no fallback. Assim você pluga as keys aos poucos, sem quebrar nada.
