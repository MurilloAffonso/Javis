# Sessões e escopo por project_id

R3 isola conversa, histórico, memória operacional e consultas por `project_id`.

## Identificadores

- `project_id`: escopo operacional obrigatório para projetos conectados.
- `javes-core`: escopo padrão seguro do núcleo.
- `project:cerebro-jampa`: escopo explícito para Cérebro/Vem Passear Jampa.
- `session_id`: conversa específica dentro de exatamente um `project_id`.

## Regras

- Toda sessão pertence a um único `project_id`.
- `session_id` de outro projeto retorna `blocked/project_scope_mismatch`.
- `session_id` inexistente retorna `not_found/session_not_found`.
- Chamadas antigas sem `project_id` usam `javes-core`.
- Histórico legado global é tratado como legado de `javes-core/default`; não é apagado.

## Histórico

`_apps/javis-local-interface/backend/history_store.py` grava sessões em SQLite:

- `chat_sessions(session_id, project_id, title, status, metadata_json, created_at, updated_at)`.
- `messages(project_id, session_id, role, content, brain, intent, source, created_at)`.

APIs internas:

- `load(project_id, session_id)`.
- `append(project_id, session_id, message)`.
- `clear(project_id, session_id)`.
- `list_sessions(project_id)`.
- `archive_session(project_id, session_id)`.

## Chat

`/chat` e `/chat/stream` normalizam `project_id` e `session_id` antes de chamar o agente.

- Sem `project_id`: usa `javes-core`.
- Sem `session_id`: usa/cria `default` no projeto atual.
- Com `session_id`: valida se pertence ao `project_id`.
- O system/contexto recebe apenas histórico da sessão/projeto correto.

## RAG e memória

- `javes-core` busca somente categorias `pessoal` e `projeto`.
- `project:cerebro-jampa` busca somente categoria `vp`.
- `CURRENT_STATE.md` é categoria `projeto`, portanto pertence ao núcleo.
- Categoria não substitui `project_id`; o escopo vem do projeto normalizado.

## Tasks e approvals

- Tasks e approvals têm filtros por `project_id`.
- Registros antigos sem `project_id` são tratados como `javes-core` em leituras escopadas.
- Um projeto não deve consultar tasks/approvals de outro escopo quando `project_id` é informado.

## Frontend

O Command Center envia:

- `project_id` calculado por agente/projeto.
- `session_id` separado por `project_id::agent_id`.

O núcleo usa `javes-core`; agentes de Vem Passear/Jampa usam `project:cerebro-jampa`.

## Doctor

`python scripts/javes_doctor.py --no-probe` mostra:

- total de sessões;
- sessões de `javes-core`;
- sessões por projeto;
- histórico legado encontrado;
- inconsistências de sessão/projeto.

O doctor não imprime mensagens do histórico.
