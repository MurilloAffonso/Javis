from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution import process_utils  # noqa: E402


class FakeProcess:
    def __init__(self, stdout="ok", stderr="", returncode=0, timeout=False):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.timeout = timeout
        self.killed = False
        self.pid = 12345
        self.calls = 0

    def communicate(self, timeout=None):
        self.calls += 1
        if self.timeout and self.calls == 1:
            raise subprocess.TimeoutExpired(["fake"], timeout)
        return self.stdout, self.stderr

    def kill(self):
        self.killed = True


def test_safe_run_usa_cwd_shell_false_e_remove_git_env(monkeypatch, tmp_path):
    captured = {}

    def popen(argv, **kwargs):
        captured.update(kwargs)
        return FakeProcess()

    monkeypatch.setenv("GIT_DIR", "NAO_VAZAR")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-NAO_VAZAR")
    result = process_utils.safe_run(
        ["python", "-m", "py_compile", "x.py"],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=1,
        popen_factory=popen,
    )
    assert result.status == "success"
    assert captured["shell"] is False
    assert captured["cwd"] == str(tmp_path.resolve())
    assert "GIT_DIR" not in captured["env"]
    assert "OPENAI_API_KEY" not in captured["env"]


def test_safe_run_sanitiza_stdout_stderr(tmp_path):
    def popen(argv, **kwargs):
        return FakeProcess(stdout="token=abc123", stderr="Authorization: Bearer secret")

    result = process_utils.safe_run(
        ["fake"],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=1,
        popen_factory=popen,
    )
    assert "abc123" not in result.stdout
    assert "secret" not in result.stderr


def test_timeout_mata_processo(monkeypatch, tmp_path):
    fake = FakeProcess(timeout=True)

    def popen(argv, **kwargs):
        return fake

    monkeypatch.setattr(process_utils, "_kill_process_tree", lambda proc: proc.kill())
    result = process_utils.safe_run(
        ["fake"],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=1,
        popen_factory=popen,
    )
    assert result.status == "timed_out"
    assert result.timed_out is True
    assert fake.killed is True


def test_cwd_fora_da_raiz_permitida_bloqueia(tmp_path):
    outside = tmp_path / "outside"
    root = tmp_path / "root"
    outside.mkdir()
    root.mkdir()
    result = process_utils.safe_run(
        ["fake"],
        cwd=outside,
        allowed_root=root,
        timeout_seconds=1,
        popen_factory=lambda argv, **kwargs: FakeProcess(),
    )
    assert result.status == "failed"
    assert "fora" in result.stderr
