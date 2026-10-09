#!/usr/bin/env python3
"""Bind an Omega Change Capsule to an actual immutable Git diff.

The tool performs read-only local Git queries. It does not use the network, modify refs,
execute repository code, admit a change, or claim that tests or other evidence are valid.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA64 = re.compile(r"^[a-f0-9]{64}$")
PROTECTED_PATHS = {"project.genome", "registry/omega/omega-000-master-index.json"}


class DiffEvidenceError(ValueError):
    """Input cannot be safely resolved or parsed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _safe_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(Path.home()),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
    }


def _git(repo_root: Path, *args: str, binary: bool = False) -> bytes | str:
    process = subprocess.run(
        ["git", "--no-pager", *args],
        cwd=str(repo_root),
        env=_safe_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        error = process.stderr.decode("utf-8", errors="replace").strip()
        raise DiffEvidenceError(f"git command failed ({process.returncode}): {error}")
    return process.stdout if binary else process.stdout.decode("utf-8", errors="strict").strip()


def _valid_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise DiffEvidenceError(f"{field}: expected normalized non-empty path")
    if chr(92) in value or chr(0) in value:
        raise DiffEvidenceError(f"{field}: backslash and NUL are prohibited")
    path = PurePosixPath(value)
    if value.startswith("/") or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise DiffEvidenceError(f"{field}: absolute/traversal path is prohibited: {value}")
    if str(path) != value or "//" in value:
        raise DiffEvidenceError(f"{field}: non-normalized path is prohibited: {value}")
    return value


def _in_scope(path: str, grants: list[str]) -> bool:
    return any(path == grant or path.startswith(grant.rstrip("/") + "/") for grant in grants)


def _resolve_commit(repo_root: Path, revision: str, field: str) -> str:
    if not isinstance(revision, str) or not SHA40.fullmatch(revision):
        raise DiffEvidenceError(f"{field}: expected a full 40-character lowercase commit SHA")
    resolved = _git(repo_root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}")
    if resolved != revision:
        raise DiffEvidenceError(f"{field}: Git resolved a different commit")
    return resolved


def calculate_diff(repo_root: Path, base_revision: str, candidate_revision: str) -> dict[str, Any]:
    """Calculate digest and exact paths from Git objects, never from manifest claims."""
    root = repo_root.resolve(strict=True)
    if not root.is_dir():
        raise DiffEvidenceError("repo_root: expected a directory")
    top = Path(str(_git(root, "rev-parse", "--show-toplevel"))).resolve(strict=True)
    if top != root:
        raise DiffEvidenceError("repo_root must be the exact working-tree root")
    base = _resolve_commit(root, base_revision, "base_revision")
    candidate = _resolve_commit(root, candidate_revision, "candidate_revision")
    diff_bytes = _git(
        root,
        "diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv",
        "--no-renames", "--ignore-submodules=none", base, candidate, "--",
        binary=True,
    )
    path_bytes = _git(
        root, "diff", "--name-only", "-z", "--no-renames",
        base, candidate, "--", binary=True,
    )
    raw_paths = [item for item in path_bytes.split(b"\0") if item]
    try:
        paths = sorted(_valid_path(item.decode("utf-8", errors="strict"), "git.changed_path") for item in raw_paths)
    except UnicodeDecodeError as exc:
        raise DiffEvidenceError("git.changed_path: non-UTF-8 file name cannot be attested safely") from exc
    if len(paths) != len(set(paths)):
        raise DiffEvidenceError("git changed-path listing unexpectedly contains duplicates")
    return {
        "base_revision": base,
        "candidate_revision": candidate,
        "diff_sha256": hashlib.sha256(diff_bytes).hexdigest(),
        "changed_paths": paths,
        "diff_bytes": len(diff_bytes),
        "diff_non_empty": bool(diff_bytes) and bool(paths),
    }


def verify_capsule(repo_root: Path, capsule: Any, candidate_revision: str) -> dict[str, Any]:
    if not isinstance(capsule, dict):
        raise DiffEvidenceError("capsule root: expected object")
    repository = capsule.get("repository")
    change = capsule.get("change")
    if not isinstance(repository, dict) or not isinstance(change, dict):
        raise DiffEvidenceError("capsule must contain repository and change objects")
    base = repository.get("base_revision")
    _resolve_commit(repo_root.resolve(strict=True), base, "capsule.repository.base_revision")
    actual = calculate_diff(repo_root, base, candidate_revision)

    raw_expected = change.get("changed_paths")
    raw_allowed = change.get("allowed_paths")
    if not isinstance(raw_expected, list) or not isinstance(raw_allowed, list):
        raise DiffEvidenceError("capsule change paths must be arrays")
    expected_paths = sorted(_valid_path(p, "capsule.changed_paths") for p in raw_expected)
    allowed_paths = [_valid_path(p, "capsule.allowed_paths") for p in raw_allowed]
    if len(expected_paths) != len(set(expected_paths)):
        raise DiffEvidenceError("capsule.changed_paths contains duplicates")
    if not isinstance(change.get("diff_sha256"), str) or not SHA64.fullmatch(change["diff_sha256"]):
        raise DiffEvidenceError("capsule.change.diff_sha256 must be a lowercase SHA-256 digest")

    digest_matches = change["diff_sha256"] == actual["diff_sha256"]
    paths_match = expected_paths == actual["changed_paths"]
    scope_violations = sorted(path for path in actual["changed_paths"] if not _in_scope(path, allowed_paths))
    protected_paths = sorted(path for path in actual["changed_paths"] if path in PROTECTED_PATHS)
    non_empty = actual["diff_non_empty"]
    passed = digest_matches and paths_match and not scope_violations and non_empty
    return {
        "schema_version": "1.0.0",
        "verification_type": "GIT_OBJECT_DERIVED_CHANGE_CAPSULE_BINDING",
        "state": "MATCH" if passed else "MISMATCH",
        "admission_decision": "NOT_EVALUATED",
        "repository": repository.get("repository"),
        "base_revision": actual["base_revision"],
        "candidate_revision": actual["candidate_revision"],
        "actual_diff_sha256": actual["diff_sha256"],
        "capsule_diff_sha256": change["diff_sha256"],
        "digest_matches": digest_matches,
        "actual_changed_paths": actual["changed_paths"],
        "capsule_changed_paths": expected_paths,
        "changed_paths_match": paths_match,
        "scope_violations": scope_violations,
        "protected_paths_changed": protected_paths,
        "diff_bytes": actual["diff_bytes"],
        "non_empty_diff": non_empty,
        "note": "A match binds the manifest to this Git diff only; it does not authenticate evidence references, run tests, approve protected changes, or grant admission.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--capsule", type=Path, required=True)
    parser.add_argument("--candidate-revision", required=True, help="Full 40-character Git commit SHA")
    args = parser.parse_args(argv)
    try:
        capsule = json.loads(args.capsule.read_text(encoding="utf-8"))
        result = verify_capsule(args.repo_root, capsule, args.candidate_revision)
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
        return 0 if result["state"] == "MATCH" else 1
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, DiffEvidenceError) as exc:
        print(f"DIFF EVIDENCE INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
