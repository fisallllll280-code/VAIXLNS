#!/usr/bin/env python3
"""Safe, read-only GitHub repository fleet intake.

Plan-only by default. Execution mirrors public repositories into a separate
local directory without checking out or executing source code. Existing mirrors
are never fetched, reset, overwritten, or deleted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER_DEFAULT = "fisallllll280-code"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULT_REPOSITORIES = (
    "VAIXLNS", "VAIXLNS-unified", "NEXENT", "VX-runtime",
    "vx-agents-fabric", "vx-agents-system", "NAXLNS",
    "VX50_COMPLETE_BUILD", "vaixlns-core", "vaixlns-csd-kernel",
    "VAIXLNS-Intent-to-Reality", "vx-financial-kernel",
)
NETWORK_GATE = "VX_REPOSITORY_INTAKE_NETWORK_ENABLED"


class IntakeError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_scope(owner: str, repositories: list[str], max_repositories: int) -> list[str]:
    if not REPO_PATTERN.fullmatch(owner):
        raise IntakeError("INVALID_OWNER")
    if not repositories:
        raise IntakeError("EXPLICIT_REPOSITORY_LIST_REQUIRED")
    if len(repositories) > max_repositories:
        raise IntakeError("REPOSITORY_BATCH_LIMIT_EXCEEDED")
    if len(set(repositories)) != len(repositories):
        raise IntakeError("DUPLICATE_REPOSITORY")
    for name in repositories:
        if not REPO_PATTERN.fullmatch(name) or name in {".", ".."}:
            raise IntakeError("INVALID_REPOSITORY_NAME:" + str(name))
    return [f"{owner}/{name}" for name in repositories]


def fetch_metadata(repository: str, timeout: int = 15) -> dict[str, Any]:
    request = Request(
        f"https://api.github.com/repos/{repository}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "VAIXLNS-Repository-Fleet-Intake/1.0",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise IntakeError("METADATA_READ_FAILED:" + repository) from exc
    if not isinstance(payload, dict) or payload.get("full_name", "").casefold() != repository.casefold():
        raise IntakeError("REPOSITORY_IDENTITY_MISMATCH:" + repository)
    return payload


def build_plan(
    owner: str,
    repositories: list[str],
    *,
    max_repositories: int = 20,
    max_total_size_mb: int = 20480,
    metadata_reader: Callable[[str], dict[str, Any]] = fetch_metadata,
) -> dict[str, Any]:
    full_names = validate_scope(owner, repositories, max_repositories)
    if max_total_size_mb < 1:
        raise IntakeError("INVALID_SIZE_LIMIT")
    items: list[dict[str, Any]] = []
    total_size_mb = 0
    for full_name in full_names:
        try:
            meta = metadata_reader(full_name)
            size_mb = max(0, int(meta.get("size", 0))) / 1024
            total_size_mb += size_mb
            visibility = "PRIVATE" if meta.get("private") is True else "PUBLIC"
            status = "READY" if visibility == "PUBLIC" else "SKIPPED_PRIVATE"
            items.append({
                "repository": full_name,
                "status": status,
                "visibility": visibility,
                "archived": bool(meta.get("archived", False)),
                "default_branch": meta.get("default_branch"),
                "pushed_at": meta.get("pushed_at"),
                "size_mb": round(size_mb, 3),
                "license_spdx": (meta.get("license") or {}).get("spdx_id"),
                "clone_url": meta.get("clone_url"),
                "source_revision": meta.get("default_branch"),
                "code_execution": False,
                "remote_write": False,
            })
        except (IntakeError, TypeError, ValueError) as exc:
            items.append({
                "repository": full_name,
                "status": "BLOCKED",
                "reason": str(exc),
                "code_execution": False,
                "remote_write": False,
            })
    if total_size_mb > max_total_size_mb:
        for item in items:
            if item.get("status") == "READY":
                item["status"] = "BLOCKED_SIZE_BUDGET"
                item["reason"] = "BATCH_SIZE_LIMIT_EXCEEDED"
    plan_body = {
        "schema": "VAIXLNS.RepositoryFleetIntakePlan.v1",
        "owner": owner,
        "mode": "PLAN_ONLY",
        "repository_count": len(items),
        "estimated_total_size_mb": round(total_size_mb, 3),
        "max_total_size_mb": max_total_size_mb,
        "items": items,
        "safety": {
            "remote_write": False,
            "source_delete": False,
            "existing_mirror_update": False,
            "checkout": False,
            "source_code_execution": False,
            "private_repository_access": False,
        },
    }
    return {**plan_body, "plan_sha256": sha256_bytes(canonical_json(plan_body))}


def _run_git(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def execute_intake(
    plan: dict[str, Any],
    destination: str | Path,
    *,
    network_enabled: bool,
    git_runner: Callable[..., subprocess.CompletedProcess[str]] = _run_git,
) -> dict[str, Any]:
    if network_enabled is not True:
        raise IntakeError("NETWORK_GATE_CLOSED")
    if plan.get("schema") != "VAIXLNS.RepositoryFleetIntakePlan.v1":
        raise IntakeError("INVALID_PLAN_SCHEMA")
    if plan.get("mode") != "PLAN_ONLY" or not plan.get("plan_sha256"):
        raise IntakeError("INVALID_OR_ALREADY_EXECUTED_PLAN")
    if plan.get("safety", {}).get("remote_write") is not False:
        raise IntakeError("UNSAFE_PLAN")
    root = Path(destination).expanduser().resolve()
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise IntakeError("DESTINATION_MUST_BE_A_DIRECTORY")
    root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for item in plan.get("items", []):
        if item.get("status") != "READY":
            results.append({**item, "intake_status": "NOT_ATTEMPTED"})
            continue
        full_name = item["repository"]
        owner, repo = full_name.split("/", 1)
        target = root / f"{owner}--{repo}.git"
        if target.exists() or target.is_symlink():
            results.append({**item, "intake_status": "EXISTS_NOT_MODIFIED", "local_path": str(target)})
            continue
        clone_url = item.get("clone_url")
        if not isinstance(clone_url, str) or not clone_url.startswith("https://github.com/"):
            results.append({**item, "intake_status": "BLOCKED_INVALID_CLONE_URL"})
            continue
        command = ["git", "clone", "--mirror", "--no-hardlinks", clone_url, str(target)]
        try:
            cloned = git_runner(command, timeout=1800)
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({**item, "intake_status": "CLONE_FAILED", "reason": type(exc).__name__})
            continue
        if cloned.returncode != 0:
            # Preserve any partial directory for explicit inspection; never auto-delete it.
            results.append({
                **item, "intake_status": "CLONE_FAILED_PARTIAL_PRESERVED",
                "reason": (cloned.stderr or cloned.stdout or "git clone failed")[-2000:],
                "local_path": str(target) if target.exists() else None,
            })
            continue
        head = git_runner(["git", "--git-dir", str(target), "rev-parse", "HEAD"], timeout=30)
        bare = git_runner(["git", "--git-dir", str(target), "rev-parse", "--is-bare-repository"], timeout=30)
        if head.returncode != 0 or bare.returncode != 0 or bare.stdout.strip() != "true":
            results.append({
                **item, "intake_status": "CLONED_BUT_VERIFICATION_FAILED",
                "local_path": str(target),
            })
            continue
        results.append({
            **item, "intake_status": "MIRRORED",
            "local_path": str(target),
            "observed_head_sha": head.stdout.strip(),
            "mirror_verified_bare": True,
            "checkout_performed": False,
            "source_code_executed": False,
        })
    body = {
        "schema": "VAIXLNS.RepositoryFleetIntakeReceipt.v1",
        "mode": "LOCAL_READ_ONLY_MIRROR",
        "plan_sha256": plan["plan_sha256"],
        "destination": str(root),
        "results": results,
        "safety": {
            "remote_write": False,
            "source_delete": False,
            "existing_mirror_update": False,
            "checkout": False,
            "source_code_execution": False,
        },
    }
    return {**body, "receipt_sha256": sha256_bytes(canonical_json(body))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default=OWNER_DEFAULT)
    parser.add_argument("--repositories", nargs="+", default=list(DEFAULT_REPOSITORIES))
    parser.add_argument("--max-repositories", type=int, default=20)
    parser.add_argument("--max-total-size-mb", type=int, default=20480)
    parser.add_argument("--destination", default="VAIXLNS_REPOSITORY_FLEET")
    parser.add_argument("--execute", action="store_true", help="Mirror public repositories locally.")
    parser.add_argument("--receipt", help="Create a new receipt file; existing files are never overwritten.")
    args = parser.parse_args(argv)
    try:
        plan = build_plan(
            args.owner, args.repositories,
            max_repositories=args.max_repositories,
            max_total_size_mb=args.max_total_size_mb,
        )
        if args.execute:
            if os.environ.get(NETWORK_GATE) != "1":
                raise IntakeError("SET_EXPLICIT_NETWORK_GATE_TO_EXECUTE")
            receipt = execute_intake(plan, args.destination, network_enabled=True)
            output = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        else:
            output = json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.receipt:
            path = Path(args.receipt)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                stream.write(output)
        else:
            sys.stdout.write(output)
        return 0
    except (IntakeError, OSError, ValueError) as exc:
        sys.stderr.write(f"REPOSITORY_INTAKE_BLOCKED: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
