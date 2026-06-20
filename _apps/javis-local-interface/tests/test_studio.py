"""Testes do Estúdio em modo seguro: gera criativos-semana.md, registra Journey
Log (agent_called/file_generated/approval_requested), cria Gate 2, idempotência e
ausência de integração externa.
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


def _seed_design():
    import repositories as repo, studio
    repo.tasks.upsert(studio._DESIGN_TASK, "[Design] Produzir os criativos da pauta aprovada",
                      status="pending", mission="pipeline-marketing-vem-passear-jampa")
    return studio._DESIGN_TASK


def _backup_criativos():
    import studio
    return studio.CRIATIVOS.read_text(encoding="utf-8") if studio.CRIATIVOS.exists() else None


def _restore_criativos(bkp):
    import studio
    if bkp is not None:
        studio.CRIATIVOS.write_text(bkp, encoding="utf-8")
    elif studio.CRIATIVOS.exists():
        os.remove(studio.CRIATIVOS)


def test_gera_arquivo_e_eventos() -> int:
    print("\n--- Roda Estúdio: gera criativos-semana.md + eventos ---")
    _fresh_db()
    import repositories as repo, studio
    failures = 0
    bkp = _backup_criativos()
    tid = _seed_design()
    try:
        res = studio.run_studio(tid)
        if not check("run_studio ok", res.get("ok") is True):
            failures += 1
        if not check("arquivo criativos-semana.md existe", studio.CRIATIVOS.exists()):
            failures += 1
        conteudo = studio.CRIATIVOS.read_text(encoding="utf-8")
        if not check("conteúdo tem 'Criativos da Semana'", "Criativos da Semana" in conteudo):
            failures += 1
        if not check("tem marcador [CONFIRMAR COM MURILLO]", "[CONFIRMAR COM MURILLO" in conteudo):
            failures += 1
        if not check("tem Status Gate 2", "Gate 2" in conteudo):
            failures += 1
        tipos = [e["event_type"] for e in repo.task_events.list_by_task(tid)]
        for et in ["agent_called", "file_generated", "approval_requested"]:
            if not check(f"evento '{et}' registrado", et in tipos):
                failures += 1
        if not check("task ficou in_progress", repo.tasks.get_task(tid)["status"] == "in_progress"):
            failures += 1
    finally:
        _restore_criativos(bkp)
    return failures


def test_cria_gate2_pendente() -> int:
    print("\n--- Cria Gate 2 pendente e aparece em /approvals/pending ---")
    _fresh_db()
    import repositories as repo, studio, server
    failures = 0
    bkp = _backup_criativos()
    tid = _seed_design()
    try:
        studio.run_studio(tid)
        g2 = next((a for a in repo.approvals.pending()
                   if a["subject"] == "Aprovar criativos da semana antes de publicar"), None)
        if not check("Gate 2 pendente existe", g2 is not None):
            failures += 1
        if not check("Gate 2 agent=estudio", bool(g2) and g2["agent"] == "estudio"):
            failures += 1
        if not check("Gate 2 task_id = task de Design", bool(g2) and g2["task_id"] == tid):
            failures += 1
        # endpoint /approvals/pending
        resp = asyncio.run(server.approvals_pending())
        body = json.loads(bytes(resp.body))
        achou = any(a["subject"].startswith("Aprovar criativos") for a in body["approvals"])
        if not check("Gate 2 aparece no endpoint /approvals/pending", achou):
            failures += 1
    finally:
        _restore_criativos(bkp)
    return failures


def test_idempotente() -> int:
    print("\n--- Não duplica Gate 2 se rodar 2x ---")
    _fresh_db()
    import repositories as repo, studio
    failures = 0
    bkp = _backup_criativos()
    tid = _seed_design()
    try:
        studio.run_studio(tid)
        res2 = studio.run_studio(tid)
        if not check("2ª execução recusada (already)", res2.get("already") is True):
            failures += 1
        n = len([a for a in repo.approvals.by_task(tid)
                 if a["subject"] == "Aprovar criativos da semana antes de publicar"])
        if not check(f"apenas 1 Gate 2 ({n})", n == 1):
            failures += 1
    finally:
        _restore_criativos(bkp)
    return failures


def test_so_task_de_design() -> int:
    print("\n--- Recusa task que não é de Design ---")
    _fresh_db()
    import repositories as repo, studio
    failures = 0
    repo.tasks.upsert("qualquer-1", "[Conteúdo] outra coisa", status="pending", mission="wf")
    res = studio.run_studio("qualquer-1")
    if not check("recusou task não-Design", res.get("ok") is False):
        failures += 1
    return failures


def test_sem_integracao_externa() -> int:
    print("\n--- Estúdio NÃO chama integração externa nem gera imagem ---")
    import studio
    failures = 0
    src = (inspect.getsource(studio.run_studio) + inspect.getsource(studio.gerar_criativos_vp)
           + inspect.getsource(studio._template_criativos)).lower()
    # tokens de CHAMADA/IMPORT (não palavras soltas — "imagem" PT no briefing é ok)
    proibidos = ["whatsapp_send", "import integrations", "integrations.", "gmail", "instagram",
                 "sheets.", "telegram_bridge", "requests.get", "requests.post",
                 "imagedraw", "from pil", "import pil", "pillow", "dall-e", "dalle",
                 "stable-diffusion", "generate_image", "create_image", ".publish("]
    achou = [p for p in proibidos if p in src]
    if not check(f"sem integração/geração de imagem (achados: {achou})", not achou):
        failures += 1
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: Estúdio em modo seguro + Gate 2")
    print("=" * 50)
    total = 0
    total += test_gera_arquivo_e_eventos()
    total += test_cria_gate2_pendente()
    total += test_idempotente()
    total += test_so_task_de_design()
    total += test_sem_integracao_externa()
    print("\n" + "=" * 50)
    print("\033[32m✅ Todos os testes passaram.\033[0m" if total == 0
          else f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total)


if __name__ == "__main__":
    main()
