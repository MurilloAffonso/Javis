"""Route-level safety gates for the legacy Javis backend."""
from __future__ import annotations

import uuid
import hmac
import os
from pathlib import Path

import safe_config

JAVIS_ROOT = Path(__file__).resolve().parents[3]
CEREBRO_JAMPA_SCOPE = "project:cerebro-jampa"
CORE_SCOPE = "javes-core"
INGEST_DEFAULT_DIR = JAVIS_ROOT / "_inbox" / "ingestao"
UPLOAD_TMP_DIR = JAVIS_ROOT / "_apps" / "javis-local-interface" / "_tmp" / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
LOCAL_TOKEN_HEADER = "X-Javes-Local-Token"
LOCAL_TOKEN_ENVS = ("JAVES_LOCAL_TOKEN", "JAVIS_LOCAL_TOKEN")

BLOCKED_UPLOAD_EXTENSIONS = {
    ".bat", ".cmd", ".com", ".dll", ".exe", ".js", ".msi", ".ps1", ".py",
    ".scr", ".sh", ".vbs", ".wsf",
}
ALLOWED_UPLOAD_EXTENSIONS = {
    ".bmp", ".csv", ".docx", ".gif", ".jpeg", ".jpg", ".json", ".md",
    ".pdf", ".png", ".pptx", ".txt", ".webp", ".xls", ".xlsx",
}

_TRUE_APPROVAL_VALUES = {"1", "true", "yes", "y", "on", "sim", "approved", "ok"}


def disabled_by_default(action: str, capability: str = "", flag: str = "") -> dict:
    out = {
        "status": "disabled_by_default",
        "reason": "requires_explicit_enable",
        "action": action,
    }
    if capability:
        out["capability"] = capability
    if flag:
        out["flag"] = flag
    return out


def blocked(reason: str, action: str = "", **extra) -> dict:
    out = {"status": "blocked", "reason": reason}
    if action:
        out["action"] = action
    out.update(extra)
    return out


def project_id_required(scope: str = CEREBRO_JAMPA_SCOPE) -> dict:
    return {
        "status": "blocked",
        "reason": "project_id_required",
        "scope": scope,
    }


def project_id_mismatch(project_id: str, scope: str = CEREBRO_JAMPA_SCOPE) -> dict:
    return blocked(
        "project_id_mismatch",
        project_id=project_id,
        scope=scope,
    )


def approval_required(action: str, **extra) -> dict:
    out = {
        "status": "approval_required",
        "reason": "human_approval_required",
        "action": action,
    }
    out.update({k: v for k, v in extra.items() if v not in ("", None)})
    return out


def _configured_local_token() -> str:
    for name in LOCAL_TOKEN_ENVS:
        token = os.environ.get(name, "").strip()
        if token:
            return token
    return ""


def require_local_auth(token: str | None, action: str = "local_auth") -> dict | None:
    configured = _configured_local_token()
    provided = token.strip() if isinstance(token, str) else ""
    if not provided:
        return blocked("unauthorized_local_token_required", action)
    if not configured:
        return blocked("local_token_not_configured", action)
    if not hmac.compare_digest(provided, configured):
        return blocked("unauthorized_local_token_invalid", action)
    return None


def explicit_approval(value: bool | str | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in _TRUE_APPROVAL_VALUES


def require_approval(action: str, approved: bool | str | None = False) -> dict | None:
    return approval_required(action, approved_param_ignored=explicit_approval(approved))


def require_persisted_approval(
    action: str,
    approval_id: int | None = None,
    route: str = "",
    project_id: str = "",
    risk_level: str = "medium",
    reason: str = "human_approval_required",
    metadata: dict | None = None,
    approved: bool | str | None = False,
) -> dict | None:
    import repositories as repo

    if approval_id:
        approval = repo.approvals.get(approval_id)
        if repo.approvals.valid_for_action(approval, action, route=route, project_id=project_id):
            if repo.approvals.consume(approval_id) >= 1:
                try:
                    repo.logs.add(
                        source="gate",
                        intent=action,
                        agent=approval.get("requested_by", "") if approval else "",
                        message=(
                            f"approval_id={approval_id} route={route or ''} "
                            f"project_id={project_id or ''} result=approved"
                        ),
                        status="approved",
                        approved=True,
                    )
                except Exception:
                    pass
                return None
            approval = repo.approvals.get(approval_id)
            status = "consumed"
        else:
            if approval and approval.get("consumed_at"):
                status = "consumed"
            else:
                status = approval.get("status") if approval else "missing"
        return approval_required(
            action,
            approval_id=approval_id,
            approval_status=status,
            route=route,
            project_id=project_id,
        )

    existing = repo.approvals.find_pending_action(action, route=route, project_id=project_id)
    created = False
    if existing:
        gate_id = existing["id"]
    else:
        gate_id = repo.approvals.add(
            subject=f"{action} precisa de aprovação humana",
            kind="route_gate",
            detail=reason,
            project_id=project_id,
            action=action,
            route=route,
            risk_level=risk_level,
            requested_by="route",
            reason=reason,
            metadata=metadata or {},
        )
        created = True
    return approval_required(
        action,
        approval_id=gate_id,
        approval_status="pending",
        approval_created=created,
        approved_param_ignored=explicit_approval(approved),
        route=route,
        project_id=project_id,
    )


def require_external_adapters(action: str) -> dict | None:
    if safe_config.external_adapters_enabled():
        return None
    return disabled_by_default(
        action,
        "external_adapters",
        safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS,
    )


def require_local_actions(action: str) -> dict | None:
    if safe_config.local_actions_enabled():
        return None
    return disabled_by_default(
        action,
        "local_actions",
        safe_config.JAVIS_ENABLE_LOCAL_ACTIONS,
    )


def require_vp_effects(action: str) -> dict | None:
    if safe_config.vp_effects_enabled():
        return None
    return disabled_by_default(
        action,
        "vp_effects",
        safe_config.JAVIS_ENABLE_VP_EFFECTS,
    )


def require_project_scope(
    project_id: str | None,
    scope: str | list[str] | tuple[str, ...] | set[str] = CEREBRO_JAMPA_SCOPE,
) -> dict | None:
    normalized = (project_id or "").strip()
    if not normalized:
        return project_id_required(scope)
    if isinstance(scope, (list, tuple, set)):
        allowed = {str(item).strip() for item in scope if str(item).strip()}
        if normalized not in allowed:
            return project_id_mismatch(normalized, sorted(allowed))
    elif normalized != scope:
        return project_id_mismatch(normalized, scope)
    return None


def validate_ingest_folder(folder: str | None) -> tuple[Path | None, dict | None]:
    raw = (folder or "").strip()
    if not raw:
        return INGEST_DEFAULT_DIR, None

    requested = Path(raw)
    if ".." in requested.parts:
        return None, blocked("path_traversal", "knowledge.ingest")

    candidate = requested if requested.is_absolute() else JAVIS_ROOT / requested
    try:
        resolved = candidate.resolve()
        root = JAVIS_ROOT.resolve()
    except OSError:
        return None, blocked("path_invalid", "knowledge.ingest")

    try:
        resolved.relative_to(root)
    except ValueError:
        return None, blocked("path_outside_javis_root", "knowledge.ingest")

    return resolved, None


def validate_upload_filename(filename: str | None) -> dict | None:
    name = (filename or "").strip()
    if not name:
        return blocked("filename_required", "upload")
    if "/" in name or "\\" in name or Path(name).name != name:
        return blocked("path_not_allowed", "upload")
    suffix = Path(name).suffix.lower()
    if not suffix:
        return blocked("extension_required", "upload")
    if suffix in BLOCKED_UPLOAD_EXTENSIONS:
        return blocked("blocked_file_type", "upload", extension=suffix)
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        return blocked("unsupported_file_type", "upload", extension=suffix)
    return None


def reserve_upload_path(filename: str | None) -> Path:
    suffix = Path(filename or "upload.bin").suffix.lower() or ".bin"
    return UPLOAD_TMP_DIR / f"{uuid.uuid4().hex}{suffix}"


def upload_too_large(size: int) -> dict:
    return blocked(
        "upload_too_large",
        "upload",
        max_bytes=MAX_UPLOAD_BYTES,
        size=size,
    )
