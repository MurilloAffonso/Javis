# Open WebUI — Setup

Data: 2026-06-10

## O que foi feito

- docker-compose.yml criado na raiz do projeto
- Pasta open-webui-data/ criada para persistência
- docker compose up -d executado com sucesso (exit code 0)
- Imagem baixada: ghcr.io/open-webui/open-webui:main (v0.9.6)

## Configuração

```yaml
Container: javis-open-webui
Porta: 3000 (host) -> 8080 (container)
Ollama: http://host.docker.internal:11434
Nome: Javis
Dados: ./open-webui-data:/app/backend/data
```

## Status do Startup

1. Banco SQLite inicializado (migrations completas) ✅
2. Baixando embedding model do HuggingFace (30 arquivos) — lento sem HF_TOKEN ⏳
   - Modelo: sentence-transformers/all-MiniLM-L6-v2
   - ~90 MB total, download em bursts com rate limiting
   - Padrão: burst ~10MB/s, pausa, reinicia
   - Progresso: 7/14 arquivos completos na hora do registro
3. Uvicorn server: inicia APÓS download completo do embedding model

## Aviso ao retomar

Se o download do HF Hub travar, pode ser necessário adicionar HF_TOKEN:

```yaml
environment:
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
  - WEBUI_NAME=Javis
  - HF_TOKEN=<seu_token>  # opcional, aumenta rate limit
```

Ou desabilitar embedding:
```yaml
  - RAG_EMBEDDING_ENGINE=ollama
  - RAG_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## Acesso

- Local: http://localhost:3000
- Celular (mesma rede): http://<IP-da-maquina>:3000
  Obter IP: `ipconfig | findstr IPv4`

## Comandos do dia a dia

```bash
docker compose up -d        # iniciar
docker compose down         # parar
docker compose ps           # status
docker compose logs -f open-webui  # logs ao vivo
docker compose pull && docker compose up -d  # atualizar
```
