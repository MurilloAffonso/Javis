"""Validação fail-closed da especificação R4.4A."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from .project_execution_registry import ProjectExecutionRegistry


TOP_FIELDS = {"schema_version", "project_id", "title", "objective", "executor",
              "allowed_paths", "test_profile", "limits"}
LIMIT_FIELDS = {"max_duration_seconds", "max_changed_files", "max_diff_lines"}
POLICY_MAXIMUMS = {"max_duration_seconds": 300, "max_changed_files": 5,
                   "max_diff_lines": 300}
TEST_PROFILES = {
    "docs_only": (("git", "diff", "--check"), ("internal", "document_validation")),
    "safe_python": (("python", "-m", "pytest", "_apps/javis-local-interface/tests"),),
}
EXECUTORS = {"claude", "codex"}
BLOCKED_PARTS = {".git", "_data", "javis-worktrees", "node_modules", ".venv",
                 "__pycache__", "evidence", "evidences", "evidencias"}
SECRET_RE = re.compile(
    r"(?:^|[._-])(secret|secrets|credential|credentials|token|private[_-]?key)(?:[._-]|$)", re.I
)
SQLITE_RE = re.compile(r"\.(?:db|sqlite|sqlite3)(?:[-.].*)?$", re.I)


class SpecValidationError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ValidatedProgrammingTaskSpec:
    data: dict[str, Any]
    canonical_json: str
    spec_hash: str

    def public_payload(self) -> dict[str, Any]:
        return {
            "status": "valid", "schema_version": self.data["schema_version"],
            "project_id": self.data["project_id"], "title": self.data["title"],
            "executor": self.data["executor"],
            "allowed_paths": list(self.data["allowed_paths"]),
            "test_profile": self.data["test_profile"], "limits": dict(self.data["limits"]),
            "objective_length": len(self.data["objective"]), "spec_hash": self.spec_hash,
        }


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SpecValidationError("duplicate_field")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise SpecValidationError("invalid_json_number")


def load_spec(path: str | Path) -> dict[str, Any]:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SpecValidationError("spec_unreadable") from exc
    if not raw.strip():
        raise SpecValidationError("spec_empty")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs_no_duplicates,
                           parse_constant=_reject_constant)
    except SpecValidationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SpecValidationError("invalid_json") from exc
    if not isinstance(value, dict):
        raise SpecValidationError("spec_must_be_object")
    return value


def _clean_text(value: Any, field: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        raise SpecValidationError(f"{field}_invalid")
    text = value.strip()
    if not minimum <= len(text) <= maximum:
        raise SpecValidationError(f"{field}_length_invalid")
    if "\x00" in text or any(ord(ch) < 32 and ch not in "\n\r\t" for ch in text):
        raise SpecValidationError(f"{field}_unsafe_control_character")
    return text


def _path(value: Any, repository_root: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecValidationError("allowed_path_invalid")
    if any(ord(ch) < 32 for ch in value):
        raise SpecValidationError("allowed_path_unsafe_control_character")
    raw = value.strip().replace("\\", "/")
    segments = raw.rstrip("/").split("/")
    if not segments or any(part in {"", ".", ".."} for part in segments) or ":" in raw:
        raise SpecValidationError("allowed_path_traversal")
    win, posix = PureWindowsPath(value), PurePosixPath(raw)
    if win.is_absolute() or win.drive or posix.is_absolute() or raw.startswith("//"):
        raise SpecValidationError("allowed_path_absolute")
    lowered = [part.lower() for part in posix.parts]
    if any(part in BLOCKED_PARTS for part in lowered):
        raise SpecValidationError("allowed_path_blocked")
    for part in lowered:
        if part == ".env" or part.startswith(".env.") or SECRET_RE.search(part) or SQLITE_RE.search(part):
            raise SpecValidationError("allowed_path_sensitive")
    root = repository_root.resolve()
    candidate = (root / Path(*posix.parts)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SpecValidationError("allowed_path_escape") from exc
    normalized = posix.as_posix()
    return normalized + "/" if value.rstrip().endswith(("/", "\\")) else normalized


def validate_spec(raw: dict[str, Any], registry: ProjectExecutionRegistry | None = None) -> ValidatedProgrammingTaskSpec:
    if set(raw) != TOP_FIELDS:
        raise SpecValidationError("unknown_or_missing_fields")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise SpecValidationError("schema_version_unsupported")
    registry = registry or ProjectExecutionRegistry()
    try:
        project = registry.require(raw["project_id"] if isinstance(raw["project_id"], str) else "")
    except ValueError as exc:
        raise SpecValidationError("project_not_allowed") from exc
    title = _clean_text(raw["title"], "title", 3, 120)
    objective = _clean_text(raw["objective"], "objective", 10, 8000)
    executor = raw["executor"]
    if executor not in EXECUTORS:
        raise SpecValidationError("executor_not_allowed")
    paths = raw["allowed_paths"]
    if not isinstance(paths, list) or not paths:
        raise SpecValidationError("allowed_paths_required")
    normalized_paths = [_path(item, project.repository_path) for item in paths]
    if len(set(normalized_paths)) != len(normalized_paths):
        raise SpecValidationError("allowed_paths_duplicate")
    profile = raw["test_profile"]
    if profile not in TEST_PROFILES:
        raise SpecValidationError("test_profile_not_allowed")
    limits = raw["limits"]
    if not isinstance(limits, dict) or set(limits) != LIMIT_FIELDS:
        raise SpecValidationError("limits_invalid")
    normalized_limits: dict[str, int] = {}
    for name, maximum in POLICY_MAXIMUMS.items():
        value = limits[name]
        if type(value) is not int or value < 1 or value > maximum:
            raise SpecValidationError(f"{name}_exceeds_policy")
        normalized_limits[name] = value
    normalized = {
        "schema_version": 1, "project_id": project.project_id, "title": title,
        "objective": objective, "executor": executor, "allowed_paths": normalized_paths,
        "test_profile": profile, "limits": normalized_limits,
    }
    canonical = json.dumps(normalized, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return ValidatedProgrammingTaskSpec(normalized, canonical, digest)


def load_and_validate(path: str | Path, registry: ProjectExecutionRegistry | None = None) -> ValidatedProgrammingTaskSpec:
    return validate_spec(load_spec(path), registry)


def validate_snapshot(snapshot_json: str, expected_hash: str,
                      registry: ProjectExecutionRegistry | None = None) -> ValidatedProgrammingTaskSpec:
    """Revalida o snapshot persistido e recalcula seu hash canônico."""
    if not snapshot_json:
        raise SpecValidationError("spec_not_found")
    try:
        raw = json.loads(snapshot_json, object_pairs_hook=_pairs_no_duplicates,
                         parse_constant=_reject_constant)
    except SpecValidationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SpecValidationError("spec_hash_mismatch") from exc
    if not isinstance(raw, dict):
        raise SpecValidationError("spec_hash_mismatch")
    try:
        validated = validate_spec(raw, registry)
    except SpecValidationError as exc:
        raise SpecValidationError("spec_hash_mismatch") from exc
    if not expected_hash or validated.spec_hash != expected_hash:
        raise SpecValidationError("spec_hash_mismatch")
    return validated
