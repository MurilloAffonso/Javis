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
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ext_id     TEXT UNIQUE,                       -- id do mission_board (node id)
    mission    TEXT,                              -- slug da missão
    title      TEXT NOT NULL,
    status     TEXT DEFAULT 'pending',            -- pending | running | done
    source     TEXT DEFAULT 'backlog',            -- backlog | chat | flow
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL,                     -- user | assistant
    content    TEXT,
    brain      TEXT,
    intent     TEXT,
    source     TEXT DEFAULT 'chat',               -- chat | voice
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS approvals (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT,                              -- 'gate' | 'acao' ...
    subject    TEXT NOT NULL,                     -- o que precisa aprovar
    agent      TEXT,
    task_id    TEXT,                              -- task relacionada (ext_id), se houver
    status     TEXT DEFAULT 'pending',            -- pending | approved | rejected
    detail     TEXT,
    note       TEXT,                              -- observação da decisão humana
    created_at TEXT DEFAULT (datetime('now')),
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

CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status     ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_logs_created     ON action_logs(created_at);
