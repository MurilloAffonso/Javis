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
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
