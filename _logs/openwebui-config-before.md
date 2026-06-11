# Open WebUI — Estado Antes da Configuração

**Data/hora:** 2026-06-10

## Infraestrutura

- Docker container: `javis-open-webui` (ghcr.io/open-webui/open-webui:main)
- Status: Up, healthy, porta 3000->8080
- Ollama: rodando, acessível em http://host.docker.internal:11434

## Modelos Ollama disponíveis

- `llama3.2:3b` (2.0 GB) — modelo base escolhido para o Javis
- `phi3:mini` (2.2 GB)

## Arquivos de prompt encontrados antes da configuração

- `_prompts/system-openwebui-javis.md` — prompt geral único existente
- Pasta `_prompts/modelos-openwebui/` — NÃO existia (criada nesta sessão)

## Modelos no Open WebUI (antes)

- Não foi possível verificar via API sem autenticação.
- Estado visual a ser confirmado via interface após login de Murillo.

## API OpenAI

- Estado desconhecido antes do acesso à interface — verificar após login.

## Observações

- O Javis existente estava gerando blocos "Acompanhamento" indesejados.
- O Javis existente estava gerando perguntas extras não solicitadas.
- Objetivo desta sessão: criar 6 modelos especializados com prompts disciplinados.
- Nenhuma alteração foi feita no banco de dados do Open WebUI.
- Nenhuma alteração foi feita nos arquivos de open-webui-data/.
