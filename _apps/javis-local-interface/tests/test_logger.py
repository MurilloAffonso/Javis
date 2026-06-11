"""Testes do módulo logger — rotação diária, campos mínimos, preservação de logs antigos."""
import sys
import io
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {description}")
    return condition


def _sample_route(intent: str = "abrir_youtube") -> dict:
    return {
        "intent": intent, "confidence": 0.9, "risk_level": "low",
        "requires_approval": False, "action": "open_youtube",
        "reason": "keyword match", "original_text": "abre o youtube",
    }


def _sample_action_result(status: str = "dry_run_only") -> dict:
    return {"status": status, "message": "teste"}


def test_rotacao_diaria() -> int:
    print("\n--- Rotação diária: arquivo actions-YYYY-MM-DD.jsonl criado ---")
    import logger
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        original = logger.LOGS_DIR
        logger.LOGS_DIR = Path(tmpdir)
        try:
            logger.log(
                source="voice",
                user_text="abre o youtube",
                route=_sample_route(),
                action_result=_sample_action_result(),
                approved=False,
                duration_ms=5,
                extra={"clean_transcript": "abre o youtube", "dry_run": True,
                       "would_execute": True, "note": "seguro"},
            )
            files = list(Path(tmpdir).glob("actions-*.jsonl"))
            ok_count = len(files) == 1
            if not ok_count:
                failures += 1
            check(f"arquivo actions-*.jsonl criado (encontrados: {len(files)})", ok_count)

            if ok_count:
                name = files[0].name
                # Verifica formato YYYY-MM-DD
                date_part = name.replace("actions-", "").replace(".jsonl", "")
                try:
                    datetime.strptime(date_part, "%Y-%m-%d")
                    ok_date = True
                except ValueError:
                    ok_date = False
                if not ok_date:
                    failures += 1
                check(f"nome no formato actions-YYYY-MM-DD.jsonl ({name})", ok_date)

            # Garante que NÃO existe actions.jsonl (nome antigo)
            old_file = Path(tmpdir) / "actions.jsonl"
            ok_no_old = not old_file.exists()
            if not ok_no_old:
                failures += 1
            check("arquivo actions.jsonl (nome antigo) NÃO criado", ok_no_old)

        finally:
            logger.LOGS_DIR = original

    return failures


def test_json_valido() -> int:
    print("\n--- Linha gravada é JSON válido ---")
    import logger
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        original = logger.LOGS_DIR
        logger.LOGS_DIR = Path(tmpdir)
        try:
            logger.log(
                source="voice",
                user_text="status",
                route=_sample_route("status_sistema"),
                action_result=_sample_action_result(),
                approved=False,
                duration_ms=3,
                extra={"clean_transcript": "status", "dry_run": True,
                       "would_execute": True, "note": "seguro"},
            )
            files = list(Path(tmpdir).glob("actions-*.jsonl"))
            if not files:
                failures += 1
                check("arquivo existe para verificar JSON", False)
                return failures

            lines = files[0].read_text(encoding="utf-8").strip().splitlines()
            ok_one_line = len(lines) == 1
            if not ok_one_line:
                failures += 1
            check(f"exatamente 1 linha gravada ({len(lines)})", ok_one_line)

            try:
                record = json.loads(lines[0])
                ok_json = True
            except json.JSONDecodeError as e:
                ok_json = False
                print(f"    DETALHE: {e}")
            if not ok_json:
                failures += 1
            check("linha é JSON válido", ok_json)

        finally:
            logger.LOGS_DIR = original

    return failures


def test_campos_minimos() -> int:
    print("\n--- Campos mínimos no registro ---")
    import logger
    failures = 0

    required_fields = [
        "timestamp", "source", "user_text", "normalized_text",
        "intent", "confidence", "risk_level", "requires_approval",
        "approved", "dry_run", "would_execute", "note",
        "action_result", "latency_ms",
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        original = logger.LOGS_DIR
        logger.LOGS_DIR = Path(tmpdir)
        try:
            logger.log(
                source="voice",
                user_text="Javis, abre o youtube",
                route=_sample_route("abrir_youtube"),
                action_result=_sample_action_result("dry_run_only"),
                approved=False,
                duration_ms=7,
                extra={
                    "clean_transcript": "abre o youtube",
                    "dry_run": True,
                    "would_execute": True,
                    "note": "seguro — executaria via actions.execute()",
                    "transcript": "Javis, abre o youtube",
                },
            )
            files = list(Path(tmpdir).glob("actions-*.jsonl"))
            if not files:
                failures += len(required_fields)
                for f in required_fields:
                    check(f"campo '{f}' presente", False)
                return failures

            record = json.loads(files[0].read_text(encoding="utf-8").strip())
            for field in required_fields:
                ok = field in record
                if not ok:
                    failures += 1
                    print(f"    DETALHE: campo ausente: {field!r}")
                check(f"campo '{field}' presente", ok)

            # Verificar valores específicos
            checks = [
                ("source == 'voice'",     record.get("source") == "voice"),
                ("dry_run == True",        record.get("dry_run") is True),
                ("would_execute == True",  record.get("would_execute") is True),
                ("normalized_text correto", record.get("normalized_text") == "abre o youtube"),
                ("note presente",          record.get("note") is not None),
                ("latency_ms == 7",        record.get("latency_ms") == 7),
                ("confidence == 0.9",      record.get("confidence") == 0.9),
            ]
            for desc, cond in checks:
                if not cond:
                    failures += 1
                    print(f"    DETALHE: falhou: {desc} → {record.get(desc.split('==')[0].strip())!r}")
                check(desc, cond)

        finally:
            logger.LOGS_DIR = original

    return failures


def test_logs_antigos_preservados() -> int:
    print("\n--- Logs antigos não são apagados ---")
    import logger
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        original = logger.LOGS_DIR
        logger.LOGS_DIR = Path(tmpdir)
        try:
            # Simula log de dia anterior (2000-01-01)
            old_log = Path(tmpdir) / "actions-2000-01-01.jsonl"
            old_log.write_text('{"timestamp":"2000-01-01T00:00:00+00:00","source":"test"}\n',
                               encoding="utf-8")

            # Grava novo log (hoje)
            logger.log(
                source="voice",
                user_text="status",
                route=_sample_route("status_sistema"),
                action_result=_sample_action_result(),
                approved=False,
                duration_ms=2,
                extra={"clean_transcript": "status", "dry_run": True,
                       "would_execute": True, "note": "seguro"},
            )

            # Log antigo deve ainda existir
            ok_old = old_log.exists()
            if not ok_old:
                failures += 1
            check("log antigo (2000-01-01) preservado após novo log", ok_old)

            # Log de hoje também deve existir
            today_files = [f for f in Path(tmpdir).glob("actions-*.jsonl")
                          if "2000-01-01" not in f.name]
            ok_today = len(today_files) == 1
            if not ok_today:
                failures += 1
            check("novo log do dia criado separadamente", ok_today)

            # Total: 2 arquivos
            all_files = list(Path(tmpdir).glob("actions-*.jsonl"))
            ok_count = len(all_files) == 2
            if not ok_count:
                failures += 1
            check(f"total de 2 arquivos no diretório ({len(all_files)} encontrados)", ok_count)

        finally:
            logger.LOGS_DIR = original

    return failures


def test_multiples_eventos_mesmo_dia() -> int:
    print("\n--- Múltiplos eventos no mesmo dia → mesmo arquivo, linhas acumuladas ---")
    import logger
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        original = logger.LOGS_DIR
        logger.LOGS_DIR = Path(tmpdir)
        try:
            for intent in ["abrir_youtube", "status_sistema", "acao_perigosa"]:
                logger.log(
                    source="voice",
                    user_text=f"teste {intent}",
                    route=_sample_route(intent),
                    action_result=_sample_action_result(),
                    approved=False,
                    duration_ms=1,
                    extra={"clean_transcript": intent, "dry_run": True,
                           "would_execute": True, "note": "teste"},
                )

            files = list(Path(tmpdir).glob("actions-*.jsonl"))
            ok_one_file = len(files) == 1
            if not ok_one_file:
                failures += 1
            check(f"3 eventos → 1 arquivo ({len(files)} encontrados)", ok_one_file)

            if ok_one_file:
                lines = files[0].read_text(encoding="utf-8").strip().splitlines()
                ok_lines = len(lines) == 3
                if not ok_lines:
                    failures += 1
                check(f"3 linhas no arquivo ({len(lines)} encontradas)", ok_lines)

        finally:
            logger.LOGS_DIR = original

    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: logger.py")
    print("=" * 50)

    total_failures = 0
    total_failures += test_rotacao_diaria()
    total_failures += test_json_valido()
    total_failures += test_campos_minimos()
    total_failures += test_logs_antigos_preservados()
    total_failures += test_multiples_eventos_mesmo_dia()

    print("\n" + "=" * 50)
    if total_failures == 0:
        print("\033[32m✅ Todos os testes passaram.\033[0m")
    else:
        print(f"\033[31m❌ {total_failures} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total_failures)


if __name__ == "__main__":
    main()
