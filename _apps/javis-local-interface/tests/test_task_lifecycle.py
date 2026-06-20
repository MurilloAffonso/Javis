"""Testes do fechamento da entidade: complete_task, eventos task_completed/
entity_killed/ai_digest_created, digest gerado/salvo, endpoints e idempotência.
Tudo em DB temporário isolado.
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


def _seed_task(ext_id="t-life"):
    import repositories as repo
    repo.tasks.upsert(ext_id, "Tarefa de teste", status="pending", mission="m", source="test")
    repo.task_events.add_event(ext_id, "task_created", "system", "nasceu")
    repo.task_events.add_event(ext_id, "agent_called", "agent", "chamou", agent_id="nova")
    return ext_id


def test_concluir_cria_eventos() -> int:
    print("\n--- Concluir cria task_completed + entity_killed + ai_digest_created ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed_task()
    res = task_lifecycle.complete_task(tid, note="encerrando")
    if not check("complete_task ok", res.get("ok") is True):
        failures += 1
    if not check("status == 'completed'", res.get("status") == "completed"):
        failures += 1
    tipos = [e["event_type"] for e in repo.task_events.list_by_task(tid)]
    for et in ["task_completed", "entity_killed", "ai_digest_created"]:
        if not check(f"evento '{et}' criado", et in tipos):
            failures += 1
    t = repo.tasks.get_task(tid)
    if not check("completed_at preenchido", bool(t.get("completed_at"))):
        failures += 1
    if not check("killed_at preenchido", bool(t.get("killed_at"))):
        failures += 1
    return failures


def test_digest_gerado_e_salvo() -> int:
    print("\n--- Digest gerado e salvo na task ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed_task()
    res = task_lifecycle.complete_task(tid)
    if not check("digest retornado não-vazio", bool((res.get("digest_text") or "").strip())):
        failures += 1
    if not check("digest tem cabeçalho 'Digest'", "Digest" in (res.get("digest_text") or "")):
        failures += 1
    if not check("digest tem 'Próximo passo'", "Próximo passo" in (res.get("digest_text") or "")):
        failures += 1
    t = repo.tasks.get_task(tid)
    if not check("digest persistido na task", bool((t.get("digest_text") or "").strip())):
        failures += 1
    return failures


def test_idempotente_nao_duplica() -> int:
    print("\n--- Não permite duplicar morte/conclusão ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed_task()
    task_lifecycle.complete_task(tid)
    n1 = repo.task_events.count_by_task(tid)
    res2 = task_lifecycle.complete_task(tid)
    n2 = repo.task_events.count_by_task(tid)
    if not check("2ª conclusão recusada (ok=False)", res2.get("ok") is False):
        failures += 1
    if not check("erro 'já encerrada'", "encerrada" in (res2.get("error") or "")):
        failures += 1
    if not check(f"não duplicou eventos ({n1} == {n2})", n1 == n2):
        failures += 1
    return failures


def test_stats_reflete() -> int:
    print("\n--- /stats reflete a conclusão (pending → completed) ---")
    _fresh_db()
    import repositories as repo
    import task_lifecycle
    failures = 0
    tid = _seed_task()
    pend0 = repo.tasks.count("pending")
    done0 = repo.tasks.count("completed")
    task_lifecycle.complete_task(tid)
    if not check(f"pending diminuiu ({pend0} → {repo.tasks.count('pending')})",
                 repo.tasks.count("pending") == pend0 - 1):
        failures += 1
    if not check(f"completed aumentou ({done0} → {repo.tasks.count('completed')})",
                 repo.tasks.count("completed") == done0 + 1):
        failures += 1
    return failures


def test_endpoint_complete_e_digest() -> int:
    print("\n--- Endpoints POST /complete e GET /digest ---")
    _fresh_db()
    import repositories as repo
    import server
    failures = 0
    tid = _seed_task()
    # POST complete
    resp = asyncio.run(server.task_complete(tid, server.CompleteRequest(note="via endpoint")))
    body = json.loads(bytes(resp.body))
    if not check("POST /complete ok", body.get("ok") is True):
        failures += 1
    if not check("retorna digest_text", bool((body.get("digest_text") or "").strip())):
        failures += 1
    # GET digest
    resp2 = asyncio.run(server.task_digest(tid))
    d = json.loads(bytes(resp2.body))
    if not check("GET /digest status == completed", d.get("status") == "completed"):
        failures += 1
    if not check("GET /digest traz digest_text", bool((d.get("digest_text") or "").strip())):
        failures += 1
    if not check("GET /digest traz completed_at", bool(d.get("completed_at"))):
        failures += 1
    # re-complete pelo endpoint → 409
    resp3 = asyncio.run(server.task_complete(tid, server.CompleteRequest(note="de novo")))
    if not check("re-concluir retorna 409", resp3.status_code == 409):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: morte da entidade + digest")
    print("=" * 50)
    total = 0
    total += test_concluir_cria_eventos()
    total += test_digest_gerado_e_salvo()
    total += test_idempotente_nao_duplica()
    total += test_stats_reflete()
    total += test_endpoint_complete_e_digest()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
