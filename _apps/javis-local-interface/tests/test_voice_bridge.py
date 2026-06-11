"""Testes do Voice Bridge — verifica dry-run, classificação e logging."""
import sys
import io
import json
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {description}")
    return condition


def test_dry_run_sempre_ativo() -> int:
    print("\n--- dry_run sempre True ---")
    import voice_bridge
    failures = 0
    for text in ["abre o youtube", "status", "apaga meus arquivos", "abre o terminal"]:
        r = voice_bridge.classify_voice(text)
        ok = r["dry_run"] is True
        if not ok:
            failures += 1
        check(f"{text!r} → dry_run=True", ok)
    return failures


def test_source_voice() -> int:
    print("\n--- source sempre 'voice' ---")
    import voice_bridge
    failures = 0
    for text in ["abre o youtube", "status"]:
        r = voice_bridge.classify_voice(text)
        ok = r["source"] == "voice"
        if not ok:
            failures += 1
        check(f"{text!r} → source='voice'", ok)
    return failures


def test_perigoso_nao_executa() -> int:
    print("\n--- Comandos perigosos: would_execute=False ---")
    import voice_bridge
    failures = 0
    cases = ["apaga meus arquivos", "rm -rf /", "git push --force",
             "deleta tudo", "formata o disco"]
    for text in cases:
        r = voice_bridge.classify_voice(text)
        ok = (r["would_execute"] is False
              and r["intent"] == "acao_perigosa"
              and r["risk_level"] == "critical")
        if not ok:
            failures += 1
            print(f"    DETALHE: would_execute={r['would_execute']} intent={r['intent']}")
        check(f"{text!r} → would_execute=False, critical", ok)
    return failures


def test_seguros_marcados_would_execute() -> int:
    print("\n--- Comandos seguros: would_execute=True ---")
    import voice_bridge
    failures = 0
    cases = [
        "abre o youtube",
        "toca musica",
        "status do sistema",
        "abre o open webui",
    ]
    for text in cases:
        r = voice_bridge.classify_voice(text)
        ok = r["would_execute"] is True and r["dry_run"] is True
        if not ok:
            failures += 1
            print(f"    DETALHE: would_execute={r['would_execute']}")
        check(f"{text!r} → would_execute=True (mas dry_run=True)", ok)
    return failures


def test_terminal_nao_executa_por_voz() -> int:
    print("\n--- abrir_terminal: never would_execute por voz ---")
    import voice_bridge
    failures = 0
    r = voice_bridge.classify_voice("abre o terminal")
    ok = r["would_execute"] is False
    if not ok:
        failures += 1
    check("'abre o terminal' → would_execute=False por voz", ok)
    return failures


def test_campos_obrigatorios() -> int:
    print("\n--- Campos obrigatórios na resposta ---")
    import voice_bridge
    failures = 0
    r = voice_bridge.classify_voice("abre o youtube")
    required = ["source", "transcript", "intent", "confidence",
                "risk_level", "requires_approval", "action",
                "dry_run", "would_execute", "reason", "note"]
    for field in required:
        ok = field in r
        if not ok:
            failures += 1
        check(f"campo '{field}' presente", ok)
    return failures


def test_strip_wake_word() -> int:
    print("\n--- _strip_wake_word remove saudação + wake word ---")
    import voice_bridge
    failures = 0
    cases = [
        ("Javis, abre o youtube",                    "abre o youtube"),
        ("Jarvis abre o open webui",                 "abre o open webui"),
        ("javes,  status do sistema",                "status do sistema"),
        ("diabes, toca musica",                      "toca musica"),
        ("diaves toca beethoven no youtube",         "toca beethoven no youtube"),
        ("chaves, status",                           "status"),
        ("Olá Javes, como é que tá o sistema?",      "como é que tá o sistema?"),
        ("Oi Javis, status",                         "status"),
        ("olá javis como tá o sistema",              "como tá o sistema"),
        ("abre o youtube",                           "abre o youtube"),   # sem prefixo — inalterado
        ("apaga meus arquivos",                      "apaga meus arquivos"),
    ]
    for original, expected in cases:
        got = voice_bridge._strip_wake_word(original)
        ok = got == expected
        if not ok:
            failures += 1
            print(f"    DETALHE: {original!r} → {got!r} (esperado {expected!r})")
        check(f"strip({original!r}) == {expected!r}", ok)
    return failures


def test_wake_word_classifica_intent() -> int:
    print("\n--- Os 6 casos especificados + saudação + youtube curto ---")
    import voice_bridge
    failures = 0
    cases = [
        # (texto, intent esperado, risk, would_execute)
        ("Olá Javes, como é que tá o sistema?",  "status_sistema",  "low",      True),
        ("Javis, como tá o sistema?",             "status_sistema",  "low",      True),
        ("status",                                "status_sistema",  "low",      True),
        ("tá tudo funcionando?",                  "status_sistema",  "low",      True),
        ("YouTube.",                              "abrir_youtube",   "low",      True),
        ("apaga meus arquivos",                   "acao_perigosa",   "critical", False),
        # casos extras
        ("Javis, abre o youtube",                 "abrir_youtube",   "low",      True),
        ("Javes, abre o open webui",              "abrir_openwebui", "low",      True),
        ("Diabes, toca Beethoven no youtube",     "abrir_youtube",   "low",      True),
    ]
    for text, exp_intent, exp_risk, exp_would_execute in cases:
        r = voice_bridge.classify_voice(text)
        ok = (r["intent"] == exp_intent
              and r["risk_level"] == exp_risk
              and r["dry_run"] is True
              and r["would_execute"] == exp_would_execute)
        if not ok:
            failures += 1
            print(f"    DETALHE: {text!r} → intent={r['intent']} risk={r['risk_level']} would_execute={r['would_execute']}")
        check(f"{text!r} → {exp_intent}/dry_run=True", ok)
    return failures


def test_log_gerado() -> int:
    print("\n--- Log JSONL gerado corretamente ---")
    import logger
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        original = logger.LOGS_DIR
        logger.LOGS_DIR = Path(tmpdir)
        try:
            import command_router
            route = command_router.route("abre o youtube")
            logger.log(
                source="voice",
                user_text="abre o youtube",
                route=route,
                action_result={"status": "dry_run_only", "message": "teste"},
                approved=False,
                duration_ms=10,
                extra={"dry_run": True, "would_execute": True},
            )
            log_files = list(Path(tmpdir).glob("actions-*.jsonl"))
            ok_exists = len(log_files) == 1
            check("log file criado (actions-YYYY-MM-DD.jsonl)", ok_exists)
            if ok_exists:
                log_file = log_files[0]
                lines = log_file.read_text(encoding="utf-8").strip().splitlines()
                ok_lines = len(lines) == 1
                check("exatamente 1 linha no log", ok_lines)
                if not ok_lines:
                    failures += 1
                else:
                    record = json.loads(lines[0])
                    checks = [
                        ("source == 'voice'", record.get("source") == "voice"),
                        ("dry_run == True",   record.get("dry_run") is True),
                        ("approved == False", record.get("approved") is False),
                        ("action_result == 'dry_run_only'", record.get("action_result") == "dry_run_only"),
                        ("timestamp presente", "timestamp" in record),
                    ]
                    for desc, cond in checks:
                        if not cond:
                            failures += 1
                        check(desc, cond)
        finally:
            logger.LOGS_DIR = original

    return failures


def test_hallucination_filter() -> int:
    print("\n--- Filtro anti-hallucination ---")
    import voice_bridge
    failures = 0

    # Transcrições que parecem hallucination do prompt — devem ser bloqueadas
    hallucination_cases = [
        "Javis, Javis, YouTube, status, sistema, open webui, abre, toca, vscode, terminal, status do sistema.",
        "Javis, Javes, Jarvis, YouTube, status, sistema, open webui, abre, toca, vscode, terminal, status do sistema.",
        "YouTube, status, sistema, webui, vscode, terminal, navegador",
    ]
    for text in hallucination_cases:
        r = voice_bridge.classify_voice(text)
        ok = (
            r["intent"] == "desconhecido"
            and r["would_execute"] is False
            and r["dry_run"] is True
            and r.get("note") == "blocked_hallucination"
        )
        if not ok:
            failures += 1
            print(f"    DETALHE: {text[:50]!r} → intent={r['intent']} note={r.get('note')}")
        check(f"hallucination bloqueada: {text[:45]!r}", ok)

    # Frases legítimas NÃO devem ser filtradas
    legit_cases = [
        ("Javis, abre o YouTube",       "abrir_youtube"),
        ("YouTube",                     "abrir_youtube"),
        ("Javis, como tá o sistema?",   "status_sistema"),
        ("apaga meus arquivos",         "acao_perigosa"),
        ("status",                      "status_sistema"),
    ]
    for text, exp_intent in legit_cases:
        r = voice_bridge.classify_voice(text)
        ok = r["intent"] == exp_intent and r.get("note") != "blocked_hallucination"
        if not ok:
            failures += 1
            print(f"    DETALHE: {text!r} → intent={r['intent']} note={r.get('note')}")
        check(f"legítima não filtrada: {text!r} → {exp_intent}", ok)

    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: voice_bridge.py + logger.py")
    print("=" * 50)

    total_failures = 0
    total_failures += test_dry_run_sempre_ativo()
    total_failures += test_source_voice()
    total_failures += test_perigoso_nao_executa()
    total_failures += test_seguros_marcados_would_execute()
    total_failures += test_terminal_nao_executa_por_voz()
    total_failures += test_campos_obrigatorios()
    total_failures += test_strip_wake_word()
    total_failures += test_wake_word_classifica_intent()
    total_failures += test_log_gerado()
    total_failures += test_hallucination_filter()

    print("\n" + "=" * 50)
    if total_failures == 0:
        print(f"\033[32m✅ Todos os testes passaram.\033[0m")
    else:
        print(f"\033[31m❌ {total_failures} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total_failures)


if __name__ == "__main__":
    main()
