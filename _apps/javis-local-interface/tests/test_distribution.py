"""Testes do avanço Gate 2 → Distribuição (modo seguro) + Gate 3.
Cobre: aprovar Gate 2 destrava Distribuição, rejeitar não cria, preparar gera
arquivo + eventos + Gate 3 em /approvals/pending, idempotência, sem integração.
"""
import sys
import io
import json
import asyncio
import inspect
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

_DESIGN = "pipeline-marketing-vem-passear-jampa-t2"
_DIST = "vp-distribuicao-preparar"
_GATE2_AP = {"id": 50, "agent": "estudio", "task_id": _DESIGN,
             "subject": "Aprovar criativos da semana antes de publicar"}


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


def _backup():
    import distribution
    return distribution.DISTRIB.read_text(encoding="utf-8") if distribution.DISTRIB.exists() else None


def _restore(bkp):
    import distribution
    if bkp is not None:
        distribution.DISTRIB.write_text(bkp, encoding="utf-8")
    elif distribution.DISTRIB.exists():
        os.remove(distribution.DISTRIB)


def test_aprovar_gate2_destrava_distribuicao() -> int:
    print("\n--- Aprovar Gate 2 cria/libera task de Distribuição ---")
    _fresh_db()
    import repositories as repo, approval_effects
    failures = 0
    repo.tasks.upsert(_DESIGN, "[Design] criativos", status="in_progress", mission="pipeline-marketing-vem-passear-jampa")
    res = approval_effects.on_decided(dict(_GATE2_AP), True)
    if not check("avançou (Gate 2)", res.get("advanced") is True):
        failures += 1
    dt = repo.tasks.get_task(_DIST)
    if not check("task de Distribuição criada", dt is not None):
        failures += 1
    if not check("status pending", bool(dt) and dt["status"] == "pending"):
        failures += 1
    if not check("agent midas", bool(dt) and dt["agent"] == "midas"):
        failures += 1
    tipos = [e["event_type"] for e in repo.task_events.list_by_task(_DESIGN)]
    if not check("evento distribution_task_unlocked", "distribution_task_unlocked" in tipos):
        failures += 1
    return failures


def test_rejeitar_gate2_nao_cria() -> int:
    print("\n--- Rejeitar Gate 2 NÃO cria Distribuição ---")
    _fresh_db()
    import repositories as repo, approval_effects
    failures = 0
    repo.tasks.upsert(_DESIGN, "[Design] criativos", status="in_progress", mission="pipeline-marketing-vem-passear-jampa")
    res = approval_effects.on_decided(dict(_GATE2_AP), False)
    if not check("não avançou", res.get("advanced") is False):
        failures += 1
    if not check("nenhuma task de Distribuição", repo.tasks.get_task(_DIST) is None):
        failures += 1
    tipos = [e["event_type"] for e in repo.task_events.list_by_task(_DESIGN)]
    if not check("evento approval_rejected", "approval_rejected" in tipos):
        failures += 1
    if not check("Design volta pra pending (ajuste)", repo.tasks.get_task(_DESIGN)["status"] == "pending"):
        failures += 1
    return failures


def test_prepara_distribuicao() -> int:
    print("\n--- Preparar Distribuição gera arquivo + eventos + Gate 3 ---")
    _fresh_db()
    import repositories as repo, distribution
    failures = 0
    bkp = _backup()
    repo.tasks.upsert(_DIST, "[Distribuição] Preparar pacote de publicação da pauta aprovada",
                      status="pending", mission="pipeline-marketing-vem-passear-jampa", agent="midas")
    try:
        res = distribution.run_distribution(_DIST)
        if not check("run_distribution ok", res.get("ok") is True):
            failures += 1
        if not check("distribuicao-semana.md existe", distribution.DISTRIB.exists()):
            failures += 1
        txt = distribution.DISTRIB.read_text(encoding="utf-8")
        for marca in ("Calendário sugerido", "Canais sugeridos", "Checklist antes de publicar",
                      "[CONFIRMAR COM MURILLO", "Gate 3"):
            if not check(f"conteúdo tem '{marca}'", marca in txt):
                failures += 1
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_DIST)]
        for et in ["agent_called", "file_generated", "approval_requested"]:
            if not check(f"evento '{et}'", et in tipos):
                failures += 1
    finally:
        _restore(bkp)
    return failures


def test_gate3_pendente_e_endpoint() -> int:
    print("\n--- Cria Gate 3 e aparece em /approvals/pending ---")
    _fresh_db()
    import repositories as repo, distribution, server
    failures = 0
    bkp = _backup()
    repo.tasks.upsert(_DIST, "[Distribuição] Preparar pacote de publicação da pauta aprovada",
                      status="pending", mission="pipeline-marketing-vem-passear-jampa", agent="midas")
    try:
        distribution.run_distribution(_DIST)
        g3 = next((a for a in repo.approvals.pending()
                   if a["subject"] == "Aprovar distribuição antes de publicar"), None)
        if not check("Gate 3 pendente existe", g3 is not None):
            failures += 1
        if not check("Gate 3 agent=midas", bool(g3) and g3["agent"] == "midas"):
            failures += 1
        resp = asyncio.run(server.approvals_pending())
        body = json.loads(bytes(resp.body))
        if not check("Gate 3 em /approvals/pending",
                     any(a["subject"].startswith("Aprovar distribuição") for a in body["approvals"])):
            failures += 1
        # idempotência
        res2 = distribution.run_distribution(_DIST)
        if not check("2ª execução recusada (already)", res2.get("already") is True):
            failures += 1
        n = len([a for a in repo.approvals.by_task(_DIST)
                 if a["subject"] == "Aprovar distribuição antes de publicar"])
        if not check(f"só 1 Gate 3 ({n})", n == 1):
            failures += 1
    finally:
        _restore(bkp)
    return failures


def test_sem_integracao_externa() -> int:
    print("\n--- Distribuição NÃO publica nem chama integração externa ---")
    import distribution
    failures = 0
    src = (inspect.getsource(distribution.run_distribution)
           + inspect.getsource(distribution.preparar_distribuicao_vp)
           + inspect.getsource(distribution._template_distribuicao)).lower()
    proibidos = ["whatsapp_send", "import integrations", "integrations.", "gmail_send",
                 "instagram_api", "sheets.", "telegram_bridge", "requests.get", "requests.post",
                 "imagedraw", "from pil", "import pil", ".publish(", "publicar_post"]
    achou = [p for p in proibidos if p in src]
    if not check(f"sem integração/publicação (achados: {achou})", not achou):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: Gate 2 → Distribuição + Gate 3")
    print("=" * 50)
    total = 0
    total += test_aprovar_gate2_destrava_distribuicao()
    total += test_rejeitar_gate2_nao_cria()
    total += test_prepara_distribuicao()
    total += test_gate3_pendente_e_endpoint()
    total += test_sem_integracao_externa()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
