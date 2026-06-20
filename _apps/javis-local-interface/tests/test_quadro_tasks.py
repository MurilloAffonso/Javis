"""Testes do Quadro lendo SQLite (GET /tasks) com fallback Markdown.
Cobre: tasks do SQLite, filtros, independência do Markdown na renderização,
task concluída aparece como completed, indicação de digest, fallback Markdown.
"""
import sys
import io
import json
import asyncio
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    print(f"  [{PASS if condition else FAIL}] {description}")
    return condition


def _fresh_db():
    import db
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db.DB_PATH = Path(tmp.name)
    db._initialized = False
    db.init_db()
    return db


def _tasks_via_endpoint(**kw):
    import server
    resp = asyncio.run(server.tasks_list(**kw))
    return json.loads(bytes(resp.body))


def test_tasks_do_sqlite() -> int:
    print("\n--- GET /tasks retorna tarefas do SQLite ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    repo.tasks.upsert("a-1", "Tarefa A", status="pending", mission="wf1", project_id="p1")
    repo.tasks.upsert("a-2", "Tarefa B", status="done", mission="wf1", project_id="p1")
    body = _tasks_via_endpoint()
    if not check("total == 2", body.get("total") == 2):
        failures += 1
    if not check("source == sqlite", body.get("source") == "sqlite"):
        failures += 1
    t = body["tasks"][0]
    for f in ("ext_id", "title", "status", "agent", "workflow", "project_id", "has_digest"):
        if not check(f"campo '{f}' presente", f in t):
            failures += 1
    return failures


def test_filtros() -> int:
    print("\n--- Filtros status/workflow/project_id ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    repo.tasks.upsert("f-1", "T1", status="pending", mission="wfA", project_id="px")
    repo.tasks.upsert("f-2", "T2", status="done", mission="wfA", project_id="px")
    repo.tasks.upsert("f-3", "T3", status="pending", mission="wfB", project_id="py")
    if not check("filtro status=pending → 2", _tasks_via_endpoint(status="pending")["total"] == 2):
        failures += 1
    if not check("filtro workflow=wfA → 2", _tasks_via_endpoint(workflow="wfA")["total"] == 2):
        failures += 1
    if not check("filtro project_id=py → 1", _tasks_via_endpoint(project_id="py")["total"] == 1):
        failures += 1
    return failures


def test_independe_markdown() -> int:
    print("\n--- Quadro renderiza do SQLite sem depender do Markdown ---")
    _fresh_db()
    import repositories as repo
    import mission_board
    failures = 0
    repo.tasks.upsert("m-1", "Só no SQLite", status="pending", mission="wf")
    orig = mission_board.get_missions
    mission_board.get_missions = lambda: (_ for _ in ()).throw(RuntimeError("markdown indisponível"))
    try:
        body = _tasks_via_endpoint()
        if not check("retorna a task do SQLite mesmo com Markdown quebrado", body["total"] == 1):
            failures += 1
    finally:
        mission_board.get_missions = orig
    return failures


def test_concluida_aparece_completed() -> int:
    print("\n--- Task concluída aparece como completed/killed ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    repo.tasks.upsert("c-1", "Vai morrer", status="pending", mission="wf")
    repo.task_events.add_event("c-1", "task_created", "system", "nasceu")
    task_lifecycle.complete_task("c-1")
    body = _tasks_via_endpoint()
    t = next((x for x in body["tasks"] if x["ext_id"] == "c-1"), None)
    if not check("status == completed", bool(t) and t["status"] == "completed"):
        failures += 1
    if not check("indica que tem digest (has_digest)", bool(t) and t["has_digest"] is True):
        failures += 1
    if not check("completed_at presente", bool(t) and bool(t["completed_at"])):
        failures += 1
    return failures


def test_fallback_markdown() -> int:
    print("\n--- Fallback Markdown: SQLite vazio sincroniza do backlog ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    if not check("SQLite começa vazio", repo.tasks.count() == 0):
        failures += 1
    body = _tasks_via_endpoint()   # deve sincronizar do mission_board real
    if not check("após fallback, há tarefas do backlog", body["total"] > 0):
        failures += 1
    if not check("SQLite foi populado pelo fallback", repo.tasks.count() > 0):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: Quadro lendo SQLite (GET /tasks)")
    print("=" * 50)
    total = 0
    total += test_tasks_do_sqlite()
    total += test_filtros()
    total += test_independe_markdown()
    total += test_concluida_aparece_completed()
    total += test_fallback_markdown()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
