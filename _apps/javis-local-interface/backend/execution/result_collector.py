"""result_collector — coleta segura de resultados de execução (R4.2A).

NÃO executa agentes. Recebe stdout/stderr já produzidos (na R4.2B virão do
adapter) + uma worktree e monta um pacote de revisão: streams sanitizados e
truncados, git status, git diff --stat, diff completo (limitado), relatório de
testes e lista de arquivos alterados.

Segurança:
- tudo é sanitizado (sem token/Authorization/credencial-em-URL/segredo) antes de
  salvar;
- streams e diff são truncados a um teto;
- resultados vão para uma RAIZ CONTROLADA, fora do repo, com o path reconstruído
  a partir do task_id (nunca de input livre);
- arquivos alterados são validados como estando DENTRO da worktree;
- persistência filtrada por task_id + project_id.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from . import execution_task as et
from .commit_service import INTERNAL_PREFIX, SENSITIVE_MARKERS
from ._gitcmd import run_git
from ._sanitize import sanitize_truncated

# Raiz do repo Javes (…/javis). Resultados ficam FORA dele, ao lado.
JAVIS_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_RESULTS_ROOT = JAVIS_ROOT.parent / "javis-exec-results"

# Tetos de truncagem (chars).
MAX_STREAM_CHARS = 40_000
MAX_DIFF_CHARS = 120_000


class ResultError(et.ExecutionError):
    pass


def _resolve(path) -> Path:
    return Path(path).resolve()


class ResultCollector:
    def __init__(self, results_root=None):
        env_root = os.environ.get("JAVIS_EXEC_RESULTS_ROOT")  # env, não .env
        self.results_root = _resolve(results_root or env_root or _DEFAULT_RESULTS_ROOT)

    # ── paths ──────────────────────────────────────────────────────────────
    def results_dir_for(self, task_id: str) -> Path:
        """Reconstrói o diretório de resultados SEMPRE a partir do task_id."""
        tid = et.validate_task_id(task_id)
        d = _resolve(self.results_root / tid)
        if d.parent != self.results_root:
            raise ResultError("results dir fora da raiz de resultados")
        return d

    def within_worktree(self, path, worktree) -> bool:
        """True se path resolve para DENTRO (ou igual a) a worktree."""
        root = _resolve(worktree)
        target = _resolve(path)
        if target == root:
            return True
        try:
            target.relative_to(root)
        except ValueError:
            return False
        return True

    def _valid_relative_change(self, raw: str, worktree: Path) -> str:
        rel = (raw or "").strip().strip('"').replace("\\", "/")
        if not rel:
            return ""
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            return ""
        lowered_parts = tuple(part.lower() for part in rel_path.parts)
        joined = "/".join(lowered_parts)
        if any(part.startswith(INTERNAL_PREFIX) for part in lowered_parts):
            return ""
        if any(marker in lowered_parts or marker in joined for marker in SENSITIVE_MARKERS):
            return ""
        target = _resolve(worktree / rel_path)
        if target.exists() and not self.within_worktree(target, worktree):
            return ""
        if not self.within_worktree(target.parent, worktree):
            return ""
        return rel

    def _changed_files(self, worktree: Path, diff_range: str = "") -> list[str]:
        if diff_range:
            rc, out, _ = run_git(worktree, ["diff", "--name-only", diff_range])
        else:
            rc, out, _ = run_git(worktree, ["status", "--porcelain"])
        files: list[str] = []
        if rc != 0:
            return files
        for line in out.splitlines():
            raw = line
            if not diff_range:
                if len(line) < 4:
                    continue
                raw = line[3:].strip()
            if " -> " in raw:  # rename: pega o destino
                raw = raw.split(" -> ", 1)[1]
            rel = self._valid_relative_change(raw, worktree)
            if rel:
                files.append(rel)
        return files

    def _diff_range(self, task: dict | None, worktree: Path) -> str:
        source_commit = ((task or {}).get("source_commit") or "").strip()
        if not source_commit:
            return ""
        rc, head, _ = run_git(worktree, ["rev-parse", "HEAD"])
        if rc != 0 or not head.strip() or head.strip() == source_commit:
            return ""
        rc, _, _ = run_git(worktree, ["merge-base", "--is-ancestor", source_commit, "HEAD"])
        if rc != 0:
            return ""
        return f"{source_commit}..HEAD"

    # ── coleta ─────────────────────────────────────────────────────────────
    def collect(self, task_id: str, project_id: str, worktree_path,
                stdout: str = "", stderr: str = "", test_report: str = "") -> dict:
        import repositories as repo

        tid = et.validate_task_id(task_id)
        pid = et.normalize_project_id(project_id)
        wt = _resolve(worktree_path)
        if not wt.is_dir():
            raise ResultError("worktree inexistente")
        task = repo.execution_tasks.get(tid, pid)

        rdir = self.results_dir_for(tid)
        rdir.mkdir(parents=True, exist_ok=True)

        out_txt = sanitize_truncated(stdout, MAX_STREAM_CHARS)
        err_txt = sanitize_truncated(stderr, MAX_STREAM_CHARS)
        tests_txt = sanitize_truncated(test_report, MAX_STREAM_CHARS)

        diff_range = self._diff_range(task, wt)
        _, status_out, _ = run_git(wt, ["status", "--short", "--branch"])
        if diff_range:
            _, diffstat_out, _ = run_git(wt, ["diff", "--stat", diff_range])
            _, diff_out, _ = run_git(wt, ["diff", diff_range])
        else:
            _, diffstat_out, _ = run_git(wt, ["diff", "--stat"])
            _, diff_out, _ = run_git(wt, ["diff"])
        status_txt = sanitize_truncated(status_out, MAX_STREAM_CHARS)
        diffstat_txt = sanitize_truncated(diffstat_out, MAX_STREAM_CHARS)
        diff_txt = sanitize_truncated(diff_out, MAX_DIFF_CHARS)
        changed = self._changed_files(wt, diff_range=diff_range)

        # arquivos do pacote (nomes fixos → sem input livre no path)
        stdout_path = rdir / "stdout.txt"
        stderr_path = rdir / "stderr.txt"
        diff_path = rdir / "diff.patch"
        test_report_path = rdir / "tests.txt"
        result_path = rdir / "result.json"

        stdout_path.write_text(out_txt, encoding="utf-8")
        stderr_path.write_text(err_txt, encoding="utf-8")
        diff_path.write_text(diff_txt, encoding="utf-8")
        test_report_path.write_text(tests_txt, encoding="utf-8")

        summary = {
            "task_id": tid,
            "project_id": pid,
            "git_status": status_txt,
            "diff_stat": diffstat_txt,
            "diff_range": sanitize_truncated(diff_range, 200),
            "changed_files": changed,
            "changed_count": len(changed),
            "stdout_chars": len(out_txt),
            "stderr_chars": len(err_txt),
            "diff_chars": len(diff_txt),
            "diff_truncated": len(diff_out) > MAX_DIFF_CHARS,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        result_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                               encoding="utf-8")

        repo.execution_tasks.set_result_paths(
            tid, pid, result_path=str(result_path), diff_path=str(diff_path),
            test_report_path=str(test_report_path),
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        try:
            repo.task_events.add_event(tid, "results_collected", "system",
                                       f"Resultados coletados ({len(changed)} arquivos alterados)",
                                       metadata={"changed_count": len(changed)})
        except Exception:
            pass

        # devolve SÓ paths + contagens (nunca conteúdo bruto/segredo)
        return {
            "task_id": tid,
            "project_id": pid,
            "result_path": str(result_path),
            "diff_path": str(diff_path),
            "test_report_path": str(test_report_path),
            "changed_count": len(changed),
            "stdout_chars": len(out_txt),
            "stderr_chars": len(err_txt),
            "diff_chars": len(diff_txt),
            "diff_truncated": summary["diff_truncated"],
        }
