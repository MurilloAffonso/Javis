# Open Notebook — substituto local do Google NotebookLM

Console de estudo: indexa PDFs, vídeos, áudio e páginas web; gera resumos com
citations e podcasts a partir das fontes. Roda **lado a lado** com o Javis —
não está integrado ao chat. O fluxo é:

```
Material bruto
   │  (PDF, vídeo, MP3, link)
   ▼
Open Notebook (localhost:8502)
   │  resume / gera podcast / responde com citation
   ▼
Resumo .md exportado p/ _treinamento/<area>/_resumos/
   │
   ▼
knowledge.py do Javis indexa o resumo no RAG → "buscar_conhecimento"
```

## Portas usadas

| Serviço            | Host (sua máquina) | Container |
|--------------------|--------------------|-----------|
| Javis              | 8000               | —         |
| Open WebUI         | 3000               | —         |
| Ollama             | 11434              | —         |
| **SurrealDB**      | **8400**           | 8000      |
| **Open Notebook UI** | **8502**         | 8502      |
| **Open Notebook API** | **5055**        | 5055      |

> A porta padrão do SurrealDB no compose oficial era 8000 — remapeada pra 8400
> aqui pra não conflitar com o servidor do Javis.

## Antes de subir (1 minuto)

1. **Gerar a chave de criptografia** (substituir `TROCAR-ANTES-DE-USAR-EM-SERIO-32-chars-min` no `docker-compose.yml`):
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. **Confirmar que Ollama tá rodando** (`http://localhost:11434/api/tags`).

## Subir / derrubar

```powershell
cd _ferramentas/integracoes/open-notebook

# Subir (puxa as imagens da 1ª vez — ~1-2 GB de download)
docker compose up -d

# Logs
docker compose logs -f open_notebook

# Status
docker compose ps

# Derrubar (mantém volumes)
docker compose down

# Limpar TUDO (apaga banco + fontes carregadas — irreversível)
docker compose down -v
```

Acesse: **http://localhost:8502**

## Configuração mínima após subir

1. Abrir `http://localhost:8502`.
2. **Settings → Models → Add provider:**
   - Provider: **Ollama**
   - Base URL: `http://host.docker.internal:11434`
   - Salvar.
3. Adicionar um modelo de chat (ex.: `llama3.2:3b`) e um de embeddings (ex.: `nomic-embed-text` — pode ser preciso `ollama pull nomic-embed-text` antes).
4. (Opcional) Adicionar provedor OpenAI/Anthropic com a key do `.env` do Javis se quiser qualidade maior nos resumos — gasta crédito da API.

## Plano de teste (1 hora)

1. Subir o compose.
2. Configurar Ollama no painel.
3. Carregar **2-3 fontes** do `_treinamento/conteudo/_entrada/` (1 vídeo, 1 PDF, 1 artigo).
4. Gerar 1 **resumo** + 1 **podcast**.
5. Comparar com o que o Google NotebookLM faria.
6. Se aprovar:
   - Exportar o resumo em `.md` → salvar em `_treinamento/conteudo/_resumos/`.
   - `knowledge.py` indexa no próximo restart do Javis (ou chamar `/knowledge/reindex`).
7. Se reprovar: `docker compose down -v` e desinstala — nenhum acoplamento criado.

## O que NÃO está integrado (decisão consciente)

- **Sem MCP / sem tool no chat do Javis.** O Open Notebook é console interativo.
- **Sem auto-pull do `_treinamento/_entrada/`.** Você decide manualmente o que vira fonte de estudo.
- **Sem RAG compartilhado.** O RAG do Open Notebook fica lá dentro; o RAG do
  Javis (`knowledge.py`) continua sobre os `.md`. Eles só se cruzam quando o
  resumo final é exportado pra `_treinamento/_resumos/`.

## Pastas geradas (já no `.gitignore` do diretório)

- `surreal_data/` — banco do SurrealDB.
- `notebook_data/` — dados do Open Notebook (fontes carregadas, etc.).

Ambas locais — nada vai pro git.
