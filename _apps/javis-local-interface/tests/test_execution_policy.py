"""R4.1 — execution_policy default-deny (funções puras, nada executado)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution import execution_policy as pol  # noqa: E402


@pytest.fixture
def wt(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    return tmp_path


def _ok(argv, wt):
    return pol.check_command(argv, wt).allowed


# ── permitidos ─────────────────────────────────────────────────────────────
def test_git_status_permitido(wt):
    assert _ok(["git", "status"], wt)


def test_git_diff_permitido(wt):
    assert _ok(["git", "diff"], wt)
    assert _ok(["git", "diff", "--stat"], wt)


def test_py_compile_dentro_da_worktree(wt):
    assert _ok(["python", "-m", "py_compile", str(wt / "a.py")], wt)


def test_pytest_declarado(wt):
    assert _ok(["python", "-m", "pytest", "tests/test_x.py"], wt)
    assert _ok(["pytest", "tests/test_x.py::test_x"], wt)


def test_git_add_arquivo_explicito(wt):
    assert _ok(["git", "add", "a.py"], wt)


def test_git_log_com_limite(wt):
    assert _ok(["git", "log", "-n", "5"], wt)
    assert not _ok(["git", "log"], wt)  # sem limite → nega


# ── bloqueados ─────────────────────────────────────────────────────────────
def test_git_push_bloqueado(wt):
    assert not _ok(["git", "push"], wt)
    assert not _ok(["git", "push", "--force"], wt)


def test_git_reset_clean_bloqueados(wt):
    assert not _ok(["git", "reset", "--hard"], wt)
    assert not _ok(["git", "clean", "-fd"], wt)
    assert not _ok(["git", "checkout", "master"], wt)


def test_instalacao_dependencia_bloqueada(wt):
    assert not _ok(["python", "-m", "pip", "install", "requests"], wt)
    assert not _ok(["pip", "install", "requests"], wt)
    assert not _ok(["npm", "install"], wt)


def test_rede_bloqueada(wt):
    for cmd in (["curl", "http://x"], ["wget", "http://x"], ["ssh", "host"], ["nc", "h", "80"]):
        assert not _ok(cmd, wt)


def test_leitura_env_bloqueada(wt):
    assert not _ok(["git", "add", ".env"], wt)
    assert not pol.validate_path(".env", wt).allowed
    assert not pol.validate_path("secrets/token.txt", wt).allowed


def test_path_fora_da_worktree_bloqueado(wt):
    fora = str(wt.parent / "outro.py")
    assert not _ok(["python", "-m", "py_compile", fora], wt)
    assert not pol.validate_path("../fora.py", wt).allowed


def test_comando_desconhecido_bloqueado(wt):
    assert not _ok(["rm", "-rf", "/"], wt)
    assert not _ok(["powershell", "Invoke-WebRequest"], wt)
    assert not _ok([], wt)


def test_encadeamento_bloqueado(wt):
    assert not _ok(["git", "status; rm -rf /"], wt)
    assert not _ok(["git", "status", "&&", "git", "push"], wt)
    assert not _ok(["python", "-m", "pytest", "x || curl http://x"], wt)


def test_git_add_amplo_bloqueado(wt):
    assert not _ok(["git", "add", "."], wt)
    assert not _ok(["git", "add", "-A"], wt)


def test_explain_denial_sanitiza(wt):
    # não deve vazar segredo mesmo se o comando trouxer um
    reason = pol.explain_denial(["curl", "https://x?api_key=sk-secret-123456"], wt)
    assert reason and "sk-secret-123456" not in reason
