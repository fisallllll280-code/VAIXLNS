#!/usr/bin/env python3
"""Read-only repository lifecycle/security posture inventory using the GitHub CLI.

This tool never changes visibility, access, branch rules, archive state or contents.
It can include private repository names in its report; keep the output private.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from typing import Any, Sequence

SCHEMA = "vaixlns.omega-repository-lifecycle-audit.v1"

def run_gh_json(args: Sequence[str]) -> tuple[Any | None, str | None, int]:
    try:
        result = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False, timeout=45)
    except FileNotFoundError:
        return None, "GitHub CLI (gh) is not installed", 127
    except subprocess.TimeoutExpired:
        return None, "GitHub CLI request timed out", 124
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip(), result.returncode
    try:
        return json.loads(result.stdout), None, 0
    except json.JSONDecodeError as exc:
        return None, f"GitHub CLI returned invalid JSON: {exc}", 65

def flatten_repo_pages(payload: Any) -> list[dict[str, Any]]:
    """Accept a single repo array or gh --paginate --slurp array-of-pages."""
    if not isinstance(payload, list):
        raise ValueError("repository inventory response must be a JSON array")
    pages = payload if payload and all(isinstance(page, list) for page in payload) else [payload]
    repos: list[dict[str, Any]] = []
    for page in pages:
        for item in page:
            if not isinstance(item, dict):
                raise ValueError("repository inventory page contains a non-object entry")
            if isinstance(item.get("full_name"), str):
                repos.append(item)
    seen = set()
    unique = []
    for repo in repos:
        if repo["full_name"] not in seen:
            seen.add(repo["full_name"])
            unique.append(repo)
    return sorted(unique, key=lambda item: item["full_name"].lower())

def classify_access_error(error: str | None, code: int) -> str:
    message = (error or "").lower()
    if code == 0:
        return "READABLE"
    if "403" in message or "forbidden" in message or "resource not accessible" in message:
        return "UNKNOWN_INSUFFICIENT_PERMISSION"
    if "404" in message or "not found" in message:
        return "NOT_FOUND_OR_NOT_CONFIGURED"
    if code == 127:
        return "GH_CLI_NOT_INSTALLED"
    if code == 124:
        return "REQUEST_TIMEOUT"
    return "UNKNOWN_ERROR"

def security_features(repo: dict[str, Any]) -> dict[str, Any]:
    value = repo.get("security_and_analysis")
    if not isinstance(value, dict):
        return {"state": "NOT_EXPOSED_BY_API", "features": {}}
    out = {}
    for name, detail in sorted(value.items()):
        out[name] = detail.get("status", "UNKNOWN") if isinstance(detail, dict) else "UNKNOWN"
    return {"state": "EXPOSED_BY_API", "features": out}

def inspect_repository(repo: dict[str, Any], include_settings: bool) -> dict[str, Any]:
    full_name = repo["full_name"]
    default_branch = repo.get("default_branch")
    record: dict[str, Any] = {
        "full_name": full_name,
        "visibility": repo.get("visibility", "UNKNOWN"),
        "private": repo.get("private"),
        "archived": repo.get("archived"),
        "default_branch": default_branch,
        "permissions": {key: repo.get("permissions", {}).get(key) for key in ("admin", "maintain", "push", "pull")},
        "security_features": security_features(repo),
        "branch_protection": {"state": "NOT_CHECKED"},
        "repository_rulesets": {"state": "NOT_CHECKED", "count": None},
        "closure_recommendation": "REVIEW_REQUIRED_NO_AUTOMATIC_ACTION",
    }
    if repo.get("archived") is True:
        record["closure_recommendation"] = "ALREADY_ARCHIVED_VERIFY_DEPENDENCIES_AND_BACKUP"
    elif repo.get("private") is True:
        record["closure_recommendation"] = "PRIVATE_REVIEW_ACCESS_AND_BRANCH_PROTECTION"
    else:
        record["closure_recommendation"] = "PUBLIC_REVIEW_INTENT_AND_SENSITIVE_DATA"
    if not include_settings:
        return record
    if isinstance(default_branch, str) and default_branch:
        encoded = quote(default_branch, safe="")
        protection, error, code = run_gh_json([f"repos/{full_name}/branches/{encoded}/protection"])
        access_state = classify_access_error(error, code)
        if access_state == "READABLE" and isinstance(protection, dict):
            checks = protection.get("required_status_checks") or {}
            reviews = protection.get("required_pull_request_reviews") or {}
            record["branch_protection"] = {
                "state": "PROTECTION_READABLE",
                "enforce_admins": (protection.get("enforce_admins") or {}).get("enabled") if isinstance(protection.get("enforce_admins"), dict) else None,
                "required_status_checks": checks.get("contexts", []) if isinstance(checks, dict) else [],
                "strict_status_checks": checks.get("strict") if isinstance(checks, dict) else None,
                "required_approvals": reviews.get("required_approving_review_count") if isinstance(reviews, dict) else None,
                "conversation_resolution_required": bool(protection.get("required_conversation_resolution", {}).get("enabled")) if isinstance(protection.get("required_conversation_resolution"), dict) else None,
            }
        else:
            record["branch_protection"] = {"state": access_state, "details": (error or "")[:300]}
    else:
        record["branch_protection"] = {"state": "UNKNOWN_DEFAULT_BRANCH"}
    rulesets, error, code = run_gh_json([f"repos/{full_name}/rulesets?per_page=100"])
    access_state = classify_access_error(error, code)
    if access_state == "READABLE" and isinstance(rulesets, list):
        record["repository_rulesets"] = {"state": "READABLE", "count": len(rulesets),
                                         "names": [r.get("name") for r in rulesets if isinstance(r, dict)]}
    else:
        record["repository_rulesets"] = {"state": access_state, "count": None, "details": (error or "")[:300]}
    return record

def build_report(repos: list[dict[str, Any]], owner_filter: str | None, include_settings: bool) -> dict[str, Any]:
    if owner_filter:
        repos = [repo for repo in repos if isinstance(repo.get("owner"), dict)
                 and repo["owner"].get("login", "").lower() == owner_filter.lower()]
    inspected = [inspect_repository(repo, include_settings) for repo in repos]
    public_count = sum(row["visibility"] == "public" for row in inspected)
    private_count = sum(row["visibility"] == "private" for row in inspected)
    archived_count = sum(row["archived"] is True for row in inspected)
    core = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "READ_ONLY_AUDIT",
        "owner_filter": owner_filter,
        "settings_checked": include_settings,
        "summary": {
            "repository_count": len(inspected), "public_count": public_count,
            "private_count": private_count, "archived_count": archived_count,
            "unarchived_count": len(inspected) - archived_count,
            "branch_protection_unknown_count": sum(row["branch_protection"]["state"] not in {"PROTECTION_READABLE", "NOT_CHECKED"} for row in inspected),
            "repository_rulesets_readable_count": sum(row["repository_rulesets"]["state"] == "READABLE" for row in inspected),
            "repositories_modified": 0, "repositories_archived_by_tool": 0,
            "repositories_made_private_by_tool": 0, "deletion_supported": False,
        },
        "repositories": inspected,
        "limitations": [
            "This audit never changes repository settings, access, visibility or archive state.",
            "UNKNOWN or inaccessible settings are not treated as protection being enabled or disabled.",
            "Keep this report private: repository names and access metadata may be sensitive.",
            "Before closure, verify forks, dependencies, issue/PR state, releases, artifacts, domains, webhooks and restoration evidence.",
        ],
    }
    return core

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", help="Optional exact owner login filter")
    parser.add_argument("--check-settings", action="store_true", help="Read branch protection and repository ruleset state")
    parser.add_argument("--output", default=str(Path.home() / ".vaixlns" / "repository-lifecycle-audit.private.json"))
    args = parser.parse_args()
    payload, error, code = run_gh_json(["--paginate", "--slurp", "/user/repos", "-f", "affiliation=owner", "-F", "per_page=100"])
    if code != 0 or payload is None:
        print(json.dumps({"state": "ERROR", "details": error, "exit_code": code}), file=sys.stderr)
        return 2
    try:
        repos = flatten_repo_pages(payload)
        report = build_report(repos, args.owner, args.check_settings)
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(json.dumps({"state": "ERROR", "details": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"state": "AUDIT_ONLY", "output": str(output), **report["summary"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
