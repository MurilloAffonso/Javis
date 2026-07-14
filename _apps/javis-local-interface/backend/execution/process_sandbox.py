"""Limites de recurso do executor via Windows Job Object (R4.4C).

Camada de defesa adicional além do timeout de parede já aplicado em
`process_utils.safe_run`: memória, tempo de CPU e número de processos do
adapter (Claude Code/Codex) ficam sob um Job Object. `JOB_OBJECT_LIMIT_
KILL_ON_JOB_CLOSE` garante que, mesmo se o processo do Javes morrer sem
limpar, o Windows mata os filhos órfãos quando o último handle do job
fecha — sem isso um adapter travado sobreviveria ao processo pai.

Best-effort: se pywin32 ou a API de Job Object não estiverem disponíveis,
`ProcessSandbox` levanta `SandboxUnavailable` e o chamador segue sem o
limite extra (o timeout de parede continua sendo a garantia primária).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxLimits:
    max_memory_mb: int = 2048
    max_cpu_seconds: int = 600
    max_processes: int = 32


class SandboxUnavailable(RuntimeError):
    """pywin32 ausente, plataforma não-Windows ou Job Object indisponível."""


def _win32_modules():
    if sys.platform != "win32":
        raise SandboxUnavailable("job_object_requires_windows")
    try:
        import win32api
        import win32con
        import win32job
    except ImportError as exc:
        raise SandboxUnavailable("pywin32_missing") from exc
    return win32api, win32con, win32job


class ProcessSandbox:
    """Job Object com limites de memória/CPU/processos para um único run."""

    def __init__(self, limits: SandboxLimits):
        win32api, win32con, win32job = _win32_modules()
        self._win32job = win32job
        self._win32api = win32api
        self._win32con = win32con
        self.limits = limits
        try:
            self._handle = win32job.CreateJobObject(None, "")
            info = win32job.QueryInformationJobObject(
                self._handle, win32job.JobObjectExtendedLimitInformation
            )
            basic = info["BasicLimitInformation"]
            basic["LimitFlags"] = (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                | win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
                | win32job.JOB_OBJECT_LIMIT_JOB_TIME
                | win32job.JOB_OBJECT_LIMIT_JOB_MEMORY
            )
            basic["ActiveProcessLimit"] = max(1, int(limits.max_processes))
            basic["PerJobUserTimeLimit"] = int(limits.max_cpu_seconds) * 10_000_000
            info["BasicLimitInformation"] = basic
            info["JobMemoryLimit"] = max(1, int(limits.max_memory_mb)) * 1024 * 1024
            win32job.SetInformationJobObject(
                self._handle, win32job.JobObjectExtendedLimitInformation, info
            )
        except Exception as exc:
            raise SandboxUnavailable("job_object_setup_failed") from exc

    def assign(self, pid: int) -> bool:
        """Associa um PID real ao job. Retorna False sem levantar em falha."""
        try:
            handle = self._win32api.OpenProcess(
                self._win32con.PROCESS_SET_QUOTA | self._win32con.PROCESS_TERMINATE,
                False, int(pid),
            )
        except Exception:
            return False
        try:
            self._win32job.AssignProcessToJobObject(self._handle, handle)
            return True
        except Exception:
            return False
        finally:
            try:
                handle.Close()
            except Exception:
                pass

    def close(self) -> None:
        try:
            self._handle.Close()
        except Exception:
            pass

    def __enter__(self) -> "ProcessSandbox":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
