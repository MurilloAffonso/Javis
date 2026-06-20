"""Testes da aprovação humana Gate 1 — repositório + endpoints, em DB temporário.

Cobre: listar pendentes, aprovar, rejeitar, approvals_pending diminui,
action_logs registra a decisão, e que o caminho da decisão NÃO toca integração
externa (WhatsApp/Gmail/Sheets/Instagram).
"""
import sys
import io
import json
import asyncio
import inspect
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    print(f"  [{PASS if condition else FAIL}] {description}")
    return condition


def _fresh_db():
    """Aponta o db pra um arquivo temporário e recria o schema (isolado)."""
    import db
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db.DB_PATH = Path(tmp.name)
    db._initialized = False
    db.init_db()
    return db


def test_listar_pendentes() -> int:
    print("\n--- Listar aprovações pendentes ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    repo.approvals.add("Aprovar pauta da semana (Gate 1)", agent="nova",
                       task_id="pipeline-marketing-vem-passear-jampa-t1")
    repo.approvals.add("Aprovar envio de WhatsApp", agent="midas")

    pend = repo.approvals.pending()
    if not check(f"2 pendentes listadas ({len(pend)})", len(pend) == 2):
        failures += 1
    if not check("count_pending == 2", repo.approvals.count_pending() == 2):
        failures += 1
    a = pend[-1]  # a mais antiga (ORDER BY id DESC → última é a 1ª criada)
    fields_ok = all(k in a for k in ("id", "subject", "agent", "task_id", "status", "created_at"))
    if not check("campos id/subject/agent/task_id/status/created_at presentes", fields_ok):
        failures += 1
    if not check("status inicial == 'pending'", a["status"] == "pending"):
        failures += 1
    return failures


def test_aprovar() -> int:
    print("\n--- Aprovar muda status no SQLite ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    aid = repo.approvals.add("Aprovar pauta", agent="nova")
    repo.approvals.decide(aid, True, note="pode ir pro design")
    a = repo.approvals.get(aid)
    if not check("status == 'approved'", a["status"] == "approved"):
        failures += 1
    if not check("decided_at preenchido", bool(a["decided_at"])):
        failures += 1
    if not check("note salva", a["note"] == "pode ir pro design"):
        failures += 1
    if not check("count_pending == 0 após aprovar", repo.approvals.count_pending() == 0):
        failures += 1
    return failures


def test_rejeitar() -> int:
    print("\n--- Rejeitar muda status no SQLite ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    aid = repo.approvals.add("Aprovar pauta ruim", agent="nova")
    repo.approvals.decide(aid, False, note="trocar o gancho do post 1")
    a = repo.approvals.get(aid)
    if not check("status == 'rejected'", a["status"] == "rejected"):
        failures += 1
    if not check("note da rejeição salva", a["note"] == "trocar o gancho do post 1"):
        failures += 1
    if not check("count_pending == 0 após rejeitar", repo.approvals.count_pending() == 0):
        failures += 1
    return failures


def test_pending_diminui() -> int:
    print("\n--- approvals_pending diminui após decisão ---")
    _fresh_db()
    import repositories as repo
    failures = 0
    a1 = repo.approvals.add("Gate A", agent="nova")
    repo.approvals.add("Gate B", agent="midas")
    antes = repo.approvals.count_pending()
    repo.approvals.decide(a1, True)
    depois = repo.approvals.count_pending()
    if not check(f"pendentes: {antes} → {depois} (diminuiu 1)", depois == antes - 1):
        failures += 1
    return failures


def test_endpoint_decide_e_log() -> int:
    print("\n--- Endpoint POST /approvals/{id}/decide registra em action_logs ---")
    _fresh_db()
    import repositories as repo
    import server
    failures = 0
    aid = repo.approvals.add("Aprovar pauta via endpoint", agent="nova")
    logs_antes = repo.logs.count()

    req = server.DecisionRequest(decision="approved", note="ok pelo endpoint")
    resp = asyncio.run(server.approvals_decide(aid, req))
    body = json.loads(bytes(resp.body))

    if not check("endpoint retorna ok=True", body.get("ok") is True):
        failures += 1
    if not check("endpoint retorna status 'approved'", body.get("status") == "approved"):
        failures += 1
    if not check("aprovação ficou 'approved' no banco", repo.approvals.get(aid)["status"] == "approved"):
        failures += 1
    if not check("action_logs registrou a decisão (+1)", repo.logs.count() == logs_antes + 1):
        failures += 1
    last = repo.logs.recent(1)[0]
    if not check("log com intent 'approval_decide'", last["intent"] == "approval_decide"):
        failures += 1

    # decidir de novo deve recusar (já decidida) — 409
    resp2 = asyncio.run(server.approvals_decide(aid, req))
    if not check("re-decidir retorna erro (status != 200)", resp2.status_code == 409):
        failures += 1
    return failures


def test_sem_integracao_externa() -> int:
    print("\n--- Decisão NÃO chama integração externa ---")
    import server
    failures = 0
    src = inspect.getsource(server.approvals_decide)
    # remove a docstring (que MENCIONA WhatsApp só pra dizer que NÃO envia) —
    # queremos achar CHAMADAS reais de integração, não palavras em comentário.
    doc = server.approvals_decide.__doc__
    if doc:
        src = src.replace(doc, "")
    src = src.lower()
    # tokens de CHAMADA/IMPORT de integração externa (não palavras soltas)
    proibidos = ["whatsapp_send", "import integrations", "integrations.", "gmail",
                 "instagram", "sheets.", "telegram_bridge", "requests.get", "requests.post"]
    achou = [p for p in proibidos if p in src]
    if not check(f"endpoint de decisão sem chamada de integração externa (achados: {achou})", not achou):
        failures += 1
    return failures


_T1 = "pipeline-marketing-vem-passear-jampa-t1"
_T2 = "pipeline-marketing-vem-passear-jampa-t2"
_GATE1_AP = {"id": 1, "agent": "nova", "task_id": _T1,
             "subject": "Aprovar a pauta da semana da Vem Passear (Gate 1) antes de ir pro Design"}


def _patch_mission_board():
    """Evita que o teste escreva no codex_backlog.md real. Retorna (modulo, original)."""
    import mission_board
    orig = mission_board.set_task_done
    mission_board.set_task_done = lambda *a, **k: True
    return mission_board, orig


def test_aprovar_gate1_libera_design() -> int:
    print("\n--- Aprovar Gate 1 LIBERA task de Design ---")
    _fresh_db()
    import repositories as repo
    import approval_effects
    mb, orig = _patch_mission_board()
    failures = 0
    try:
        res = approval_effects.on_decided(dict(_GATE1_AP), True)
        if not check("avançou o workflow", res.get("advanced") is True):
            failures += 1
        if not check("retornou design_task t2", res.get("design_task", "").endswith("-t2")):
            failures += 1
        design = next((t for t in repo.tasks.list() if t["ext_id"] == _T2), None)
        if not check("task de Design existe no SQLite", design is not None):
            failures += 1
        if not check("task de Design pending", bool(design) and design["status"] == "pending"):
            failures += 1
        gate = next((t for t in repo.tasks.list() if t["ext_id"] == _T1), None)
        if not check("gate marcada 'gate_approved'", bool(gate) and gate["status"] == "gate_approved"):
            failures += 1
        adv = [l for l in repo.logs.recent(10) if l["intent"] == "workflow_advance"]
        if not check("log workflow_advance registrado", len(adv) >= 1):
            failures += 1
    finally:
        mb.set_task_done = orig
    return failures


def test_aprovar_gate1_idempotente() -> int:
    print("\n--- Aprovar Gate 1 duas vezes NÃO duplica Design ---")
    _fresh_db()
    import repositories as repo
    import approval_effects
    mb, orig = _patch_mission_board()
    failures = 0
    try:
        approval_effects.on_decided(dict(_GATE1_AP), True)
        n1 = len([t for t in repo.tasks.list() if t["ext_id"] == _T2])
        adv1 = len([l for l in repo.logs.recent(30) if l["intent"] == "workflow_advance"])
        res2 = approval_effects.on_decided(dict(_GATE1_AP), True)  # de novo
        n2 = len([t for t in repo.tasks.list() if t["ext_id"] == _T2])
        adv2 = len([l for l in repo.logs.recent(30) if l["intent"] == "workflow_advance"])
        if not check(f"Design não duplicou (t2: {n1} → {n2})", n1 == 1 and n2 == 1):
            failures += 1
        if not check("2ª chamada detecta 'already'", res2.get("already") is True):
            failures += 1
        if not check(f"não re-logou workflow_advance ({adv1} → {adv2})", adv1 == adv2):
            failures += 1
    finally:
        mb.set_task_done = orig
    return failures


def test_rejeitar_gate1_nao_cria_design() -> int:
    print("\n--- Rejeitar Gate 1 NÃO cria task de Design ---")
    _fresh_db()
    import repositories as repo
    import approval_effects
    mb, orig = _patch_mission_board()
    failures = 0
    try:
        res = approval_effects.on_decided(dict(_GATE1_AP), False)
        if not check("não avançou o workflow", res.get("advanced") is False):
            failures += 1
        if not check("marcou rejected", res.get("rejected") is True):
            failures += 1
        design = [t for t in repo.tasks.list() if t["ext_id"] == _T2]
        if not check("nenhuma task de Design criada", len(design) == 0):
            failures += 1
        rej = [l for l in repo.logs.recent(10) if l["intent"] == "workflow_reject"]
        if not check("log workflow_reject registrado", len(rej) >= 1):
            failures += 1
    finally:
        mb.set_task_done = orig
    return failures


def test_endpoint_gate1_destrava_e_loga() -> int:
    print("\n--- Endpoint: aprovar Gate 1 loga approval_decide + workflow_advance ---")
    _fresh_db()
    import repositories as repo
    import server
    mb, orig = _patch_mission_board()
    failures = 0
    try:
        aid = repo.approvals.add(_GATE1_AP["subject"], agent="nova", task_id=_T1)
        req = server.DecisionRequest(decision="approved", note="pode ir pro design")
        resp = asyncio.run(server.approvals_decide(aid, req))
        body = json.loads(bytes(resp.body))
        if not check("endpoint sinaliza advanced=True", body.get("advanced") is True):
            failures += 1
        if not check("mensagem de destrave de criativos",
                     "destravada" in (body.get("message", "").lower())):
            failures += 1
        intents = [l["intent"] for l in repo.logs.recent(10)]
        if not check("action_logs tem approval_decide", "approval_decide" in intents):
            failures += 1
        if not check("action_logs tem workflow_advance", "workflow_advance" in intents):
            failures += 1
        design = next((t for t in repo.tasks.list() if t["ext_id"] == _T2), None)
        if not check("Design pending no SQLite", bool(design) and design["status"] == "pending"):
            failures += 1
    finally:
        mb.set_task_done = orig
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: aprovação humana Gate 1")
    print("=" * 50)
    total = 0
    total += test_listar_pendentes()
    total += test_aprovar()
    total += test_rejeitar()
    total += test_pending_diminui()
    total += test_endpoint_decide_e_log()
    total += test_sem_integracao_externa()
    total += test_aprovar_gate1_libera_design()
    total += test_aprovar_gate1_idempotente()
    total += test_rejeitar_gate1_nao_cria_design()
    total += test_endpoint_gate1_destrava_e_loga()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
