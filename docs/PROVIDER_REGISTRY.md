# Provider Registry — Javes

Data: 2026-07-09

## Objetivo

Centralizar providers do Javes como dados auditáveis, sem expor chaves e sem criar outro runtime.

## Providers registrados

| id | tipo | uso |
|---|---|---|
| `ollama` | local | chat local e embeddings locais |
| `gemini` | cloud | chat/tool-use externo opcional |
| `claude` | cloud | Claude assinatura/API, opcional e protegido por flags |
| `openai` | cloud | chat/tool-use e embeddings externos opcionais |
| `openrouter` | cloud | fallback cloud opcional |

`configured` significa apenas que a configuração necessária parece existir. O valor da credencial nunca é exibido.

## Modos

- `local`: seleciona somente `ollama`; não considera providers cloud.
- `cloud`: seleciona somente providers cloud habilitados, configurados e fora de cooldown.
- `auto`: tenta `ollama` primeiro; depois usa cloud apenas se `JAVIS_ENABLE_EXTERNAL_ADAPTERS=true` e o provider estiver saudável.

## Classificação de erros

- `authentication_error`: HTTP 401/403.
- `rate_limited`: HTTP 429, respeitando `Retry-After` quando disponível.
- `billing_error`: crédito, billing, quota ou pagamento.
- `timeout`: timeout explícito.
- `unavailable`: conexão/serviço indisponível.
- `invalid_request`: 400/404/409/422 ou request inválido.
- `model_not_found`: modelo ausente/inexistente.
- `unknown_error`: fallback seguro.

Erros internos, como `project_id` indefinido, não entram como falha de provider.

## Cooldown

O estado fica em `_apps/javis-local-interface/_data/provider_health.json`, sem segredos.

- auth/billing: cooldown longo, para evitar retentativa em toda mensagem.
- 429: usa `Retry-After` ou 5 minutos.
- timeout: cooldown curto.
- indisponibilidade/modelo inválido: cooldown intermediário.
- sucesso limpa o estado transitório.

Providers em cooldown são pulados pelo roteador.

## Doctor

Executar sem servidor:

```powershell
python scripts/javes_doctor.py --no-probe
python scripts/javes_doctor.py --json --no-probe
python scripts/javes_doctor.py --verbose --no-probe
```

Sem `--no-probe`, o doctor pode testar apenas a porta local do Ollama. Ele não chama Gemini, OpenAI, Claude nem OpenRouter.

O relatório mostra flags, provider mode, RAG embedder, providers registrados, health/cooldown, `CURRENT_STATE.md`, índice RAG e aprovações pendentes sem imprimir tokens, chaves ou credenciais.
