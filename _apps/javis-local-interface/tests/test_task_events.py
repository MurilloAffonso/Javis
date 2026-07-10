"""Testes do Journey Log (task_events): repositório, fluxo da pauta, efeitos da
Gate 1 e endpoint /tasks/{task_id}/events. Tudo em DB temporário isolado.
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

_T0 = "pipeline-marketing-vem-passear-jampa-t0"
_GATE1_AP = {"id": 1, "agent": "nova", "task_id": _T0,
             "subject": "Aprovar a pauta da semana da Vem Passear (Gate 1) antes de ir pro Design"}
_PAUTA_FILE = Path(__file__).resolve().parents[3] / "_projetos" / "cerebro-jampa" / "posts" / "pauta-semana.md"


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


def test_criar_e_listar_evento() -> int:
    print("\n--- Criar e listar eventos de task ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    repo.task_events.add_event("tX", "task_created", "system", "nasceu", metadata={"a": 1})
    repo.task_events.add_event("tX", "agent_called", "agent", "chamou", agent_id="nova")
    evs = repo.task_events.list_by_task("tX")
    if not check("2 eventos listados", len(evs) == 2):
        failures += 1
    if not check("ordem cronológica (task_created primeiro)", evs[0]["event_type"] == "task_created"):
        failures += 1
    if not check("metadata parseada em dict", evs[0]["metadata"] == {"a": 1}):
        failures += 1
    if not check("agent_id preservado", evs[1]["agent_id"] == "nova"):
        failures += 1
    if not check("count_by_task == 2", repo.task_events.count_by_task("tX") == 2):
        failures += 1
    return failures


def test_fluxo_pauta_cria_eventos() -> int:
    print("\n--- Fluxo da pauta cria os eventos esperados ---")
    _fresh_db()
    import repositories as repo
    import agent, vp_squad, mission_board, logger
    failures = 0
    bkp = _PAUTA_FILE.read_text(encoding="utf-8") if _PAUTA_FILE.exists() else None
    o_run, o_done, o_logs = vp_squad.run, mission_board.set_task_done, logger.LOGS_DIR
    vp_squad.run = lambda *a, **k: {"status": "ok", "name": "Nova", "agent": "nova",
                                    "result": "pauta fake\nStatus: ... (Gate 1)"}
    mission_board.set_task_done = lambda *a, **k: True
    logger.LOGS_DIR = Path(tempfile.mkdtemp())
    try:
        agent._fluxo_pauta_vp()
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_T0)]
        for et in ["task_created", "intent_detected", "agent_called", "file_generated", "approval_requested"]:
            if not check(f"evento '{et}' registrado", et in tipos):
                failures += 1
    finally:
        vp_squad.run, mission_board.set_task_done, logger.LOGS_DIR = o_run, o_done, o_logs
        if bkp is not None:
            _PAUTA_FILE.write_text(bkp, encoding="utf-8")  # restaura a pauta real
    return failures


def test_aprovacao_gera_eventos() -> int:
    print("\n--- Aprovar Gate 1 gera approval_approved + workflow_advanced + design_task_unlocked ---")
    _fresh_db()
    import repositories as repo
    import approval_effects, mission_board
    failures = 0
    o = mission_board.set_task_done
    mission_board.set_task_done = lambda *a, **k: True
    try:
        approval_effects.on_decided(dict(_GATE1_AP), True)
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_T0)]
        for et in ["approval_approved", "workflow_advanced", "design_task_unlocked"]:
            if not check(f"evento '{et}' registrado", et in tipos):
                failures += 1
        ap = next((e for e in repo.task_events.list_by_task(_T0) if e["event_type"] == "approval_approved"), None)
        if not check("approval_approved tem ator 'murillo'", bool(ap) and ap["actor"] == "murillo"):
            failures += 1
    finally:
        mission_board.set_task_done = o
    return failures


def test_rejeicao_gera_eventos() -> int:
    print("\n--- Rejeitar Gate 1 gera approval_rejected + adjustment_required (sem design) ---")
    _fresh_db()
    import repositories as repo
    import approval_effects, mission_board
    failures = 0
    o = mission_board.set_task_done
    mission_board.set_task_done = lambda *a, **k: True
    try:
        approval_effects.on_decided(dict(_GATE1_AP), False)
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_T0)]
        if not check("'approval_rejected' registrado", "approval_rejected" in tipos):
            failures += 1
        if not check("'adjustment_required' registrado", "adjustment_required" in tipos):
            failures += 1
        if not check("NÃO gerou 'design_task_unlocked'", "design_task_unlocked" not in tipos):
            failures += 1
    finally:
        mission_board.set_task_done = o
    return failures


def test_endpoint_eventos() -> int:
    print("\n--- Endpoint GET /tasks/{id}/events ---")
    _fresh_db()
    import repositories as repo
    import server
    failures = 0
    # R3.1: /tasks/{id}/events é escopado — a task precisa existir no projeto.
    repo.tasks.upsert("tEnd", "Task End", project_id="javes-core")
    repo.task_events.add_event("tEnd", "task_created", "system", "oi")
    repo.task_events.add_event("tEnd", "agent_called", "agent", "chamou nova", agent_id="nova")
    resp = asyncio.run(server.task_events("tEnd"))
    body = json.loads(bytes(resp.body))
    if not check("endpoint retorna total == 2", body.get("total") == 2):
        failures += 1
    if not check("timeline cronológica (1º task_created)", body["events"][0]["event_type"] == "task_created"):
        failures += 1
    if not check("evento traz message", body["events"][0].get("message") == "oi"):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: Journey Log (task_events)")
    print("=" * 50)
    total = 0
    total += test_criar_e_listar_evento()
    total += test_fluxo_pauta_cria_eventos()
    total += test_aprovacao_gera_eventos()
    total += test_rejeicao_gera_eventos()
    total += test_endpoint_eventos()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
