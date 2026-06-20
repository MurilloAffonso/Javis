"""repositories.py — acesso aos dados do SQLite, um repositório por entidade.

Entidades: messages, tasks, approvals, logs (action_logs), agents, projects,
workflows, memories. Cada um expõe add/list/get simples. É a fachada que o resto
do backend usa — ninguém escreve SQL solto fora daqui.

Tudo tolerante a falha: se o banco der erro, o chamador (dual-write) não quebra —
os arquivos JSON/Markdown seguem como fonte viva.
"""
from __future__ import annotations
import db


# ── messages ──────────────────────────────────────────────────────────────
class _Messages:
    def add(self, role: str, content: str, brain: str = "", intent: str = "", source: str = "chat") -> int:
        return db.execute(
            "INSERT INTO messages(role, content, brain, intent, source) VALUES(?,?,?,?,?)",
            (role, content, brain, intent, source),
        )

    def recent(self, limit: int = 50) -> list[dict]:
        return db.query("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,))

    def count(self) -> int:
        return db.count("messages")


# ── tasks ─────────────────────────────────────────────────────────────────
class _Tasks:
    def upsert(self, ext_id: str, title: str, status: str = "pending",
               mission: str = "", source: str = "backlog") -> int:
        """Insere ou atualiza por ext_id (id do mission_board) — mantém o Quadro espelhado."""
        return db.execute(
            "INSERT INTO tasks(ext_id, mission, title, status, source) VALUES(?,?,?,?,?) "
            "ON CONFLICT(ext_id) DO UPDATE SET status=excluded.status, "
            "title=excluded.title, mission=excluded.mission, updated_at=datetime('now')",
            (ext_id, mission, title, status, source),
        )

    def set_status(self, ext_id: str, status: str) -> int:
        return db.execute(
            "UPDATE tasks SET status=?, updated_at=datetime('now') WHERE ext_id=?",
            (status, ext_id),
        )

    def list(self, status: str = "") -> list[dict]:
        if status:
            return db.query("SELECT * FROM tasks WHERE status=? ORDER BY id", (status,))
        return db.query("SELECT * FROM tasks ORDER BY id")

    def count(self, status: str = "") -> int:
        return db.count("tasks", "status=?", (status,)) if status else db.count("tasks")


# ── approvals ─────────────────────────────────────────────────────────────
class _Approvals:
    def add(self, subject: str, kind: str = "gate", agent: str = "", detail: str = "") -> int:
        return db.execute(
            "INSERT INTO approvals(kind, subject, agent, status, detail) VALUES(?,?,?,'pending',?)",
            (kind, subject, agent, detail),
        )

    def decide(self, approval_id: int, approved: bool) -> int:
        return db.execute(
            "UPDATE approvals SET status=?, decided_at=datetime('now') WHERE id=?",
            ("approved" if approved else "rejected", approval_id),
        )

    def pending(self) -> list[dict]:
        return db.query("SELECT * FROM approvals WHERE status='pending' ORDER BY id DESC")

    def count_pending(self) -> int:
        return db.count("approvals", "status='pending'")


# ── logs (action_logs) ────────────────────────────────────────────────────
class _Logs:
    def add(self, source: str, intent: str, message: str, status: str,
            agent: str = "", approved=None, latency_ms: int = 0) -> int:
        ap = None if approved is None else (1 if approved else 0)
        return db.execute(
            "INSERT INTO action_logs(source, intent, agent, message, status, approved, latency_ms) "
            "VALUES(?,?,?,?,?,?,?)",
            (source, intent, agent, message, status, ap, latency_ms),
        )

    def recent(self, limit: int = 50) -> list[dict]:
        return db.query("SELECT * FROM action_logs ORDER BY id DESC LIMIT ?", (limit,))

    def count(self) -> int:
        return db.count("action_logs")


# ── agents ────────────────────────────────────────────────────────────────
class _Agents:
    def upsert(self, agent_id: str, name: str, role: str = "", squad: str = "",
               input: str = "", output: str = "", naofaz: str = "") -> int:
        return db.execute(
            "INSERT INTO agents(id, name, role, squad, contract_input, contract_output, contract_naofaz) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
            "role=excluded.role, squad=excluded.squad, contract_input=excluded.contract_input, "
            "contract_output=excluded.contract_output, contract_naofaz=excluded.contract_naofaz",
            (agent_id, name, role, squad, input, output, naofaz),
        )

    def list(self, squad: str = "") -> list[dict]:
        if squad:
            return db.query("SELECT * FROM agents WHERE squad=? ORDER BY id", (squad,))
        return db.query("SELECT * FROM agents ORDER BY id")

    def count(self) -> int:
        return db.count("agents")


# ── projects ──────────────────────────────────────────────────────────────
class _Projects:
    def upsert(self, slug: str, name: str, description: str = "", status: str = "active") -> int:
        return db.execute(
            "INSERT INTO projects(slug, name, description, status) VALUES(?,?,?,?) "
            "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, "
            "description=excluded.description, status=excluded.status",
            (slug, name, description, status),
        )

    def list(self) -> list[dict]:
        return db.query("SELECT * FROM projects ORDER BY id")

    def count(self) -> int:
        return db.count("projects")


# ── workflows ─────────────────────────────────────────────────────────────
class _Workflows:
    def upsert(self, slug: str, name: str, project_slug: str = "", status: str = "active") -> int:
        return db.execute(
            "INSERT INTO workflows(slug, name, project_slug, status) VALUES(?,?,?,?) "
            "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, "
            "project_slug=excluded.project_slug, status=excluded.status",
            (slug, name, project_slug, status),
        )

    def list(self) -> list[dict]:
        return db.query("SELECT * FROM workflows ORDER BY id")

    def count(self) -> int:
        return db.count("workflows")


# ── memories ──────────────────────────────────────────────────────────────
class _Memories:
    def add(self, content: str, key: str = "", kind: str = "fato") -> int:
        return db.execute(
            "INSERT INTO memories(key, content, kind) VALUES(?,?,?)", (key, content, kind)
        )

    def list(self, limit: int = 100) -> list[dict]:
        return db.query("SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,))

    def count(self) -> int:
        return db.count("memories")


# instâncias prontas pra uso
messages  = _Messages()
tasks     = _Tasks()
approvals = _Approvals()
logs      = _Logs()
agents    = _Agents()
projects  = _Projects()
workflows = _Workflows()
memories  = _Memories()
