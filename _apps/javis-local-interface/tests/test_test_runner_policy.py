from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution import process_utils  # noqa: E402
from execution.test_runner import TestRunner  # noqa: E402


def _runner(argv, **kwargs):
    return process_utils.ProcessResult(0, "success", "ok", "", False, 1, " ".join(argv))


def test_py_compile_explicito_permitido(tmp_path):
    target = tmp_path / "a.py"
    target.write_text("x = 1\n", encoding="utf-8")
    report = TestRunner(runner=_runner).run([["python", "-m", "py_compile", "a.py"]], tmp_path)
    assert report.ok is True


def test_pytest_sem_alvo_explicito_bloqueado(tmp_path):
    report = TestRunner(runner=_runner).run([["python", "-m", "pytest", "-q"]], tmp_path)
    assert report.ok is False
    assert report.results[0].status == "blocked"


def test_comando_fora_da_policy_bloqueado(tmp_path):
    report = TestRunner(runner=_runner).run([["python", "-m", "pip", "install", "x"]], tmp_path)
    assert report.ok is False
    assert report.results[0].status == "blocked"


def test_teste_fora_da_worktree_bloqueado(tmp_path):
    outside = tmp_path.parent / "outside_test.py"
    outside.write_text("def test_x(): pass\n", encoding="utf-8")
    report = TestRunner(runner=_runner).run(
        [["python", "-m", "py_compile", str(outside)]],
        tmp_path,
    )
    assert report.ok is False
    assert "fora" in report.results[0].stderr


def test_pytest_flag_arbitraria_bloqueada(tmp_path):
    target = tmp_path / "test_x.py"
    target.write_text("def test_x(): pass\n", encoding="utf-8")
    report = TestRunner(runner=_runner).run(
        [["python", "-m", "pytest", "-q", "--maxfail=1", "test_x.py"]],
        tmp_path,
    )
    assert report.ok is False
    assert report.results[0].status == "blocked"
