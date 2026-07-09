"""repositories.py — acesso aos dados do SQLite, um repositório por entidade.

Entidades: messages, tasks, approvals, logs (action_logs), agents, projects,
workflows, memories. Cada um expõe add/list/get simples. É a fachada que o resto
do backend usa — ninguém escreve SQL solto fora daqui.

Tudo tolerante a falha: se o banco der erro, o chamador (dual-write) não quebra —
os arquivos JSON/Markdown seguem como fonte viva.
"""
from __future__ import annotations
import json as _json
from datetime import datetime, timedelta, timezone
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
               mission: str = "", source: str = "backlog",
               agent: str | None = None, project_id: str | None = None) -> int:
        """Insere ou atualiza por ext_id (id do mission_board) — mantém o Quadro espelhado.
        agent/project_id só são sobrescritos se vierem (COALESCE preserva o existente)."""
        return db.execute(
            "INSERT INTO tasks(ext_id, mission, title, status, source, agent, project_id) "
            "VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(ext_id) DO UPDATE SET status=excluded.status, "
            "title=excluded.title, mission=excluded.mission, "
            "agent=COALESCE(excluded.agent, tasks.agent), "
            "project_id=COALESCE(excluded.project_id, tasks.project_id), "
            "updated_at=datetime('now')",
            (ext_id, mission, title, status, source, agent, project_id),
        )

    def for_board(self, status: str = "", workflow: str = "", agent: str = "",
                  project_id: str = "") -> list[dict]:
        """Tasks pro Quadro, com filtros opcionais. `workflow` filtra pela mission.
        Deriva `agent` do Journey Log quando a coluna está vazia."""
        sql = (
            "SELECT t.*, t.mission AS workflow, "
            "COALESCE(t.agent, (SELECT e.agent_id FROM task_events e "
            "WHERE e.task_id=t.ext_id AND e.agent_id IS NOT NULL ORDER BY e.id LIMIT 1)) AS agent_eff "
            "FROM tasks t WHERE 1=1"
        )
        params: list = []
        if status:
            sql += " AND t.status=?"; params.append(status)
        if workflow:
            sql += " AND t.mission=?"; params.append(workflow)
        if agent:
            sql += " AND COALESCE(t.agent,'')=?"; params.append(agent)
        if project_id:
            sql += " AND t.project_id=?"; params.append(project_id)
        sql += " ORDER BY t.id"
        return db.query(sql, tuple(params))

    def set_status(self, ext_id: str, status: str) -> int:
        return db.execute(
            "UPDATE tasks SET status=?, updated_at=datetime('now') WHERE ext_id=?",
            (status, ext_id),
        )

    def get_task(self, ext_id: str) -> dict | None:
        return db.query_one("SELECT * FROM tasks WHERE ext_id=?", (ext_id,))

    def complete_task(self, ext_id: str, actor: str = "system", note: str | None = None) -> int:
        """Encerra a entidade: status completed + completed_at/killed_at agora."""
        return db.execute(
            "UPDATE tasks SET status='completed', completed_at=datetime('now'), "
            "killed_at=datetime('now'), updated_at=datetime('now') WHERE ext_id=?",
            (ext_id,),
        )

    def update_digest(self, ext_id: str, digest_text: str) -> int:
        return db.execute(
            "UPDATE tasks SET digest_text=?, updated_at=datetime('now') WHERE ext_id=?",
            (digest_text, ext_id),
        )

    def list(self, status: str = "") -> list[dict]:
        if status:
            return db.query("SELECT * FROM tasks WHERE status=? ORDER BY id", (status,))
        return db.query("SELECT * FROM tasks ORDER BY id")

    def count(self, status: str = "") -> int:
        return db.count("tasks", "status=?", (status,)) if status else db.count("tasks")


# ── approvals ─────────────────────────────────────────────────────────────
class _Approvals:
    def _ttl_minutes(self) -> int:
        import os
        raw = (os.environ.get("JAVES_APPROVAL_TTL_MIN") or os.environ.get("JAVIS_APPROVAL_TTL_MIN") or "").strip()
        if not raw:
            return 60
        try:
            return max(1, int(raw))
        except Exception:
            return 60

    def _parse_ts(self, value: str | None) -> datetime | None:
        raw = (value or "").strip()
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace(" ", "T"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except Exception:
            return None

    def _is_expired(self, approval: dict) -> bool:
        anchor = self._parse_ts(approval.get("decided_at")) or self._parse_ts(approval.get("updated_at"))
        if not anchor:
            return False
        return datetime.now(timezone.utc) - anchor > timedelta(minutes=self._ttl_minutes())

    def add(self, subject: str, kind: str = "gate", agent: str = "",
            detail: str = "", task_id: str = "", project_id: str = "",
            action: str = "", route: str = "", risk_level: str = "",
            requested_by: str = "", reason: str = "",
            metadata: dict | None = None) -> int:
        metadata_json = _json.dumps(metadata, ensure_ascii=False) if metadata else None
        return db.execute(
            "INSERT INTO approvals(kind, subject, agent, task_id, project_id, action, route, "
            "risk_level, status, detail, requested_by, reason, metadata_json, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,'pending',?,?,?,?,datetime('now'))",
            (
                kind, subject, agent, task_id, project_id, action, route,
                risk_level, detail, requested_by, reason, metadata_json,
            ),
        )

    def get(self, approval_id: int) -> dict | None:
        return db.query_one("SELECT * FROM approvals WHERE id=?", (approval_id,))

    def decide(self, approval_id: int, approved: bool, note: str = "",
               approved_by: str = "local") -> int:
        return db.execute(
            "UPDATE approvals SET status=?, note=?, approved_by=?, "
            "decided_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
            ("approved" if approved else "rejected", note, approved_by, approval_id),
        )

    def consume(self, approval_id: int) -> int:
        return db.execute_rowcount(
            "UPDATE approvals SET consumed_at=datetime('now'), updated_at=datetime('now') "
            "WHERE id=? AND consumed_at IS NULL",
            (approval_id,),
        )

    def find_pending_action(self, action: str, route: str = "", project_id: str = "") -> dict | None:
        return db.query_one(
            "SELECT * FROM approvals WHERE status='pending' "
            "AND COALESCE(action,'')=? AND COALESCE(route,'')=? "
            "AND COALESCE(project_id,'')=? ORDER BY id DESC LIMIT 1",
            (action, route, project_id),
        )

    def valid_for_action(self, approval: dict | None, action: str,
                         route: str = "", project_id: str = "") -> bool:
        if not approval or approval.get("status") != "approved":
            return False
        if approval.get("consumed_at"):
            return False
        if self._is_expired(approval):
            try:
                db.execute(
                    "UPDATE approvals SET status='expired', updated_at=datetime('now') WHERE id=? AND status='approved'",
                    (approval["id"],),
                )
            except Exception:
                pass
            approval["status"] = "expired"
            return False
        saved_action = approval.get("action") or ""
        if saved_action and saved_action != action:
            return False
        saved_route = approval.get("route") or ""
        if route and saved_route and saved_route != route:
            return False
        saved_project = approval.get("project_id") or ""
        if project_id and saved_project != project_id:
            return False
        return True

    def pending(self) -> list[dict]:
        return db.query("SELECT * FROM approvals WHERE status='pending' ORDER BY id DESC")

    def by_task(self, task_id: str) -> list[dict]:
        return db.query("SELECT * FROM approvals WHERE task_id=? ORDER BY id", (task_id,))

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


# ── content (Estúdio de Conteúdo) ─────────────────────────────────────────
class _Content:
    def add(self, project: str, channel: str, title: str, body: str,
            status: str = "rascunho") -> int:
        return db.execute(
            "INSERT INTO content(project, channel, title, body, status) VALUES(?,?,?,?,?)",
            (project, channel, title, body, status),
        )

    def list(self, project: str = "", limit: int = 100) -> list[dict]:
        if project:
            return db.query(
                "SELECT * FROM content WHERE project=? ORDER BY id DESC LIMIT ?",
                (project, limit),
            )
        return db.query("SELECT * FROM content ORDER BY id DESC LIMIT ?", (limit,))


# ── task_events (Journey Log) ─────────────────────────────────────────────
class _TaskEvents:
    def add_event(self, task_id: str, event_type: str, actor: str = "system",
                  message: str = "", agent_id: str | None = None,
                  metadata: dict | None = None) -> int:
        meta = _json.dumps(metadata, ensure_ascii=False) if metadata else None
        return db.execute(
            "INSERT INTO task_events(task_id, event_type, actor, agent_id, message, metadata_json) "
            "VALUES(?,?,?,?,?,?)",
            (task_id, event_type, actor, agent_id, message, meta),
        )

    def list_by_task(self, task_id: str) -> list[dict]:
        """Timeline em ordem cronológica. metadata_json vira dict em 'metadata'."""
        rows = db.query("SELECT * FROM task_events WHERE task_id=? ORDER BY id", (task_id,))
        for r in rows:
            raw = r.get("metadata_json")
            try:
                r["metadata"] = _json.loads(raw) if raw else {}
            except Exception:
                r["metadata"] = {}
        return rows

    def count_by_task(self, task_id: str) -> int:
        return db.count("task_events", "task_id=?", (task_id,))


# instâncias prontas pra uso
messages  = _Messages()
tasks     = _Tasks()
approvals = _Approvals()
logs      = _Logs()
agents    = _Agents()
projects  = _Projects()
workflows = _Workflows()
memories  = _Memories()
content   = _Content()
task_events = _TaskEvents()
