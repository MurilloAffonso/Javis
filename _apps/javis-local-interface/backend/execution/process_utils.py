"""Subprocess seguro para execução supervisionada (R4.2B).

Centraliza `shell=False`, cwd validado, ambiente sanitizado, timeout e redaction.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import time

from ._sanitize import sanitize, sanitize_truncated


MAX_STREAM_CHARS = 40_000

_GIT_LOCATION_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_NAMESPACE",
    "GIT_PREFIX",
}

_SENSITIVE_ENV_FRAGMENTS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "CREDENTIAL",
    "AUTHORIZATION",
    "API_KEY",
    "APIKEY",
    "OPENAI",
    "ANTHROPIC",
    "CLAUDE",
    "GEMINI",
    "OPENROUTER",
    "CODEX",
)

_SAFE_ENV_KEYS = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "HOME",
    "COMSPEC",
    "PYTHONPATH",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
}


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int
    status: str
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    command_summary: str


def _is_sensitive_env_key(key: str) -> bool:
    upper = key.upper()
    if upper in _GIT_LOCATION_ENV:
        return True
    return any(fragment in upper for fragment in _SENSITIVE_ENV_FRAGMENTS)


def sanitized_env(base_env: dict[str, str] | None = None,
                  extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Ambiente mínimo: sem GIT_* de localização e sem tokens/chaves."""
    source = dict(os.environ if base_env is None else base_env)
    env: dict[str, str] = {}
    for key, value in source.items():
        upper = key.upper()
        if upper in _SAFE_ENV_KEYS and not _is_sensitive_env_key(upper):
            env[key] = str(value)
    for key, value in (extra_env or {}).items():
        if not _is_sensitive_env_key(key):
            env[str(key)] = str(value)
    for key in list(env):
        if key.upper() in _GIT_LOCATION_ENV:
            env.pop(key, None)
    return env


def _resolve_existing_dir(path) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_dir():
        raise ValueError("cwd inválido")
    return resolved


def validate_cwd(cwd, allowed_root=None) -> Path:
    resolved = _resolve_existing_dir(cwd)
    if allowed_root is not None:
        root = _resolve_existing_dir(allowed_root)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("cwd fora da raiz permitida") from exc
    return resolved


def _command_summary(argv: list[str]) -> str:
    parts = [Path(argv[0]).name, *argv[1:]]
    return sanitize(" ".join(parts), 500)


def _sanitize_stream(value: str) -> str:
    cleaned = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)\S+", r"\1[REDACTED]", value or "")
    cleaned = re.sub(r"(?i)\b(token|secret|password|api[_-]?key)\s*=\s*\S+", r"\1=[REDACTED]", cleaned)
    return sanitize_truncated(cleaned, MAX_STREAM_CHARS)


def _kill_process_tree(proc: subprocess.Popen) -> None:
    pid = getattr(proc, "pid", None)
    if os.name == "nt" and pid:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception:
            pass
    try:
        proc.kill()
    except Exception:
        pass


def safe_run(argv, *, cwd, timeout_seconds: int, allowed_root=None,
             env: dict[str, str] | None = None,
             popen_factory=None) -> ProcessResult:
    """Executa argv estruturado com `shell=False` e sem vazar segredos."""
    start = time.monotonic()
    try:
        if not isinstance(argv, (list, tuple)) or not argv:
            raise ValueError("argv deve ser lista não-vazia")
        argv = [str(item) for item in argv]
        cwd_path = validate_cwd(cwd, allowed_root or cwd)
        clean_env = sanitized_env(extra_env=env)
        popen = popen_factory or subprocess.Popen
        proc = popen(
            argv,
            cwd=str(cwd_path),
            shell=False,
            env=clean_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=max(1, int(timeout_seconds)))
            exit_code = int(proc.returncode if proc.returncode is not None else 0)
            status = "success" if exit_code == 0 else "failed"
            timed_out = False
        except subprocess.TimeoutExpired:
            _kill_process_tree(proc)
            stdout, stderr = proc.communicate()
            exit_code = -9
            status = "timed_out"
            timed_out = True
    except Exception as exc:
        stdout = ""
        stderr = sanitize(str(exc), 1000)
        exit_code = -1
        status = "failed"
        timed_out = False
        argv = [str(item) for item in argv] if isinstance(argv, (list, tuple)) else ["invalid"]

    duration_ms = int((time.monotonic() - start) * 1000)
    return ProcessResult(
        exit_code=exit_code,
        status=status,
        stdout=_sanitize_stream(stdout or ""),
        stderr=_sanitize_stream(stderr or ""),
        timed_out=timed_out,
        duration_ms=duration_ms,
        command_summary=_command_summary(argv),
    )
