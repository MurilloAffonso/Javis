"""Testes do Command Router — stdlib only, sem framework externo."""
import sys
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import command_router

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {description}")
    return condition


def test_seguros() -> int:
    print("\n--- Comandos seguros ---")
    failures = 0
    cases = [
        ("abre o youtube",       "abrir_youtube",   "low",      False),
        ("toca uma musica",      "tocar_musica",    "low",      False),
        ("abre o open webui",    "abrir_openwebui", "low",      False),
        ("status",               "status_sistema",  "low",      False),
        ("como vai voce",        "conversa",        "none",     False),
        ("abre a pasta do javis","abrir_javis",     "low",      False),
        ("abre o navegador",     "abrir_navegador", "low",      False),
        ("anota: tenho uma ideia","registrar_ideia","low",      False),
        ("abre o vscode",        "abrir_vscode",    "low",      False),
    ]
    for text, exp_intent, exp_risk, exp_approval in cases:
        r = command_router.route(text)
        ok = (r["intent"] == exp_intent
              and r["risk_level"] == exp_risk
              and r["requires_approval"] == exp_approval)
        if not ok:
            failures += 1
            print(f"    DETALHE: got intent={r['intent']} risk={r['risk_level']}")
        check(f"{text!r} → {exp_intent}", ok)
    return failures


def test_perigosos() -> int:
    print("\n--- Comandos perigosos (devem ser critical) ---")
    failures = 0
    cases = [
        "apaga meus arquivos",
        "apagar tudo",
        "deleta a pasta",
        "formata o disco",
        "rm -rf /",
        "del /f",
        "git push --force",
        "git reset --hard",
        "instala o python",
        "remove o docker",
        "drop table usuarios",
    ]
    for text in cases:
        r = command_router.route(text)
        ok = (r["intent"] == "acao_perigosa"
              and r["risk_level"] == "critical"
              and r["requires_approval"] is True
              and r["action"] == "blocked")
        if not ok:
            failures += 1
            print(f"    DETALHE: {text!r} → intent={r['intent']} risk={r['risk_level']}")
        check(f"{text!r} → acao_perigosa/critical/blocked", ok)
    return failures


def test_aprovacao_media() -> int:
    print("\n--- Comandos com aprovação média ---")
    failures = 0
    cases = [
        ("abre o terminal",     "abrir_terminal", "medium", True),
        ("abre o powershell",   "abrir_terminal", "medium", True),
        ("linha de comando",    "abrir_terminal", "medium", True),
    ]
    for text, exp_intent, exp_risk, exp_approval in cases:
        r = command_router.route(text)
        ok = (r["intent"] == exp_intent
              and r["risk_level"] == exp_risk
              and r["requires_approval"] == exp_approval)
        if not ok:
            failures += 1
        check(f"{text!r} → {exp_intent}/medium/approval=True", ok)
    return failures


def test_ambiguos() -> int:
    print("\n--- Comandos ambíguos (conversa ou desconhecido) ---")
    failures = 0
    cases = [
        ("ok",       ["desconhecido", "conversa"]),
        ("blz",      ["desconhecido"]),
        ("o que acha de criar um dashboard", ["conversa"]),
        ("me explica como funciona o ollama", ["conversa"]),
    ]
    for text, expected_intents in cases:
        r = command_router.route(text)
        ok = r["intent"] in expected_intents and r["risk_level"] in ("none",)
        if not ok:
            failures += 1
            print(f"    DETALHE: {text!r} → intent={r['intent']} risk={r['risk_level']}")
        check(f"{text!r} → {expected_intents}", ok)
    return failures


def test_status_natural() -> int:
    print("\n--- Status em linguagem natural ---")
    failures = 0
    cases = [
        "status",
        "status do sistema",
        "como está o sistema",
        "como tá o sistema",
        "como é que tá o sistema",
        "o sistema está ok",
        "tá tudo funcionando",
        "tudo funcionando",
    ]
    for text in cases:
        r = command_router.route(text)
        ok = (r["intent"] == "status_sistema"
              and r["risk_level"] == "low"
              and r["requires_approval"] is False)
        if not ok:
            failures += 1
            print(f"    DETALHE: {text!r} → intent={r['intent']}")
        check(f"{text!r} → status_sistema", ok)
    return failures


def test_com_wake_word_no_texto() -> int:
    print("\n--- Comandos com wake word no texto (router classifica pelo keyword) ---")
    failures = 0
    cases = [
        ("Javis, abre o youtube",           "abrir_youtube",   "low",      False),
        ("Javes, abre o open webui",         "abrir_openwebui", "low",      False),
        ("Diabes, toca Beethoven no youtube","abrir_youtube",   "low",      False),
        ("apaga meus arquivos",              "acao_perigosa",   "critical", True),
    ]
    for text, exp_intent, exp_risk, exp_approval in cases:
        r = command_router.route(text)
        ok = (r["intent"] == exp_intent
              and r["risk_level"] == exp_risk
              and r["requires_approval"] == exp_approval)
        if not ok:
            failures += 1
            print(f"    DETALHE: got intent={r['intent']} risk={r['risk_level']}")
        check(f"{text!r} → {exp_intent}", ok)
    return failures


def test_campos_obrigatorios() -> int:
    print("\n--- Campos obrigatórios no resultado ---")
    failures = 0
    r = command_router.route("abre o youtube")
    required = ["intent", "confidence", "risk_level", "requires_approval",
                "action", "reason", "original_text"]
    for field in required:
        ok = field in r
        if not ok:
            failures += 1
        check(f"campo '{field}' presente", ok)
    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: command_router.py")
    print("=" * 50)

    total_failures = 0
    total_failures += test_seguros()
    total_failures += test_perigosos()
    total_failures += test_aprovacao_media()
    total_failures += test_ambiguos()
    total_failures += test_status_natural()
    total_failures += test_com_wake_word_no_texto()
    total_failures += test_campos_obrigatorios()

    print("\n" + "=" * 50)
    if total_failures == 0:
        print(f"\033[32m✅ Todos os testes passaram.\033[0m")
    else:
        print(f"\033[31m❌ {total_failures} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total_failures)


if __name__ == "__main__":
    main()
