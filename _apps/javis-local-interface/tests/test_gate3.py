"""Testes do Gate 3 (final): pacote de publicação MANUAL + fim da campanha.
Cobre: aprovar gera pacote-publicacao-semana.md + manual_publication_package_created
+ conclui a task (completed) + digest; rejeitar não gera; idempotência; sem
integração externa.
"""
import sys
import io
import inspect
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

_DIST = "vp-distribuicao-preparar"
_GATE3_AP = {"id": 60, "agent": "midas", "task_id": _DIST,
             "subject": "Aprovar distribuição antes de publicar"}


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
    return distribution.PACOTE.read_text(encoding="utf-8") if distribution.PACOTE.exists() else None


def _restore(bkp):
    import distribution
    if bkp is not None:
        distribution.PACOTE.write_text(bkp, encoding="utf-8")
    elif distribution.PACOTE.exists():
        os.remove(distribution.PACOTE)


def _seed_dist(status="in_progress"):
    import repositories as repo
    repo.tasks.upsert(_DIST, "[Distribuição] Preparar pacote de publicação da pauta aprovada",
                      status=status, mission="pipeline-marketing-vem-passear-jampa", agent="midas")
    return _DIST


def test_aprovar_gate3_gera_pacote_e_eventos() -> int:
    print("\n--- Aprovar Gate 3 gera pacote + eventos ---")
    _fresh_db()
    import repositories as repo, approval_effects, distribution
    failures = 0
    bkp = _backup()
    _seed_dist()
    try:
        res = approval_effects.on_decided(dict(_GATE3_AP), True)
        if not check("avançou + completou", res.get("advanced") is True and res.get("completed") is True):
            failures += 1
        if not check("pacote-publicacao-semana.md existe", distribution.PACOTE.exists()):
            failures += 1
        txt = distribution.PACOTE.read_text(encoding="utf-8")
        if not check("aviso PUBLICAÇÃO MANUAL no arquivo", "PUBLICAÇÃO MANUAL" in txt):
            failures += 1
        if not check("tem checklist manual", "Checklist manual antes de publicar" in txt):
            failures += 1
        if not check("tem [CONFIRMAR COM MURILLO]", "[CONFIRMAR COM MURILLO" in txt):
            failures += 1
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_DIST)]
        for et in ["approval_approved", "file_generated", "manual_publication_package_created"]:
            if not check(f"evento '{et}'", et in tipos):
                failures += 1
    finally:
        _restore(bkp)
    return failures


def test_aprovar_gate3_conclui_e_digest() -> int:
    print("\n--- Aprovar Gate 3 conclui a task + digest (lifecycle) ---")
    _fresh_db()
    import repositories as repo, approval_effects, distribution
    failures = 0
    bkp = _backup()
    _seed_dist()
    try:
        approval_effects.on_decided(dict(_GATE3_AP), True)
        t = repo.tasks.get_task(_DIST)
        if not check("task de Distribuição completed", t["status"] == "completed"):
            failures += 1
        if not check("completed_at preenchido", bool(t["completed_at"])):
            failures += 1
        if not check("digest gerado e salvo", bool((t["digest_text"] or "").strip())):
            failures += 1
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_DIST)]
        for et in ["entity_killed", "ai_digest_created"]:
            if not check(f"evento '{et}' (lifecycle)", et in tipos):
                failures += 1
    finally:
        _restore(bkp)
    return failures


def test_rejeitar_gate3_nao_gera() -> int:
    print("\n--- Rejeitar Gate 3 NÃO gera pacote final ---")
    _fresh_db()
    import repositories as repo, approval_effects, distribution
    failures = 0
    bkp = _backup()
    if distribution.PACOTE.exists():
        os.remove(distribution.PACOTE)
    _seed_dist()
    try:
        res = approval_effects.on_decided(dict(_GATE3_AP), False)
        if not check("não avançou", res.get("advanced") is False):
            failures += 1
        if not check("NÃO gerou pacote", not distribution.PACOTE.exists()):
            failures += 1
        if not check("Distribuição volta pra pending", repo.tasks.get_task(_DIST)["status"] == "pending"):
            failures += 1
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(_DIST)]
        if not check("evento approval_rejected", "approval_rejected" in tipos):
            failures += 1
    finally:
        _restore(bkp)
    return failures


def test_idempotente() -> int:
    print("\n--- Não duplica pacote/conclusão se rodar de novo ---")
    _fresh_db()
    import approval_effects
    failures = 0
    bkp = _backup()
    _seed_dist()
    try:
        approval_effects.on_decided(dict(_GATE3_AP), True)
        res2 = approval_effects.on_decided(dict(_GATE3_AP), True)
        if not check("2ª vez detecta 'already'", res2.get("already") is True):
            failures += 1
    finally:
        _restore(bkp)
    return failures


def test_sem_integracao_externa() -> int:
    print("\n--- Gate 3 NÃO publica nem chama integração externa ---")
    import approval_effects, distribution
    failures = 0
    src = (inspect.getsource(approval_effects._advance_gate3)
           + inspect.getsource(distribution.gerar_pacote_publicacao_manual_vp)
           + inspect.getsource(distribution._template_pacote_manual)).lower()
    proibidos = ["whatsapp_send", "import integrations", "integrations.", "gmail_send",
                 "instagram_api", "sheets.", "telegram_bridge", "requests.get", "requests.post",
                 "imagedraw", "from pil", ".publish(", "publicar_post", "graph.facebook"]
    achou = [p for p in proibidos if p in src]
    if not check(f"sem integração/publicação (achados: {achou})", not achou):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: Gate 3 → pacote manual + fim da campanha")
    print("=" * 50)
    total = 0
    total += test_aprovar_gate3_gera_pacote_e_eventos()
    total += test_aprovar_gate3_conclui_e_digest()
    total += test_rejeitar_gate3_nao_gera()
    total += test_idempotente()
    total += test_sem_integracao_externa()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
