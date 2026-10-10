"""Apply one source-pinned text repair only after explicit approval.

This utility does not run plan-supplied commands, fetch remote content, install packages,
create/delete files, or declare a repair verified. Tests are run separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "1.0.0"
REVISION_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REPAIR_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
PROTECTED_CANONICAL_PATHS = {
    "project.genome",
    "registry/omega/omega-000-master-index.json",
}


class RepairError(ValueError):
    """A fail-closed repair validation error with a stable machine code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fail(code: str, message: str) -> None:
    raise RepairError(code, message)


def _validate_plan_shape(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        _fail("INVALID_PLAN", "repair plan must be a JSON object")
    required = {"schema_version", "repair_id", "repository", "base_revision", "change"}
    if set(plan) != required:
        _fail("INVALID_PLAN_FIELDS", "repair plan must contain exactly the documented top-level fields")
    if plan.get("schema_version") != SCHEMA_VERSION:
        _fail("UNSUPPORTED_SCHEMA", "unsupported repair plan schema_version")
    if not isinstance(plan.get("repair_id"), str) or not REPAIR_ID_RE.fullmatch(plan["repair_id"]):
        _fail("INVALID_REPAIR_ID", "repair_id must be a short stable identifier")
    if not isinstance(plan.get("repository"), str) or not REPOSITORY_RE.fullmatch(plan["repository"]):
        _fail("INVALID_REPOSITORY", "repository must use owner/repository form")
    if not isinstance(plan.get("base_revision"), str) or not REVISION_RE.fullmatch(plan["base_revision"]):
        _fail("INVALID_BASE_REVISION", "base_revision must be a pinned Git commit SHA")
    change = plan.get("change")
    if not isinstance(change, dict):
        _fail("INVALID_CHANGE", "change must be an object")
    required_change = {"path", "operation", "expected_sha256", "old_text", "new_text"}
    if not required_change.issubset(change) or set(change) - (required_change | {"expected_occurrences"}):
        _fail("INVALID_CHANGE_FIELDS", "change must match the guarded replace_text contract")
    if change.get("operation") != "replace_text":
        _fail("UNSUPPORTED_OPERATION", "only replace_text is supported; arbitrary commands are not accepted")
    if not isinstance(change.get("path"), str):
        _fail("INVALID_PATH", "change.path must be a repository-relative POSIX path")
    if not isinstance(change.get("expected_sha256"), str) or not SHA256_RE.fullmatch(change["expected_sha256"]):
        _fail("INVALID_PREIMAGE_HASH", "expected_sha256 must be a SHA-256 digest")
    if not isinstance(change.get("old_text"), str) or change["old_text"] == "":
        _fail("INVALID_OLD_TEXT", "old_text must be a non-empty UTF-8 string")
    if not isinstance(change.get("new_text"), str) or change["new_text"] == change["old_text"]:
        _fail("INVALID_NEW_TEXT", "new_text must differ from old_text")
    occurrences = change.get("expected_occurrences", 1)
    if isinstance(occurrences, bool) or not isinstance(occurrences, int) or occurrences < 1:
        _fail("INVALID_OCCURRENCE_COUNT", "expected_occurrences must be a positive integer")
    return plan


def _resolve_existing_target(root: Path, path_text: str) -> Path:
    if not path_text or "\\" in path_text or "\x00" in path_text:
        _fail("INVALID_PATH", "path must be non-empty and use forward slashes only")
    relative = PurePosixPath(path_text)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        _fail("PATH_TRAVERSAL_BLOCKED", "absolute paths and traversal segments are forbidden")
    normalized = relative.as_posix().casefold()
    if normalized in PROTECTED_CANONICAL_PATHS:
        _fail("CANONICAL_WRITE_BLOCKED", "canonical authority artifacts are read-only")
    if not relative.parts:
        _fail("INVALID_PATH", "path must identify an existing file")

    target = root
    for part in relative.parts:
        target = target / part
        if target.is_symlink():
            _fail("SYMLINK_PATH_BLOCKED", "symbolic-link paths are not eligible for repair")
    try:
        resolved = target.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        _fail("PATH_OUTSIDE_REPOSITORY", "target must resolve inside the selected repository")
    if not resolved.is_file():
        _fail("TARGET_NOT_FILE", "repair target must be an existing regular file")
    return resolved


def prepare_repair(
    plan: Any, root: str | Path, current_revision: str, *, apply: bool = False
) -> dict[str, Any]:
    """Validate a repair plan and optionally atomically replace text in one file."""
    plan = _validate_plan_shape(plan)
    if not REVISION_RE.fullmatch(str(current_revision)):
        _fail("INVALID_CURRENT_REVISION", "current_revision must be a pinned Git commit SHA")
    if plan["base_revision"].casefold() != current_revision.casefold():
        _fail("REVISION_MISMATCH", "repair plan base_revision does not match the current checkout")

    repository_root = Path(root).resolve(strict=True)
    if not repository_root.is_dir():
        _fail("INVALID_REPOSITORY_ROOT", "root must be a repository directory")

    change = plan["change"]
    target = _resolve_existing_target(repository_root, change["path"])
    try:
        original = target.read_bytes()
        original.decode("utf-8")
    except UnicodeDecodeError:
        _fail("NON_UTF8_TARGET", "binary or non-UTF-8 targets are not supported")
    except OSError as exc:
        _fail("TARGET_READ_FAILED", "target could not be read: " + str(exc))

    actual_hash = sha256_bytes(original)
    if actual_hash.casefold() != change["expected_sha256"].casefold():
        _fail("PREIMAGE_HASH_MISMATCH", "target content no longer matches expected_sha256")

    old_bytes = change["old_text"].encode("utf-8")
    new_bytes = change["new_text"].encode("utf-8")
    if original.count(old_bytes) != change.get("expected_occurrences", 1):
        _fail("ANCHOR_OCCURRENCE_MISMATCH", "old_text occurrence count differs from expected_occurrences")

    replacement = original.replace(old_bytes, new_bytes)
    if replacement == original:
        _fail("NO_OP_REPAIR", "repair would not change the target")

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "repair_id": plan["repair_id"],
        "repository": plan["repository"],
        "source_revision": current_revision.lower(),
        "path": change["path"],
        "status": "PATCH_CANDIDATE_READY",
        "applied": False,
        "plan_sha256": sha256_bytes(canonical_json(plan).encode("utf-8")),
        "preimage_sha256": actual_hash,
        "postimage_sha256": sha256_bytes(replacement),
        "verification_state": "NOT_VERIFIED",
        "required_next_checks": [
            "reproduce_failure",
            "targeted_regression",
            "full_relevant_suite",
            "independent_review",
        ],
    }
    if not apply:
        return receipt

    temp_path = None
    try:
        mode = target.stat().st_mode
        fd, temp_name = tempfile.mkstemp(prefix=".repair-", dir=str(target.parent))
        temp_path = Path(temp_name)
        with os.fdopen(fd, "wb") as handle:
            if hasattr(os, "fchmod"):
                os.fchmod(handle.fileno(), mode & 0o777)
            handle.write(replacement)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except OSError as exc:
        _fail("ATOMIC_WRITE_FAILED", "atomic file replacement failed: " + str(exc))
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    receipt["status"] = "PATCH_APPLIED_NOT_VERIFIED"
    receipt["applied"] = True
    receipt["postimage_sha256_observed"] = sha256_bytes(target.read_bytes())
    return receipt


def _run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        _fail("GIT_CONTEXT_UNAVAILABLE", "cannot establish Git repository context: " + str(exc))
    return result.stdout.strip()


def _origin_repository(remote: str) -> str:
    match = re.search(
        r"(?:github\.com[:/])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$",
        remote.strip(), flags=re.IGNORECASE,
    )
    if not match:
        _fail("REMOTE_IDENTITY_UNRESOLVED", "origin must resolve to a GitHub owner/repository URL")
    return match.group(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preflight or explicitly apply one source-pinned repair to an existing file."
    )
    parser.add_argument("plan", help="path to a guarded repair plan JSON file")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--apply", action="store_true", help="apply the validated replacement; default is dry-run")
    args = parser.parse_args(argv)

    try:
        root = Path(args.root).resolve(strict=True)
        repository_root = Path(_run_git(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
        if repository_root != root:
            _fail("REPOSITORY_ROOT_MISMATCH", "--root must be the Git repository root")
        current_revision = _run_git(root, "rev-parse", "HEAD")
        remote = _run_git(root, "remote", "get-url", "origin")
        with open(args.plan, "r", encoding="utf-8") as stream:
            plan = json.load(stream)
        if not isinstance(plan, dict):
            _fail("INVALID_PLAN", "repair plan must be a JSON object")
        if _origin_repository(remote).casefold() != str(plan.get("repository", "")).casefold():
            _fail("REPOSITORY_IDENTITY_MISMATCH", "repair plan repository does not match origin")
        if args.apply:
            dirty = _run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
            if dirty:
                _fail("DIRTY_WORKTREE", "apply requires a clean working tree; use a disposable worktree")
        receipt = prepare_repair(plan, root, current_revision, apply=args.apply)
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (RepairError, OSError, json.JSONDecodeError) as exc:
        code = exc.code if isinstance(exc, RepairError) else "INPUT_OR_IO_ERROR"
        print(json.dumps({"status": "BLOCKED", "code": code, "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
