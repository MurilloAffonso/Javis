"""R4.4C — limites de recurso do executor via Windows Job Object.

Processos reais (não fakes): Job Object só pode ser associado a um PID
verdadeiro, então estes testes rodam scripts Python pequenos sob
`process_utils.safe_run(sandbox_limits=...)` e verificam que memória, CPU
e nº de processos do job são de fato limitados pelo SO — não apenas pelo
timeout de parede já existente.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution import process_utils  # noqa: E402
from execution.process_sandbox import ProcessSandbox, SandboxLimits, SandboxUnavailable  # noqa: E402
from execution.test_runner import DEFAULT_TEST_SANDBOX_LIMITS, TestRunner  # noqa: E402
from execution.executor_adapter import DEFAULT_SANDBOX_LIMITS, ClaudeCodeAdapter  # noqa: E402

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Job Object é específico do Windows")


def _script(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_processo_leve_completa_normalmente_sob_sandbox(tmp_path):
    script = _script(tmp_path, "leve.py", "print('ok')\n")
    result = process_utils.safe_run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=10,
        sandbox_limits=SandboxLimits(max_memory_mb=256, max_cpu_seconds=30, max_processes=8),
    )
    assert result.status == "success"
    assert "ok" in result.stdout


def test_cpu_time_limit_mata_processo_antes_do_timeout_de_parede(tmp_path):
    script = _script(tmp_path, "loop.py", (
        "import time\n"
        "end = time.monotonic() + 20\n"
        "while time.monotonic() < end:\n"
        "    pass\n"
        "print('done')\n"
    ))
    result = process_utils.safe_run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=15,
        sandbox_limits=SandboxLimits(max_memory_mb=256, max_cpu_seconds=1, max_processes=8),
    )
    assert "done" not in result.stdout
    assert result.duration_ms < 10_000


def test_memory_limit_impede_alocacao_alem_do_job(tmp_path):
    script = _script(tmp_path, "mem.py", (
        "blocks = []\n"
        "try:\n"
        "    for _ in range(400):\n"
        "        blocks.append(bytearray(1024 * 1024))\n"
        "    print('allocated_all')\n"
        "except MemoryError:\n"
        "    print('memory_error')\n"
        "    raise SystemExit(1)\n"
    ))
    result = process_utils.safe_run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=15,
        sandbox_limits=SandboxLimits(max_memory_mb=48, max_cpu_seconds=30, max_processes=8),
    )
    assert "allocated_all" not in result.stdout


def test_active_process_limit_bloqueia_processos_alem_do_limite(tmp_path):
    child = _script(tmp_path, "child.py", "import time\ntime.sleep(5)\n")
    parent = _script(tmp_path, "spawn.py", (
        "import subprocess, sys\n"
        f"child = {str(child)!r}\n"
        "spawned = 0\n"
        "procs = []\n"
        "for _ in range(10):\n"
        "    try:\n"
        "        procs.append(subprocess.Popen([sys.executable, child]))\n"
        "        spawned += 1\n"
        "    except OSError:\n"
        "        break\n"
        "print(f'spawned={spawned}')\n"
        "for p in procs:\n"
        "    p.kill()\n"
    ))
    result = process_utils.safe_run(
        [sys.executable, str(parent)],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=15,
        sandbox_limits=SandboxLimits(max_memory_mb=256, max_cpu_seconds=30, max_processes=3),
    )
    match = re.search(r"spawned=(\d+)", result.stdout)
    assert match, result.stdout
    assert 1 <= int(match.group(1)) < 10


def test_fase_de_testes_roda_sob_sandbox_e_nao_so_timeout(tmp_path):
    """A fase de testes executa código de autoria do agente (safe_python roda
    pytest sobre a worktree). Sem Job Object ela teria só o timeout de parede:
    este teste prova que o TestRunner realmente passa sandbox_limits adiante."""
    captured = {}

    def runner(argv, **kwargs):
        captured.update(kwargs)
        return process_utils.ProcessResult(0, "success", "", "", False, 1, "ok")

    report = TestRunner(runner=runner).run(
        [["python", "-m", "pytest", "-q", "tests"]], tmp_path,
    )
    assert report.ok is True, report.report
    assert captured["sandbox_limits"] == DEFAULT_TEST_SANDBOX_LIMITS


def test_teste_do_agente_que_consome_cpu_e_morto_pelo_job(tmp_path):
    """Cenário real: o agente escreve um teste que gira CPU sem parar. Antes do
    R4.4C isso rodava até o timeout de parede; agora o job mata muito antes."""
    (tmp_path / "test_hostil.py").write_text(
        "import time\n"
        "def test_gira():\n"
        "    end = time.monotonic() + 30\n"
        "    while time.monotonic() < end:\n"
        "        pass\n",
        encoding="utf-8",
    )
    report = TestRunner(
        timeout_seconds=25,
        sandbox_limits=SandboxLimits(max_memory_mb=512, max_cpu_seconds=1, max_processes=8),
    ).run([[sys.executable, "-m", "pytest", "-q", "test_hostil.py"]], tmp_path)

    # não pode ter sido barrado pela allowlist — tem que ter REALMENTE rodado e
    # sido morto pelo job, senão o teste passaria pelo motivo errado
    assert report.results[0].status != "blocked", report.report
    assert report.ok is False
    assert all(r.duration_ms < 15_000 for r in report.results)


def test_adapter_passa_sandbox_limits_para_o_runner(tmp_path):
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: fake", encoding="utf-8")
    prompt = worktree / "prompt.txt"
    prompt.write_text("objective", encoding="utf-8")
    captured = {}

    def runner(argv, **kwargs):
        captured.update(kwargs)
        return process_utils.ProcessResult(0, "success", "", "", False, 1, "ok")

    from execution.executor_adapter import AdapterRequest

    ClaudeCodeAdapter(runner=runner).run(AdapterRequest(
        task_id="exec_aaaaaaaa", project_id="javes-core", objective="obj",
        worktree_path=str(worktree), timeout_seconds=10,
        prompt_path=str(prompt), executor="claude",
    ))
    assert captured["sandbox_limits"] == DEFAULT_SANDBOX_LIMITS


def test_profile_safe_python_passa_na_allowlist_do_test_runner(tmp_path):
    """Regressão: o argv de safe_python precisa satisfazer _is_python_pytest
    (>=5 elementos). Sem o `-q` ele caía em 'comando de teste fora da allowlist'
    e o perfil ficava morto — nenhuma task safe_python conseguia passar."""
    from execution.programming_task_spec import TEST_PROFILES
    from execution.test_runner import _validate_runner_command

    for command in TEST_PROFILES["safe_python"]:
        assert _validate_runner_command(list(command), tmp_path) == ""


def test_sandbox_indisponivel_nao_quebra_execucao(monkeypatch, tmp_path):
    def boom(self, limits):
        raise SandboxUnavailable("forced")

    monkeypatch.setattr(ProcessSandbox, "__init__", boom)
    script = _script(tmp_path, "leve.py", "print('ok')\n")
    result = process_utils.safe_run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=10,
        sandbox_limits=SandboxLimits(),
    )
    assert result.status == "success"
    assert "ok" in result.stdout
