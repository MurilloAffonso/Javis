"""Modo Madrugada (R4.5) — execução desassistida de UMA task já aprovada.

A Madrugada **não cria um caminho novo** de execução: ela reusa o mesmo
`ProgrammingTaskFlow` da R4.4B e só consegue disparar o passo `run` de uma task
que já está em `approved`. E `approved` só existe depois que um humano rodou
`approve_start`, consumindo um approval `execution.start` single-use amarrado ao
`spec_hash`. A autorização acontece **acordado**; a Madrugada só aperta o botão
mais tarde. Ela é incapaz de executar algo que Murillo não aprovou antes.

O que a Madrugada NUNCA faz, por construção (não existe chamada para isso aqui):
aprovar merge, fazer merge, dar push, ou admitir/aprovar uma task nova.
Ela para em `awaiting_review` e, no máximo, **pede** o approval de merge — que
fica `pending`, esperando o humano de manhã.

## Por que UMA task por noite, e não uma fila

O executor mantém uma invariante de raio de explosão: **uma task real ativa por
vez** (`execution_task_specs.active_for_project`, onde `awaiting_review` ainda
conta como ativa). Uma fila de N tasks por noite não só esbarraria nisso como
seria incoerente: todas nasceriam do mesmo `source_commit`, então mergear a
primeira de manhã moveria o master e as outras N-1 cairiam em
`source_branch_moved` — inmergeáveis. Rodar uma só não é limitação contornada,
é o único desenho coerente. Se houver mais de uma task aprovada, a Madrugada
**recusa** em vez de escolher sozinha qual rodar.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import repositories as repo
import safe_config

from . import execution_task as et
from ._sanitize import sanitize
from .programming_task_flow import CORE_PROJECT_ID, RUN_PHRASE, ProgrammingTaskFlow


JAVIS_ROOT = Path(__file__).resolve().parents[4]
KILL_SWITCH = JAVIS_ROOT / "_estado" / "MADRUGADA.OFF"
NIGHT_LOG_DIR = JAVIS_ROOT / "_logs" / "madrugada"

ARM_PHRASE = "ARMAR MADRUGADA"


@dataclass(frozen=True)
class NightWindow:
    """Janela horária em que a Madrugada pode iniciar a task. Suporta virada."""

    start_hour: int = 0
    end_hour: int = 6

    def contains(self, moment: datetime) -> bool:
        hour = moment.hour
        if self.start_hour == self.end_hour:
            return False
        if self.start_hour < self.end_hour:
            return self.start_hour <= hour < self.end_hour
        return hour >= self.start_hour or hour < self.end_hour


DEFAULT_WINDOW = NightWindow()


class NightMode:
    def __init__(
        self,
        *,
        flow: ProgrammingTaskFlow | None = None,
        repository=repo,
        window: NightWindow = DEFAULT_WINDOW,
        now=lambda: datetime.now(timezone.utc).astimezone(),
        kill_switch: Path = KILL_SWITCH,
        log_dir: Path = NIGHT_LOG_DIR,
        request_merge_approval: bool = True,
    ):
        self._flow = flow
        self.repo = repository
        self.window = window
        self.now = now
        self.kill_switch = Path(kill_switch)
        self.log_dir = Path(log_dir)
        self.request_merge_approval = request_merge_approval

    @property
    def flow(self) -> ProgrammingTaskFlow:
        if self._flow is None:
            self._flow = ProgrammingTaskFlow()
        return self._flow

    # ── guardas ──────────────────────────────────────────────────────────
    def _gate(self) -> str:
        """Primeiro motivo de bloqueio, ou "" se pode rodar. Fail-closed."""
        if not safe_config.night_mode_enabled():
            return "night_mode_disabled"
        if not safe_config.supervised_execution_enabled():
            return "supervised_execution_disabled"
        if not safe_config.real_programming_tasks_enabled():
            return "real_programming_tasks_disabled"
        if self.kill_switch.exists():
            return "kill_switch_active"
        if not self.window.contains(self.now()):
            return "outside_night_window"
        return ""

    def approved_tasks(self) -> list[dict]:
        """Tasks que a Madrugada PODE rodar: aprovadas por um humano. Nada aqui é
        aprovado pela Madrugada — a lista é só lida."""
        rows = self.repo.execution_tasks.list_by_project(CORE_PROJECT_ID, et.APPROVED)
        return [row for row in rows if row.get("approval_id")]

    def _target(self) -> tuple[dict | None, str]:
        """A única task elegível, ou o motivo de não haver uma."""
        approved = self.approved_tasks()
        if not approved:
            return None, "no_approved_task"
        if len(approved) > 1:
            # O executor só admite uma task real ativa por vez, e duas tasks da
            # mesma noite seriam inmergeáveis (source_branch_moved). Recusar é
            # mais honesto do que escolher sozinha qual roda.
            return None, "multiple_approved_tasks"
        return approved[0], ""

    def preflight(self) -> dict:
        """Diagnóstico sem efeito colateral: dá pra rodar esta noite?"""
        blocked = self._gate()
        target, why = self._target()
        reason = blocked or why
        return {
            "status": "blocked" if reason else "ready",
            "reason": reason,
            "window": f"{self.window.start_hour:02d}h-{self.window.end_hour:02d}h",
            "inside_window": self.window.contains(self.now()),
            "kill_switch_active": self.kill_switch.exists(),
            "approved_tasks": len(self.approved_tasks()),
            "task_id": (target or {}).get("task_id", ""),
        }

    # ── execução ─────────────────────────────────────────────────────────
    def run(self, confirm: str) -> dict:
        if confirm != ARM_PHRASE:
            return {"status": "blocked", "reason": "confirmation_phrase_required"}
        blocked = self._gate()
        if blocked:
            return {"status": "blocked", "reason": blocked}
        target, why = self._target()
        if not target:
            return {"status": "blocked", "reason": why}

        started = self.now()
        outcome = self._run_one(target["task_id"])
        report = {
            "status": "ok",
            "started_at": started.isoformat(),
            "finished_at": self.now().isoformat(),
            **outcome,
        }
        self._log(report)
        return report

    def _run_one(self, task_id: str) -> dict:
        try:
            result = self.flow.run(task_id, RUN_PHRASE)
        except Exception as exc:  # noqa: BLE001 — a noite falha registrando, não estourando
            return {"task_id": task_id, "task_status": "failed",
                    "reason": sanitize(str(exc), 120) or "night_run_error",
                    "merge_approval_id": None}

        outcome = {
            "task_id": task_id,
            "task_status": result.get("status") or "",
            "reason": result.get("reason") or "",
            "merge_approval_id": None,
        }
        if outcome["task_status"] != et.AWAITING_REVIEW:
            return outcome

        # Só PEDE o approval de merge — ele nasce `pending` e espera o humano.
        # A Madrugada não tem caminho para aprová-lo nem para fazer o merge.
        if self.request_merge_approval:
            try:
                requested = self.flow.request_merge(task_id)
                if requested.get("status") == et.AWAITING_REVIEW:
                    outcome["merge_approval_id"] = requested.get("approval_id")
                else:
                    outcome["reason"] = requested.get("reason") or ""
            except Exception:
                outcome["reason"] = "merge_request_failed"
        return outcome

    def _log(self, report: dict) -> None:
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            stamp = self.now().strftime("%Y-%m-%d")
            path = self.log_dir / f"{stamp}_madrugada.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(report, ensure_ascii=False) + "\n")
        except Exception:
            pass
