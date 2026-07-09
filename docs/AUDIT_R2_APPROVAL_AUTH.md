# Auditoria R2 — Approval persistido, auth local e project_id

Data: 2026-07-09  
Branch: `hardening/r2-approval-auth-projectid`

## Escopo

R2 fecha o ciclo operacional depois da R1:

- substitui `approved=true` fragil por approval persistido;
- adiciona auth local leve para rotas sensiveis;
- faz o frontend enviar `project_id=project:cerebro-jampa` nas chamadas VP/Jampa/WA/tasks/conteudo conectado;
- classifica rotas pendentes sem ligar servidor, agentes, RAG local ou adaptadores externos.

## Approval persistido

Tabela reutilizada: `approvals`.

Campos aditivos:

- `project_id`
- `action`
- `route`
- `risk_level`
- `requested_by`
- `approved_by`
- `approval_token_id`
- `reason`
- `metadata_json`
- `updated_at`

Status aceitos:

- `pending`
- `approved`
- `rejected`
- `expired`
- `canceled`

Contrato:

- rota sensivel sem `approval_id` aprovado retorna `approval_required`;
- `approved=true` legado nao libera execucao;
- `approved=true` apenas cria/consulta gate pendente;
- rota sensivel executa somente quando `approval_id` aponta para approval `approved` compativel com `action`, `route` e `project_id`.

## Auth local

Header:

```text
X-Javes-Local-Token
```

Fontes locais:

```text
JAVES_LOCAL_TOKEN
JAVIS_LOCAL_TOKEN
```

Regras:

- token ausente retorna `blocked` com `reason=unauthorized_local_token_required`;
- token invalido retorna `blocked` com `reason=unauthorized_local_token_invalid`;
- token nao configurado retorna `blocked` com `reason=local_token_not_configured`;
- token nao e logado, impresso ou exposto;
- testes usam token fake em `conftest.py`.

## Frontend project_id

Escopo VP/Jampa:

```text
project:cerebro-jampa
```

Command Center:

- `app.js` exporta `VP_PROJECT_ID`, `withProjectId()` e `withLocalAuth()`;
- `operacao.js` usa `withProjectId()` nas mutacoes de tasks;
- `vempassear.js` usa `vpUrl()` para `/vp/*`, `/jampa/*` e `/conteudo?projeto=vempassear`;
- `conteudo.js` envia `project_id` quando o projeto e `vempassear`;
- `treino.js` envia `project_id` em `/wa/analyze` e `/wa/save-voice`.

Painel legado:

- `frontend/vempassear.js` usa `scopedPath()` para anexar `project_id` em `/vp/*` e `/jampa/*`;
- `authHeaders()` anexa `X-Javes-Local-Token` se houver token em `localStorage`.

## Rotas protegidas

Auth local:

- `POST /knowledge/dna`
- `POST /knowledge/ingest`
- `POST /knowledge/reindex`
- `GET /knowledge/search`
- `POST /knowledge/graph/build`
- `POST /upload`
- `POST /wa/analyze`
- `POST /wa/save-voice`
- mutacoes `POST/PATCH/DELETE /vp/*`
- mutacoes `POST /jampa/*`
- `POST /tasks/{id}/run-studio`
- `POST /tasks/{id}/prepare-distribution`
- `POST /tasks/{id}/status`
- `POST /tasks/{id}/complete`
- `POST /approvals/{id}/decide`
- `GET /history/session`
- `GET /history`
- `DELETE /history`
- `POST /brain/active`
- `POST /missions/{mission_id}/nodes/{node_id}/done`
- `POST /conteudo`

Approval persistido:

- `POST /knowledge/dna`
- `POST /knowledge/ingest`
- `POST /upload`
- `POST /wa/save-voice`

Project scope:

- `POST /tasks/{id}/run-studio`
- `POST /tasks/{id}/prepare-distribution`
- `POST /tasks/{id}/status`
- `POST /tasks/{id}/complete`
- `POST /wa/analyze`
- `POST /wa/save-voice`
- mutacoes `POST/PATCH/DELETE /vp/*`
- mutacoes `POST /jampa/*`
- `POST /conteudo` quando `project=vempassear`

## Rotas revisadas

- `missions/*`: leitura `safe`; mutacao `auth_required + local_actions`.
- `history`: leitura `auth_required`; delete `auth_required + local_actions`.
- `brain/active`: GET `safe`; POST `auth_required + local_actions`.
- `approvals/decide`: `auth_required`; efeitos VP continuam sob `vp_effects`.
- `/conteudo`: GET `safe`; POST `auth_required`; VP/Jampa exige `project_id_required + vp_effects`; demais projetos exigem `local_actions`.

## Continua OFF por padrao

- `external_adapters`
- `local_actions`
- `vp_effects`
- Codex
- Claude headless
- browser automation
- Telegram
- MCP

## Pendencias R3

- RAG project-scoped real por `project_id`.
- UI explicita para cadastrar/rotacionar token local.
- TTL/expiracao formal de approvals.
- Revisao de rotas amplas de chat/voice/agents/train/browser antes de uso operacional.
- Politica de auditoria/log redaction para decisions de approval.
