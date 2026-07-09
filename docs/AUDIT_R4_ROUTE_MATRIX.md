# Auditoria R4 — matriz de rotas

Data: 2026-07-09
Branch: `hardening/r4-route-audit`

## Leitura rápida

- `auth` = exige `X-Javes-Local-Token`
- `project_id` = exige escopo explícito
- `approval` = exige `require_persisted_approval`
- `escape` = ainda sai do contrato de segurança esperado para a família

## Rotas já fechadas pelo contrato

| Rota | Ação | Rede/LLM/Escrita | auth | project_id | approval | escape |
| --- | --- | --- | --- | --- | --- | --- |
| `POST /knowledge/reindex` | reindexar RAG | LLM/embeddings | sim | não | não | não |
| `GET /knowledge/search` | buscar RAG | LLM/embeddings | sim | não | não | não |
| `POST /knowledge/dna` | extrair DNA | rede + escrita | sim | não | sim | não |
| `POST /knowledge/ingest` | ingerir pasta | rede + escrita | sim | path validado | sim | não |
| `POST /knowledge/graph/build` | construir grafo | escrita SQLite | sim | não | não | não |
| `POST /upload` | upload temporário + análise | escrita + LLM/visão | sim | não | sim | não |
| `POST /wa/analyze` | analisar WA | rede/LLM | sim | sim | não | não |
| `POST /wa/save-voice` | salvar grounding | escrita | sim | sim | sim | não |
| `POST /agents/run` | executar agente | LLM/execução | sim | sim | sim | não |
| `POST /browser/run` | browser exec | LLM/execução | sim | sim | sim | não |
| `POST /train/youtube` | treino por YouTube | rede + escrita | sim | sim | sim | não |
| `POST /chat` | conversa core/VP | RAG/brain | sim | sim | não | não |
| `POST /chat/stream` | conversa SSE | RAG/brain | sim | sim | não | não |
| `POST /voice` | voz | LLM/voz | sim | sim | não | não |
| `POST /voice/stream` | voz SSE | LLM/voz | sim | sim | não | não |
| `POST /tasks/{id}/run-studio` | studio | local template | sim | sim | não | não |
| `POST /tasks/{id}/prepare-distribution` | distribution | local template | sim | sim | não | não |
| `POST /tasks/{id}/status` | status task | escrita SQLite | sim | sim | não | não |
| `POST /tasks/{id}/complete` | concluir task | escrita SQLite | sim | sim | não | não |
| `POST /approvals/{approval_id}/decide` | decidir gate | escrita SQLite | sim | não | não | não |
| `DELETE /history` | limpar histórico | escrita local | sim | não | não | não |
| `GET /history` | ler histórico | leitura local | sim | não | não | não |
| `GET /history/session` | ler sessão | leitura local | sim | não | não | não |
| `POST /brain/active` | trocar motor | escrita local | sim | não | não | não |
| `POST /missions/{mission_id}/nodes/{node_id}/done` | concluir node | escrita local | sim | não | não | não |

## Rotas em contrato, mas com fronteira explícita por projeto

| Rota | Ação | Rede/LLM/Escrita | auth | project_id | approval | escape |
| --- | --- | --- | --- | --- | --- | --- |
| `POST /vp/passeios` | mutação VP | escrita local | sim | sim | não | não |
| `DELETE /vp/passeios/{item_id}` | mutação VP | escrita local | sim | sim | não | não |
| `POST /vp/clientes` | mutação VP | escrita local | sim | sim | não | não |
| `PATCH /vp/clientes/{item_id}` | mutação VP | escrita local | sim | sim | não | não |
| `DELETE /vp/clientes/{item_id}` | mutação VP | escrita local | sim | sim | não | não |
| `POST /vp/conteudo` | mutação VP | escrita local | sim | sim | não | não |
| `POST /vp/conteudos` | mutação VP | escrita local | sim | sim | não | não |
| `DELETE /vp/conteudos/{item_id}` | mutação VP | escrita local | sim | sim | não | não |
| `POST /vp/pauta` | mutação VP | escrita local | sim | sim | não | não |
| `PATCH /vp/pauta/{item_id}` | mutação VP | escrita local | sim | sim | não | não |
| `DELETE /vp/pauta/{item_id}` | mutação VP | escrita local | sim | sim | não | não |
| `POST /jampa/squad` | mutação Jampa | escrita/saída local | sim | sim | não | não |
| `POST /jampa/responder-lead` | mutação Jampa | escrita/saída local | sim | sim | não | não |
| `POST /jampa/forjar-skill` | mutação Jampa | escrita + ferramenta externa | sim | sim | não | não |
| `POST /vp/agents/run` | execução VP | LLM/execução | sim | sim | não | não |
| `GET /ui/squads/{project_id}` | UI escopada | leitura | não | sim | não | não |
| `GET /ui/project/{project_id}` | UI escopada | leitura | não | sim | não | não |

## Rotas que ainda escapam ou pedem revisão

| Rota | Ação | Rede/LLM/Escrita | auth | project_id | approval | escape |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /approvals/pending` | listar aprovações | leitura SQLite | não | não | não | sim |
| `GET /brain/active` | ler motor ativo | leitura local | não | não | não | sim |
| `GET /profile` | ler perfil | leitura local | não | não | não | sim |
| `GET /integrations` | ler integrações | leitura local | não | não | não | sim |
| `GET /status` | status serviços | inspeção local | não | não | não | sim |
| `GET /exec/status` | status exec | leitura local | não | não | não | sim |
| `GET /stats` | contadores | leitura SQLite | não | não | não | sim |
| `GET /reminders/poll` | lembretes | leitura local | não | não | não | sim |
| `GET /reminders` | lembretes | leitura local | não | não | não | sim |
| `GET /knowledge/eval` | avaliar RAG | leitura/avaliação | não | não | não | sim |
| `GET /knowledge/graph` | consultar grafo | leitura SQLite | não | não | não | sim |
| `GET /knowledge/ingest/status` | status ingest | leitura local | não | não | não | sim |
| `GET /projects/registry` | registry | leitura local | não | não | não | sim |
| `GET /agents` | catálogo agentes | leitura local | não | não | não | sim |
| `GET /vp/agents` | catálogo VP | leitura local | não | não | não | sim |
| `GET /missions` | listar missões | leitura local | não | não | não | sim |
| `GET /missions/{mission_id}/nodes` | listar nodes | leitura local | não | não | não | sim |
| `GET /v1/models` | compat OpenAI | leitura local | não | não | não | sim |
| `GET /ui/state` | estado UI | leitura local | não | não | não | sim |
| `GET /ui/projects` | estado UI | leitura local | não | não | não | sim |
| `GET /ui/agents` | estado UI | leitura local | não | não | não | sim |
| `GET /ui/skills` | estado UI | leitura local | não | não | não | sim |
| `GET /ui/scripts` | estado UI | leitura local | não | não | não | sim |
| `GET /ui/mcp` | estado UI | leitura local | não | não | não | sim |
| `GET /mcp/{server_id}/tools` | estado MCP | leitura local | não | não | não | sim |
| `POST /mcp/{server_id}/call` | chamada MCP | ferramenta externa | não | não | não | sim |
| `GET /ui/integrations` | estado UI | leitura local | não | não | não | sim |
| `GET /ui/telemetry` | telemetria | leitura local | não | não | não | sim |
| `GET /conteudo` | listar conteúdo | leitura SQLite | não | não | não | sim |
| `GET /vp/passeios` | listar VP | leitura SQLite | não | não | não | sim |
| `GET /vp/clientes` | listar VP | leitura SQLite | não | não | não | sim |
| `GET /vp/conteudos` | listar VP | leitura SQLite | não | não | não | sim |
| `GET /vp/pauta` | listar VP | leitura SQLite | não | não | não | sim |
| `GET /jampa/agents` | listar Jampa | leitura local | não | não | não | sim |

## Observação final

- O contrato de mutação ficou fechado nas rotas sensíveis.
- O que ainda escapa é majoritariamente leitura/telemetria/listagem.
- As únicas rotas de leitura que merecem revisão adicional são as que expõem estado operacional sem auth: `approvals/pending`, `brain/active`, `stats`, `status`, `exec/status`, e as listagens de project data (`/conteudo`, `/vp/*`, `/jampa/agents`).

