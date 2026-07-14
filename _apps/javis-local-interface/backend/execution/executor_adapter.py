"""Adapters supervisionados para Codex e Claude Code (R4.2B).

Os adapters só rodam dentro de worktree validada e sempre via process_utils.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import execution_task as et
from . import process_utils
from ._sanitize import sanitize
from .process_sandbox import SandboxLimits
from .worktree_manager import JAVIS_ROOT, SecurityError


DEFAULT_SANDBOX_LIMITS = SandboxLimits(
    max_memory_mb=2048, max_cpu_seconds=600, max_processes=32,
)


@dataclass(frozen=True)
class AdapterRequest:
    task_id: str
    project_id: str
    objective: str
    worktree_path: str
    timeout_seconds: int
    prompt_path: str
    executor: str


AdapterResult = process_utils.ProcessResult


def _blocked(reason: str) -> AdapterResult:
    return AdapterResult(
        exit_code=126,
        status="blocked",
        stdout="",
        stderr=sanitize(reason, 1000),
        timed_out=False,
        duration_ms=0,
        command_summary="blocked",
    )


class BaseAdapter:
    executor_id = ""

    def __init__(self, *, binary: str, runner=process_utils.safe_run,
                 sandbox_limits: SandboxLimits | None = DEFAULT_SANDBOX_LIMITS):
        self.binary = binary
        self.runner = runner
        self.sandbox_limits = sandbox_limits

    def validate_request(self, request: AdapterRequest) -> Path:
        et.validate_task_id(request.task_id)
        et.normalize_project_id(request.project_id)
        if request.executor and request.executor != self.executor_id:
            raise SecurityError("executor incompatível com adapter")
        worktree = Path(request.worktree_path).resolve()
        if not worktree.is_dir() or not (worktree / ".git").exists():
            raise SecurityError("worktree inválida")
        root = JAVIS_ROOT.resolve()
        if worktree == root:
            raise SecurityError("adapter recusou repo principal")
        if request.prompt_path:
            prompt = Path(request.prompt_path).resolve()
            try:
                prompt.relative_to(worktree)
            except ValueError as exc:
                raise SecurityError("prompt_path fora da worktree") from exc
        return worktree

    def _run(self, argv: list[str], request: AdapterRequest) -> AdapterResult:
        worktree = self.validate_request(request)
        return self.runner(
            argv,
            cwd=worktree,
            allowed_root=worktree,
            timeout_seconds=request.timeout_seconds,
            sandbox_limits=self.sandbox_limits,
        )


class ClaudeCodeAdapter(BaseAdapter):
    """Claude Code limitado a edição/leitura; testes ficam no TestRunner do Javes."""

    executor_id = "claude"

    def __init__(self, *, binary: str = "claude", runner=process_utils.safe_run,
                 sandbox_limits: SandboxLimits | None = DEFAULT_SANDBOX_LIMITS):
        super().__init__(binary=binary, runner=runner, sandbox_limits=sandbox_limits)

    def run(self, request: AdapterRequest) -> AdapterResult:
        try:
            self.validate_request(request)
        except Exception as exc:
            return _blocked(str(exc))
        argv = [
            self.binary,
            "-p",
            str(Path(request.prompt_path).resolve()),
            "--allowedTools",
            "Read,Edit,Write",
        ]
        return self._run(argv, request)


class CodexAdapter(BaseAdapter):
    """Codex falha fechado se sandbox workspace-write não foi verificado."""

    executor_id = "codex"

    def __init__(self, *, binary: str = "codex", runner=process_utils.safe_run,
                 help_text: str | None = None,
                 sandbox_limits: SandboxLimits | None = DEFAULT_SANDBOX_LIMITS):
        super().__init__(binary=binary, runner=runner, sandbox_limits=sandbox_limits)
        self.help_text = help_text

    def _secure_sandbox_available(self) -> bool:
        text = self.help_text or ""
        return "--sandbox" in text and "workspace-write" in text

    def run(self, request: AdapterRequest) -> AdapterResult:
        try:
            self.validate_request(request)
        except Exception as exc:
            return _blocked(str(exc))
        if not self._secure_sandbox_available():
            return _blocked("secure_codex_sandbox_unavailable")
        argv = [
            self.binary,
            "exec",
            "--sandbox",
            "workspace-write",
            str(Path(request.prompt_path).resolve()),
        ]
        return self._run(argv, request)


def adapter_for(executor: str, **kwargs):
    normalized = et.validate_executor(executor)
    if normalized == "codex":
        return CodexAdapter(**kwargs)
    if normalized == "claude":
        return ClaudeCodeAdapter(**kwargs)
    raise ValueError("executor desconhecido")
