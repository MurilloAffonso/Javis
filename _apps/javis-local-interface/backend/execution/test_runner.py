"""Runner de testes permitido para execução supervisionada (R4.2B)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import execution_policy
from . import process_utils
from ._sanitize import sanitize_truncated
from .process_sandbox import SandboxLimits

__test__ = False


# A fase de testes executa código de autoria do agente (o perfil safe_python
# roda pytest sobre a worktree, então qualquer .py dentro da allowlist que o
# pytest importe vira código rodando). Teto mais apertado que o do adapter:
# rodar a suíte não deveria precisar de muita memória nem estourar processos.
DEFAULT_TEST_SANDBOX_LIMITS = SandboxLimits(
    max_memory_mb=1024, max_cpu_seconds=300, max_processes=16,
)


@dataclass(frozen=True)
class TestRunReport:
    __test__ = False

    status: str
    ok: bool
    results: list[process_utils.ProcessResult]
    report: str


def _program(argv: list[str]) -> str:
    name = Path(argv[0]).name.lower()
    return name[:-4] if name.endswith(".exe") else name


def _is_python_py_compile(argv: list[str]) -> bool:
    return (
        _program(argv) in {"python", "python3", "py"}
        and len(argv) >= 4
        and argv[1:3] == ["-m", "py_compile"]
        and all(not str(arg).startswith("-") for arg in argv[3:])
    )


def _is_python_pytest(argv: list[str]) -> bool:
    if not (_program(argv) in {"python", "python3", "py"} and len(argv) >= 5):
        return False
    if argv[1:3] != ["-m", "pytest"]:
        return False
    args = argv[3:]
    if any(str(arg).startswith("-") and arg != "-q" for arg in args):
        return False
    targets = [arg for arg in args if not str(arg).startswith("-")]
    return bool(targets) and "." not in targets


def _validate_runner_command(argv, worktree_path) -> str:
    if not isinstance(argv, (list, tuple)) or not argv:
        return "comando deve ser argv explícito"
    argv = [str(arg) for arg in argv]
    if not (_is_python_py_compile(argv) or _is_python_pytest(argv)):
        return "comando de teste fora da allowlist"
    decision = execution_policy.check_command(argv, worktree_path)
    if not decision.allowed:
        return decision.reason
    return ""


class TestRunner:
    __test__ = False

    def __init__(self, *, runner=process_utils.safe_run, timeout_seconds: int = 120,
                 sandbox_limits: SandboxLimits | None = DEFAULT_TEST_SANDBOX_LIMITS):
        self.runner = runner
        self.timeout_seconds = timeout_seconds
        self.sandbox_limits = sandbox_limits

    def run(self, commands: list[list[str]], worktree_path) -> TestRunReport:
        if not isinstance(commands, list) or not commands:
            blocked = process_utils.ProcessResult(
                exit_code=126,
                status="blocked",
                stdout="",
                stderr="lista explícita de testes ausente",
                timed_out=False,
                duration_ms=0,
                command_summary="test_runner",
            )
            return TestRunReport("blocked", False, [blocked], blocked.stderr)

        worktree = Path(worktree_path).resolve()
        results: list[process_utils.ProcessResult] = []
        for command in commands:
            denial = _validate_runner_command(command, worktree)
            if denial:
                result = process_utils.ProcessResult(
                    exit_code=126,
                    status="blocked",
                    stdout="",
                    stderr=denial,
                    timed_out=False,
                    duration_ms=0,
                    command_summary=" ".join(str(arg) for arg in command),
                )
            else:
                result = self.runner(
                    [str(arg) for arg in command],
                    cwd=worktree,
                    allowed_root=worktree,
                    timeout_seconds=self.timeout_seconds,
                    sandbox_limits=self.sandbox_limits,
                )
            results.append(result)
            if result.status != "success":
                break

        ok = all(result.status == "success" and result.exit_code == 0 for result in results)
        status = "success" if ok else ("timed_out" if any(r.timed_out for r in results) else "failed")
        report = "\n".join(
            f"$ {r.command_summary}\n{r.stdout}\n{r.stderr}".strip()
            for r in results
        )
        return TestRunReport(status, ok, results, sanitize_truncated(report, process_utils.MAX_STREAM_CHARS))
