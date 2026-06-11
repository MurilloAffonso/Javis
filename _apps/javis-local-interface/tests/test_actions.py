"""Testes do módulo actions — verifica handlers sem side-effects reais."""
import sys
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {description}")
    return condition


def test_browser_handlers() -> int:
    print("\n--- Browser handlers: webbrowser.open chamado ---")
    import actions
    failures = 0
    browser_intents = ["abrir_youtube", "tocar_musica", "abrir_navegador", "abrir_openwebui"]
    with patch("webbrowser.open") as mock_open:
        for intent in browser_intents:
            mock_open.reset_mock()
            r = actions.execute(intent, "")
            ok = r["status"] == "ok" and mock_open.called
            if not ok:
                failures += 1
            check(f"{intent} → ok + webbrowser.open chamado", ok)
    return failures


def test_blocked_handler() -> int:
    print("\n--- acao_perigosa: sempre blocked ---")
    import actions
    failures = 0
    r = actions.execute("acao_perigosa", "")
    ok = r["status"] == "blocked"
    if not ok:
        failures += 1
    check("acao_perigosa → status=blocked", ok)
    return failures


def test_status_sistema() -> int:
    print("\n--- status_sistema: retorna ok com message ---")
    import actions
    failures = 0
    r = actions.execute("status_sistema", "")
    ok = r["status"] == "ok" and "message" in r and "serviços" in r["message"].lower()
    if not ok:
        failures += 1
        print(f"    DETALHE: {r}")
    check("status_sistema → ok + mensagem de status", ok)
    return failures


def test_llm_handlers() -> int:
    print("\n--- conversa/desconhecido/unknown: redirect llm ---")
    import actions
    failures = 0
    for intent in ["conversa", "desconhecido", "INTENT_INEXISTENTE"]:
        r = actions.execute(intent, "")
        ok = r["status"] == "llm"
        if not ok:
            failures += 1
        check(f"{intent!r} → status=llm", ok)
    return failures


def test_vscode_handler() -> int:
    print("\n--- abrir_vscode: sem shell=True, usa shutil.which ---")
    import actions
    failures = 0
    with patch("shutil.which", return_value="/fake/code") as _mock_which, \
         patch("subprocess.Popen") as mock_popen:
        r = actions.execute("abrir_vscode", "")
        ok_status = r["status"] == "ok"
        ok_called = mock_popen.called
        call_kwargs = mock_popen.call_args[1] if mock_popen.call_args else {}
        ok_no_shell = call_kwargs.get("shell", False) is False
        if not (ok_status and ok_called):
            failures += 1
        if not ok_no_shell:
            failures += 1
        check("abrir_vscode → ok + subprocess.Popen chamado", ok_status and ok_called)
        check("abrir_vscode → sem shell=True", ok_no_shell)
    return failures


def test_vscode_not_found() -> int:
    print("\n--- abrir_vscode: VS Code não encontrado no PATH ---")
    import actions
    failures = 0
    with patch("shutil.which", return_value=None):
        r = actions.execute("abrir_vscode", "")
        ok = r["status"] == "error"
        if not ok:
            failures += 1
        check("abrir_vscode sem VS Code → status=error", ok)
    return failures


def test_terminal_no_shell_uses_cwd() -> int:
    print("\n--- abrir_terminal: sem shell=True, usa cwd= ---")
    import actions
    failures = 0
    with patch("subprocess.Popen") as mock_popen:
        actions.execute("abrir_terminal", "")
        call_kwargs = mock_popen.call_args[1] if mock_popen.call_args else {}
        ok_no_shell = call_kwargs.get("shell", False) is False
        ok_has_cwd = "cwd" in call_kwargs
        if not ok_no_shell:
            failures += 1
        if not ok_has_cwd:
            failures += 1
        check("abrir_terminal: sem shell=True", ok_no_shell)
        check("abrir_terminal: usa cwd= (sem interpolação de path)", ok_has_cwd)
    return failures


def test_register_idea_validation() -> int:
    print("\n--- _register_idea: validações ---")
    import actions
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        original_root = actions.JAVIS_ROOT
        actions.JAVIS_ROOT = Path(tmpdir)
        try:
            # Texto vazio → error, sem arquivo criado
            r = actions.execute("registrar_ideia", "")
            ok = r["status"] == "error"
            if not ok:
                failures += 1
            check("texto vazio → status=error", ok)
            ok_no_file = len(list(Path(tmpdir).rglob("*.md"))) == 0
            if not ok_no_file:
                failures += 1
            check("texto vazio → nenhum arquivo criado", ok_no_file)

            # Texto só espaço → error, sem arquivo criado
            r = actions.execute("registrar_ideia", "   \n   ")
            ok = r["status"] == "error"
            if not ok:
                failures += 1
            check("texto só espaço → status=error", ok)
            ok_no_file2 = len(list(Path(tmpdir).rglob("*.md"))) == 0
            if not ok_no_file2:
                failures += 1
            check("texto só espaço → nenhum arquivo criado", ok_no_file2)

            # Texto longo > 2000 chars → truncado, arquivo criado
            long_text = "z" * 3000
            r = actions.execute("registrar_ideia", long_text)
            ok_status = r["status"] == "ok"
            if not ok_status:
                failures += 1
            check("texto 3000 chars → status=ok (truncado)", ok_status)

            files = list(Path(tmpdir).rglob("*.md"))
            ok_created = len(files) == 1
            if not ok_created:
                failures += 1
            check("texto 3000 chars → arquivo criado", ok_created)

            if ok_created:
                content = files[0].read_text(encoding="utf-8")
                z_count = content.count("z")
                ok_truncated = z_count <= 2000
                if not ok_truncated:
                    failures += 1
                check(f"conteúdo truncado a ≤2000 z's (tem {z_count})", ok_truncated)

            # Texto normal → ok
            r = actions.execute("registrar_ideia", "Ideia de teste válida")
            ok = r["status"] == "ok"
            if not ok:
                failures += 1
            check("texto válido → status=ok", ok)

        finally:
            actions.JAVIS_ROOT = original_root

    return failures


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 50)
    print("Testes: actions.py")
    print("=" * 50)

    total_failures = 0
    total_failures += test_browser_handlers()
    total_failures += test_blocked_handler()
    total_failures += test_status_sistema()
    total_failures += test_llm_handlers()
    total_failures += test_vscode_handler()
    total_failures += test_vscode_not_found()
    total_failures += test_terminal_no_shell_uses_cwd()
    total_failures += test_register_idea_validation()

    print("\n" + "=" * 50)
    if total_failures == 0:
        print("\033[32m✅ Todos os testes passaram.\033[0m")
    else:
        print(f"\033[31m❌ {total_failures} teste(s) falharam.\033[0m")
    print("=" * 50)
    sys.exit(total_failures)


if __name__ == "__main__":
    main()
