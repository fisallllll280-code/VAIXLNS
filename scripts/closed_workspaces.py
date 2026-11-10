"""Fail-closed local workspaces for isolated engineering tasks.

This module creates and audits workspace directories only. It does not execute code,
start containers, provision infrastructure, or provide an OS-level security boundary.
Use an actual sandbox/container/VM before running untrusted code.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

MANIFEST_NAME = ".vaixl-workspace.json"
SCHEMA_VERSION = "vaixl.closed-workspace.v1"
WORKSPACE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_id(workspace_id: str) -> str:
    if not isinstance(workspace_id, str) or not WORKSPACE_ID.fullmatch(workspace_id):
        raise ValueError("WORKSPACE_ID_INVALID")
    if workspace_id in {".", ".."}:
        raise ValueError("WORKSPACE_ID_INVALID")
    return workspace_id


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _file_inventory(workspace: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(workspace.rglob("*")):
        if path == workspace / MANIFEST_NAME:
            continue
        if path.is_symlink():
            raise PermissionError("SYMLINK_BLOCKED:" + path.relative_to(workspace).as_posix())
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({
            "path": path.relative_to(workspace).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": digest,
        })
    return records


def create_workspace(root: str | Path, workspace_id: str, *, mission_id: str,
                     source_revision: str, policy_id: str = "closed-default-v1") -> dict[str, Any]:
    """Create a private directory and its initial control manifest; no code is executed."""
    workspace_id = _safe_id(workspace_id)
    if not mission_id.strip() or not source_revision.strip() or not policy_id.strip():
        raise ValueError("MISSION_REVISION_AND_POLICY_REQUIRED")
    root_path = Path(root).expanduser()
    root_path.mkdir(parents=True, exist_ok=True, mode=0o700)
    root_real = root_path.resolve(strict=True)
    if root_path.is_symlink():
        raise PermissionError("WORKSPACE_ROOT_SYMLINK_BLOCKED")
    workspace = root_real / workspace_id
    if not _inside(root_real, workspace):
        raise PermissionError("WORKSPACE_PATH_ESCAPE")
    if workspace.exists() or workspace.is_symlink():
        raise FileExistsError("WORKSPACE_ALREADY_EXISTS")
    workspace.mkdir(mode=0o700)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "workspace_id": workspace_id,
        "mission_id": mission_id.strip(),
        "source_revision": source_revision.strip(),
        "policy_id": policy_id.strip(),
        "state": "CREATED",
        "isolation": {
            "network_access": "DENY_BY_DEFAULT",
            "host_mounts": [],
            "production_credentials": False,
            "canonical_writes": False,
            "production_deployments": False,
            "command_execution": "DISABLED",
        },
        "baseline_files": [],
        "baseline_hash": canonical_hash([]),
        "authority_decision": "PENDING",
    }
    _write_manifest(workspace, manifest)
    return manifest


def _write_manifest(workspace: Path, manifest: dict[str, Any]) -> None:
    target = workspace / MANIFEST_NAME
    fd, temp_name = tempfile.mkstemp(prefix=".manifest-", dir=workspace)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, sort_keys=True, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _load_workspace(root: str | Path, workspace_id: str) -> tuple[Path, dict[str, Any]]:
    workspace_id = _safe_id(workspace_id)
    root_path = Path(root).expanduser()
    if root_path.is_symlink():
        raise PermissionError("WORKSPACE_ROOT_SYMLINK_BLOCKED")
    root_real = root_path.resolve(strict=True)
    workspace = root_real / workspace_id
    if not _inside(root_real, workspace) or workspace.is_symlink() or not workspace.is_dir():
        raise PermissionError("WORKSPACE_PATH_INVALID")
    manifest_path = workspace / MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise PermissionError("WORKSPACE_MANIFEST_MISSING_OR_UNSAFE")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("workspace_id") != workspace_id:
        raise ValueError("WORKSPACE_MANIFEST_IDENTITY_MISMATCH")
    return workspace, manifest


def seal_workspace(root: str | Path, workspace_id: str) -> dict[str, Any]:
    """Capture the current file inventory as a baseline; sealing is not approval."""
    workspace, manifest = _load_workspace(root, workspace_id)
    files = _file_inventory(workspace)
    manifest["baseline_files"] = files
    manifest["baseline_hash"] = canonical_hash(files)
    manifest["state"] = "SEALED"
    manifest["authority_decision"] = "PENDING"
    _write_manifest(workspace, manifest)
    return {"workspace_id": workspace_id, "state": "SEALED",
            "file_count": len(files), "baseline_hash": manifest["baseline_hash"],
            "authority_decision": "PENDING"}


def verify_workspace(root: str | Path, workspace_id: str) -> dict[str, Any]:
    """Compare current files to the sealed baseline; fail closed on drift."""
    workspace, manifest = _load_workspace(root, workspace_id)
    if manifest.get("state") != "SEALED":
        return {"workspace_id": workspace_id, "state": "UNSEALED", "valid": False,
                "errors": ["WORKSPACE_NOT_SEALED"]}
    current = _file_inventory(workspace)
    current_hash = canonical_hash(current)
    baseline = manifest.get("baseline_files", [])
    errors: list[str] = []
    if current_hash != manifest.get("baseline_hash"):
        expected = {item["path"]: item["sha256"] for item in baseline}
        observed = {item["path"]: item["sha256"] for item in current}
        for name in sorted(set(expected) | set(observed)):
            if expected.get(name) != observed.get(name):
                errors.append("FILE_DRIFT:" + name)
    return {"workspace_id": workspace_id, "state": "VERIFIED" if not errors else "DRIFT_DETECTED",
            "valid": not errors, "errors": errors, "baseline_hash": manifest.get("baseline_hash"),
            "observed_hash": current_hash, "authority_decision": "PENDING"}


def inspect_workspace(root: str | Path, workspace_id: str) -> dict[str, Any]:
    _, manifest = _load_workspace(root, workspace_id)
    return manifest
