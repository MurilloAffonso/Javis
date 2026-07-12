"""Enforcement pós-execução e commit controlado para tasks reais R4.4B1."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from ._gitcmd import run_git
from ._sanitize import sanitize, sanitize_truncated
from .commit_service import CommitResult, INTERNAL_PREFIX
from .programming_task_spec import SECRET_RE, SQLITE_RE, TEST_PROFILES
from .test_runner import TestRunner


_TEXT_SUFFIXES = {".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml",
                  ".py", ".js", ".ts", ".css", ".html", ".xml", ".csv"}
_BLOCKED_PARTS = {".git", "_data", "javis-worktrees", "node_modules", ".venv",
                  "__pycache__", "evidence", "evidences", "evidencias"}


class PolicyViolation(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ChangeRecord:
    status: str
    source: str
    destination: str

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(path for path in (self.source, self.destination) if path)


@dataclass(frozen=True)
class ValidatedChanges:
    records: tuple[ChangeRecord, ...]
    stage_paths: tuple[str, ...]
    diff_lines: int

    @property
    def changed_count(self) -> int:
        return len(self.records)


@dataclass(frozen=True)
class ProfileReport:
    status: str
    ok: bool
    report: str
    duration_ms: int


def build_internal_prompt(spec: dict) -> str:
    paths = "\n".join(f"- {path}" for path in spec["allowed_paths"])
    limits = spec["limits"]
    return (
        f"TAREFA REAL SUPERVISIONADA\nTítulo: {spec['title']}\n\n"
        f"Objetivo:\n{spec['objective']}\n\nCaminhos permitidos:\n{paths}\n\n"
        f"Perfil de testes: {spec['test_profile']}\n"
        f"Limites: {limits['max_duration_seconds']} segundos, "
        f"{limits['max_changed_files']} arquivos, {limits['max_diff_lines']} linhas de diff.\n\n"
        "REGRAS OBRIGATÓRIAS:\n"
        "- Não use rede e não inicie servidores.\n"
        "- Não altere arquivos fora dos caminhos permitidos.\n"
        "- Não abra .env, credenciais, bancos SQLite ou diretórios de evidências.\n"
        "- Não execute push, merge, rebase ou reset.\n"
        "- Não use git add ., git add -A ou git add --all.\n"
        "- Faça somente a alteração solicitada; o Javes executará testes e commit.\n"
    )


def _normalize_change_path(raw: str) -> str:
    value = (raw or "").strip().strip('"').replace("\\", "/")
    path = PurePosixPath(value)
    if (not value or value.startswith("/") or ":" in value or ".." in path.parts
            or any(part in {"", "."} for part in value.split("/"))):
        raise PolicyViolation("path_policy_violation")
    return path.as_posix()


def _is_sensitive(path: str) -> bool:
    parts = tuple(part.lower() for part in PurePosixPath(path).parts)
    joined = "/".join(parts)
    return (
        any(part in _BLOCKED_PARTS or part.startswith(INTERNAL_PREFIX) for part in parts)
        or any(part == ".env" or part.startswith(".env.") for part in parts)
        or bool(SECRET_RE.search(joined) or SQLITE_RE.search(joined))
    )


def _allowed(path: str, allowed_paths: list[str]) -> bool:
    for allowed in allowed_paths:
        normalized = allowed.rstrip("/")
        if path == normalized or (allowed.endswith("/") and path.startswith(normalized + "/")):
            return True
    return False


class ProgrammingChangePolicy:
    def __init__(self, git_runner=run_git):
        self.git_runner = git_runner

    def _git(self, cwd: Path, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
        return self.git_runner(cwd, args, timeout=timeout)

    def _working_records(self, worktree: Path) -> list[ChangeRecord]:
        rc, out, err = self._git(worktree, ["status", "--porcelain=v1", "-z"])
        if rc != 0:
            raise PolicyViolation("dirty_worktree")
        tokens = out.split("\0")
        records: list[ChangeRecord] = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            index += 1
            if not token:
                continue
            if len(token) < 4 or token[2] != " ":
                raise PolicyViolation("path_policy_violation")
            status = token[:2]
            destination = _normalize_change_path(token[3:])
            source = ""
            if "R" in status or "C" in status:
                if index >= len(tokens) or not tokens[index]:
                    raise PolicyViolation("path_policy_violation")
                source = _normalize_change_path(tokens[index])
                index += 1
            records.append(ChangeRecord(status.strip() or "M", source, destination))
        return records

    def _committed_records(self, worktree: Path, source_commit: str) -> list[ChangeRecord]:
        rc, out, _ = self._git(
            worktree, ["diff", "--name-status", "-M", f"{source_commit}..HEAD"]
        )
        if rc != 0:
            raise PolicyViolation("no_new_commit")
        records: list[ChangeRecord] = []
        for line in out.splitlines():
            fields = line.split("\t")
            if len(fields) < 2:
                raise PolicyViolation("path_policy_violation")
            status = fields[0]
            if status.startswith(("R", "C")):
                if len(fields) != 3:
                    raise PolicyViolation("path_policy_violation")
                records.append(ChangeRecord(status, _normalize_change_path(fields[1]),
                                            _normalize_change_path(fields[2])))
            else:
                records.append(ChangeRecord(status, "", _normalize_change_path(fields[1])))
        return records

    def _git_mode(self, worktree: Path, path: str, source_commit: str = "") -> str:
        rc, out, _ = self._git(worktree, ["ls-files", "--stage", "--", path])
        if rc == 0 and out.strip():
            return out.split(None, 1)[0]
        if source_commit:
            rc, out, _ = self._git(worktree, ["ls-tree", source_commit, "--", path])
            if rc == 0 and out.strip():
                return out.split(None, 1)[0]
        return ""

    def _validate_paths(self, worktree: Path, records: list[ChangeRecord], spec: dict,
                        source_commit: str) -> tuple[str, ...]:
        stage: list[str] = []
        seen: set[str] = set()
        for record in records:
            for path in record.paths:
                if _is_sensitive(path):
                    raise PolicyViolation("sensitive_path_violation")
                if not _allowed(path, spec["allowed_paths"]):
                    raise PolicyViolation("path_policy_violation")
                target = worktree / Path(*PurePosixPath(path).parts)
                if target.is_symlink() or self._git_mode(worktree, path, source_commit) == "120000":
                    raise PolicyViolation("symlink_not_allowed")
                if self._git_mode(worktree, path, source_commit) == "160000":
                    raise PolicyViolation("submodule_not_allowed")
                if path not in seen:
                    seen.add(path)
                    stage.append(path)
        return tuple(stage)

    def _diff_lines(self, worktree: Path, records: list[ChangeRecord], source_commit: str,
                    committed: bool) -> int:
        diff_range = f"{source_commit}..HEAD" if committed else "HEAD"
        rc, out, _ = self._git(worktree, ["diff", "--numstat", diff_range])
        if rc != 0:
            raise PolicyViolation("max_diff_lines_exceeded")
        total = 0
        tracked_paths: set[str] = set()
        for line in out.splitlines():
            fields = line.split("\t")
            if len(fields) < 3 or not fields[0].isdigit() or not fields[1].isdigit():
                raise PolicyViolation("max_diff_lines_exceeded")
            total += int(fields[0]) + int(fields[1])
            tracked_paths.add(fields[-1].replace("\\", "/"))
        if not committed:
            for record in records:
                path = record.destination
                if path in tracked_paths or not record.status.startswith("??"):
                    continue
                target = worktree / Path(*PurePosixPath(path).parts)
                try:
                    data = target.read_bytes()
                    if b"\x00" in data:
                        raise PolicyViolation("max_diff_lines_exceeded")
                    total += len(data.splitlines())
                except OSError as exc:
                    raise PolicyViolation("path_policy_violation") from exc
        return total

    def validate(self, task: dict, spec: dict, *, committed: bool = False) -> ValidatedChanges:
        worktree = Path(task.get("worktree_path") or "").resolve()
        if not worktree.is_dir():
            raise PolicyViolation("dirty_worktree")
        source_commit = (task.get("source_commit") or "").strip()
        if not source_commit:
            raise PolicyViolation("no_new_commit")
        records = (self._committed_records(worktree, source_commit) if committed
                   else self._working_records(worktree))
        if not records:
            raise PolicyViolation("no_new_commit")
        if len(records) > int(spec["limits"]["max_changed_files"]):
            raise PolicyViolation("max_changed_files_exceeded")
        stage = self._validate_paths(worktree, records, spec, source_commit)
        lines = self._diff_lines(worktree, records, source_commit, committed)
        if lines > int(spec["limits"]["max_diff_lines"]):
            raise PolicyViolation("max_diff_lines_exceeded")
        return ValidatedChanges(tuple(records), stage, lines)


class RealTaskCommitService:
    def __init__(self, policy: ProgrammingChangePolicy | None = None):
        self.policy = policy or ProgrammingChangePolicy()

    def commit(self, task: dict, spec: dict) -> CommitResult:
        worktree = Path(task["worktree_path"]).resolve()
        changes = self.policy.validate(task, spec, committed=False)
        rc, before, _ = self.policy._git(worktree, ["rev-parse", "HEAD"])
        if rc != 0 or before.strip() != task.get("source_commit"):
            raise PolicyViolation("source_branch_moved")
        rc, _, err = self.policy._git(worktree, ["add", "--", *changes.stage_paths])
        if rc != 0:
            raise PolicyViolation("path_policy_violation")
        title = re.sub(r"[\x00-\x1f\x7f]+", " ", spec["title"]).strip()[:120]
        message = f"javes(real:{task['task_id']}): {title}"
        rc, _, err = self.policy._git(worktree, ["commit", "-m", message], timeout=60)
        if rc != 0:
            raise PolicyViolation("no_new_commit")
        rc, after, _ = self.policy._git(worktree, ["rev-parse", "HEAD"])
        if rc != 0 or not after.strip() or after.strip() == before.strip():
            raise PolicyViolation("no_new_commit")
        return CommitResult("committed", after.strip(), changes.changed_count,
                            changes.stage_paths, "")


class ProgrammingTestProfiles:
    def __init__(self, *, git_runner=run_git, python_runner: TestRunner | None = None):
        self.git_runner = git_runner
        self.python_runner = python_runner or TestRunner()

    def run(self, profile: str, worktree: Path, changed_files: tuple[str, ...],
            timeout_seconds: int) -> ProfileReport:
        import time
        start = time.monotonic()
        if profile == "docs_only":
            rc, out, err = self.git_runner(worktree, ["diff", "--check"],
                                           timeout=max(1, timeout_seconds))
            if rc != 0:
                return ProfileReport("failed", False, sanitize_truncated(out + err, 40000),
                                     int((time.monotonic() - start) * 1000))
            for rel in changed_files:
                target = worktree / Path(*PurePosixPath(rel).parts)
                if target.exists() and target.suffix.lower() in _TEXT_SUFFIXES:
                    try:
                        target.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        return ProfileReport("failed", False, "utf8_validation_failed",
                                             int((time.monotonic() - start) * 1000))
            return ProfileReport("success", True, "status=passed\ndocs_only",
                                 int((time.monotonic() - start) * 1000))
        if profile == "safe_python":
            commands = [list(command) for command in TEST_PROFILES["safe_python"]]
            runner = TestRunner(runner=self.python_runner.runner,
                                timeout_seconds=max(1, timeout_seconds))
            report = runner.run(commands, worktree)
            return ProfileReport(report.status, report.ok, report.report,
                                 int((time.monotonic() - start) * 1000))
        return ProfileReport("failed", False, "test_profile_not_allowed", 0)
