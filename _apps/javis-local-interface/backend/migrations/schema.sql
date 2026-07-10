-- Javis — schema SQLite (camada de persistência ADITIVA).
-- Não substitui JSON/Markdown: roda lado a lado (dual-write).
-- Tudo IF NOT EXISTS → seguro de rodar várias vezes (idempotente).

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT DEFAULT 'active',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agents (
    id               TEXT PRIMARY KEY,           -- ex.: 'nova', 'architect'
    name             TEXT NOT NULL,
    role             TEXT,
    squad            TEXT,                        -- 'mente' | 'vp' | ...
    contract_input   TEXT,
    contract_output  TEXT,
    contract_naofaz  TEXT,
    created_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workflows (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    slug         TEXT UNIQUE,
    name         TEXT NOT NULL,
    project_slug TEXT,
    status       TEXT DEFAULT 'active',
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ext_id       TEXT UNIQUE,                     -- id do mission_board (node id)
    mission      TEXT,                            -- slug da missão
    title        TEXT NOT NULL,
    status       TEXT DEFAULT 'pending',          -- pending | running | done | gate_approved | completed | killed
    source       TEXT DEFAULT 'backlog',          -- backlog | chat | flow
    agent        TEXT,                            -- agente/dono, se houver
    project_id   TEXT,                            -- projeto (slug), se houver
    completed_at TEXT,                            -- quando foi concluída
    killed_at    TEXT,                            -- quando a entidade "morreu"
    digest_text  TEXT,                            -- resumo final (AI Digest)
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL,                     -- user | assistant
    content    TEXT,
    brain      TEXT,
    intent     TEXT,
    source     TEXT DEFAULT 'chat',               -- chat | voice
    project_id TEXT DEFAULT 'javes-core',
    session_id TEXT DEFAULT 'default',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id    TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL,
    title         TEXT,
    status        TEXT DEFAULT 'active',
    metadata_json TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS approvals (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT,                              -- 'gate' | 'acao' ...
    subject    TEXT NOT NULL,                     -- o que precisa aprovar
    agent      TEXT,
    task_id    TEXT,                              -- task relacionada (ext_id), se houver
    project_id TEXT,
    action     TEXT,
    route      TEXT,
    risk_level TEXT,
    status     TEXT DEFAULT 'pending',            -- pending | approved | rejected | expired | canceled
    detail     TEXT,
    note       TEXT,                              -- observação da decisão humana
    requested_by TEXT,
    approved_by TEXT,
    approval_token_id TEXT,
    consumed_at TEXT,
    reason     TEXT,
    metadata_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    decided_at TEXT
);

CREATE TABLE IF NOT EXISTS action_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source     TEXT,
    intent     TEXT,
    agent      TEXT,
    message    TEXT,
    status     TEXT,
    approved   INTEGER,                           -- NULL | 0 | 1
    latency_ms INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT,
    content    TEXT,
    kind       TEXT,                              -- 'fato' | 'decisao' ...
    created_at TEXT DEFAULT (datetime('now'))
);

-- Estúdio de Conteúdo: posts/rascunhos criados no Command Center.
CREATE TABLE IF NOT EXISTS content (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project    TEXT,                              -- 'vempassear' | 'javes'
    channel    TEXT,                              -- 'instagram' | 'blog' | ...
    title      TEXT,
    body       TEXT,
    status     TEXT DEFAULT 'rascunho',           -- 'rascunho' | 'agendado' | 'publicado'
    created_at TEXT DEFAULT (datetime('now'))
);

-- Journey Log: cada tarefa vira uma entidade com timeline de eventos
-- (nascimento → eventos → checkpoints → aprovação → avanço → conclusão).
CREATE TABLE IF NOT EXISTS task_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id       TEXT NOT NULL,                  -- ext_id da task (ou slug do fluxo)
    event_type    TEXT NOT NULL,                  -- task_created | agent_called | ...
    actor         TEXT,                           -- 'system' | 'murillo' | 'agent'
    agent_id      TEXT,                           -- agente envolvido, se houver
    message       TEXT,
    metadata_json TEXT,                           -- JSON livre (contexto extra)
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_project_session ON messages(project_id, session_id, id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project ON chat_sessions(project_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status     ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_logs_created     ON action_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_task_events_task ON task_events(task_id, id);

-- === RAG híbrido (SQLite-nativo): vetores + FTS5/BM25 =====================
-- Aditivo: não substitui _memoria/knowledge_index.json. knowledge_hybrid.py
-- guarda os chunks aqui (vetor em BLOB float32) e cruza busca semântica
-- (cosine numpy) com busca por palavra-chave (FTS5/BM25) via RRF.
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT NOT NULL,
    mtime       REAL,
    chunk_index INTEGER,
    content     TEXT NOT NULL,
    vec         BLOB,                              -- numpy float32 bytes (NULL = só BM25)
    dim         INTEGER,
    categoria   TEXT,                              -- escopo determinístico: pessoal | projeto | vp (categoria.py)
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_kchunks_path ON knowledge_chunks(path);

-- Índice de texto completo (external content ligado a knowledge_chunks).
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    content,
    content='knowledge_chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

-- Triggers mantêm o FTS em sincronia com a tabela de chunks.
CREATE TRIGGER IF NOT EXISTS knowledge_chunks_ai AFTER INSERT ON knowledge_chunks BEGIN
    INSERT INTO knowledge_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS knowledge_chunks_ad AFTER DELETE ON knowledge_chunks BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS knowledge_chunks_au AFTER UPDATE ON knowledge_chunks BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, content) VALUES ('delete', old.id, old.content);
    INSERT INTO knowledge_fts(rowid, content) VALUES (new.id, new.content);
END;

-- === Knowledge graph: conceitos ligados entre os dossiês de DNA ============
-- Nós = conceitos (uma "ideia" de alguma dimensão do DNA). Arestas = co-ocorrência
-- no mesmo dossiê (não-direcionadas, guardadas com src<dst). Reconstruído por
-- knowledge_graph.build_from_dna() a partir de _memoria/dna/*.json.
CREATE TABLE IF NOT EXISTS kg_nodes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT UNIQUE NOT NULL,     -- slug normalizado (identidade do conceito)
    label      TEXT NOT NULL,            -- texto original (primeiro visto)
    type       TEXT,                     -- dimensão de origem (frameworks, voz_tom, ...)
    mentions   INTEGER DEFAULT 0,        -- em quantos dossiês aparece
    sources    TEXT,                     -- JSON: nomes dos dossiês (capado)
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS kg_edges (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    src    INTEGER NOT NULL,
    dst    INTEGER NOT NULL,
    rel    TEXT DEFAULT 'co_ocorre',
    weight INTEGER DEFAULT 1,
    UNIQUE(src, dst, rel)
);
CREATE INDEX IF NOT EXISTS idx_kg_edges_src ON kg_edges(src);
CREATE INDEX IF NOT EXISTS idx_kg_edges_dst ON kg_edges(dst);
