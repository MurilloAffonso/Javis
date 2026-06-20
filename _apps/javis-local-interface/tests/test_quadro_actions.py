"""Testes das ações operacionais do Quadro: POST /tasks/{id}/status.
Cobre: mudança de status, evento status_changed, action_logs task_status_changed,
bloqueio de reabertura, completed reusa lifecycle/digest, idempotência, /stats.
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


def _seed(ext_id="q-1", status="pending"):
    import repositories as repo
    repo.tasks.upsert(ext_id, "Task do Quadro", status=status, mission="wf")
    return ext_id


def test_muda_status() -> int:
    print("\n--- Muda status da task pelo endpoint ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed()
    res = task_lifecycle.change_task_status(tid, "in_progress", note="comecei")
    if not check("retorno ok", res.get("ok") is True):
        failures += 1
    if not check("status atualizado no SQLite", repo.tasks.get_task(tid)["status"] == "in_progress"):
        failures += 1
    return failures


def test_registra_status_changed() -> int:
    print("\n--- Registra status_changed no Journey Log (com metadata) ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed()
    task_lifecycle.change_task_status(tid, "gate_approved", note="liberado")
    ev = next((e for e in repo.task_events.list_by_task(tid) if e["event_type"] == "status_changed"), None)
    if not check("evento status_changed criado", ev is not None):
        failures += 1
    md = ev["metadata"] if ev else {}
    if not check("metadata from_status=pending", md.get("from_status") == "pending"):
        failures += 1
    if not check("metadata to_status=gate_approved", md.get("to_status") == "gate_approved"):
        failures += 1
    if not check("metadata source=board", md.get("source") == "board"):
        failures += 1
    return failures


def test_registra_action_log() -> int:
    print("\n--- Registra task_status_changed em action_logs ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed()
    task_lifecycle.change_task_status(tid, "in_progress")
    intents = [l["intent"] for l in repo.logs.recent(10)]
    if not check("action_logs tem task_status_changed", "task_status_changed" in intents):
        failures += 1
    return failures


def test_bloqueia_reabertura() -> int:
    print("\n--- Não reabre task completed/killed ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed()
    task_lifecycle.change_task_status(tid, "completed")   # mata
    res = task_lifecycle.change_task_status(tid, "pending")  # tenta reabrir
    if not check("reabertura recusada (ok=False)", res.get("ok") is False):
        failures += 1
    if not check("erro de encerrada", "encerrada" in (res.get("error") or "")):
        failures += 1
    if not check("status segue completed", repo.tasks.get_task(tid)["status"] == "completed"):
        failures += 1
    return failures


def test_completed_reusa_lifecycle() -> int:
    print("\n--- Mover para completed usa lifecycle/digest existente ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed()
    repo.task_events.add_event(tid, "task_created", "system", "nasceu")
    res = task_lifecycle.change_task_status(tid, "completed")
    if not check("retorna digest_text (lifecycle)", bool((res.get("digest_text") or "").strip())):
        failures += 1
    tipos = [e["event_type"] for e in repo.task_events.list_by_task(tid)]
    if not check("gerou task_completed", "task_completed" in tipos):
        failures += 1
    if not check("gerou entity_killed", "entity_killed" in tipos):
        failures += 1
    if not check("gerou ai_digest_created", "ai_digest_created" in tipos):
        failures += 1
    return failures


def test_idempotente_e_stats() -> int:
    print("\n--- Idempotência + /stats reflete ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle, server
    failures = 0
    tid = _seed()
    pend0 = repo.tasks.count("pending")
    task_lifecycle.change_task_status(tid, "in_progress")
    if not check(f"pending diminuiu ({pend0} → {repo.tasks.count('pending')})",
                 repo.tasks.count("pending") == pend0 - 1):
        failures += 1
    # idempotente: mesmo status
    res = task_lifecycle.change_task_status(tid, "in_progress")
    if not check("mesmo status = unchanged", res.get("unchanged") is True):
        failures += 1
    # endpoint inválido
    resp = asyncio.run(server.task_set_status(tid, server.StatusRequest(status="xpto")))
    if not check("status inválido → 409", resp.status_code == 409):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: ações operacionais do Quadro (SQLite)")
    print("=" * 50)
    total = 0
    total += test_muda_status()
    total += test_registra_status_changed()
    total += test_registra_action_log()
    total += test_bloqueia_reabertura()
    total += test_completed_reusa_lifecycle()
    total += test_idempotente_e_stats()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
