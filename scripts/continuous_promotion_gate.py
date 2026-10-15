#!/usr/bin/env python3
"""Deterministically decide which open pull requests are safe to promote.

This module is intentionally read-only. It never calls GitHub, merges a PR,
deploys software, or grants approval; a separate trusted workflow acts only on
PRs whose metadata and completed checks satisfy this fail-closed policy.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUCCESS_CONCLUSIONS = {"SUCCESS", "SKIPPED", "NEUTRAL"}


def _check_is_successful(check: Any) -> tuple[bool, str]:
    if not isinstance(check, dict):
        return False, "MALFORMED_CHECK"

    name = str(check.get("name") or check.get("context") or "unnamed")
    kind = check.get("__typename")

    if kind == "CheckRun":
        if check.get("status") != "COMPLETED":
            return False, f"CHECK_NOT_COMPLETED:{name}"
        conclusion = check.get("conclusion")
        if conclusion not in SUCCESS_CONCLUSIONS:
            return False, f"CHECK_NOT_SUCCESSFUL:{name}:{conclusion or 'UNKNOWN'}"
        return True, ""

    if kind == "StatusContext":
        if check.get("state") != "SUCCESS":
            return False, f"STATUS_NOT_SUCCESSFUL:{name}:{check.get('state') or 'UNKNOWN'}"
        return True, ""

    return False, f"UNKNOWN_CHECK_TYPE:{name}:{kind or 'UNKNOWN'}"


def evaluate_pull_request(pr: dict[str, Any]) -> dict[str, Any]:
    """Return READY_TO_MERGE only when every defined gate is satisfied."""
    reasons: list[str] = []
    number = pr.get("number")

    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        reasons.append("INVALID_PULL_REQUEST_NUMBER")
    if pr.get("baseRefName") != "main":
        reasons.append("BASE_BRANCH_NOT_MAIN")
    if pr.get("isDraft") is not False:
        reasons.append("PULL_REQUEST_IS_DRAFT_OR_DRAFT_STATE_UNKNOWN")
    if pr.get("reviewDecision") != "APPROVED":
        reasons.append("HUMAN_REVIEW_APPROVAL_REQUIRED")
    if pr.get("mergeable") != "MERGEABLE":
        reasons.append("PULL_REQUEST_NOT_CONFIRMED_MERGEABLE")
    if not isinstance(pr.get("headRefOid"), str) or not pr.get("headRefOid", "").strip():
        reasons.append("HEAD_COMMIT_SHA_MISSING")

    checks = pr.get("statusCheckRollup")
    if not isinstance(checks, list) or not checks:
        reasons.append("NO_CHECK_RESULTS_FOUND")
    else:
        for check in checks:
            successful, reason = _check_is_successful(check)
            if not successful:
                reasons.append(reason)

    reasons = list(dict.fromkeys(reasons))
    decision = "READY_TO_MERGE" if not reasons else "HOLD"

    return {
        "number": number if isinstance(number, int) and not isinstance(number, bool) else None,
        "title": str(pr.get("title") or ""),
        "url": str(pr.get("url") or ""),
        "head_sha": pr.get("headRefOid") if isinstance(pr.get("headRefOid"), str) else None,
        "decision": decision,
        "reasons": reasons,
        "checks_seen": len(checks) if isinstance(checks, list) else 0,
    }


def build_plan(pull_requests: Any) -> dict[str, Any]:
    if not isinstance(pull_requests, list):
        raise ValueError("Input must be a JSON array of pull requests.")

    evaluated = [
        evaluate_pull_request(pr) if isinstance(pr, dict) else {
            "number": None,
            "title": "",
            "url": "",
            "head_sha": None,
            "decision": "HOLD",
            "reasons": ["MALFORMED_PULL_REQUEST_RECORD"],
            "checks_seen": 0,
        }
        for pr in pull_requests
    ]
    evaluated.sort(key=lambda item: (item["number"] is None, item["number"] or 0))
    eligible = [
        item["number"] for item in evaluated
        if item["decision"] == "READY_TO_MERGE" and item["number"] is not None
    ]

    return {
        "schema_version": "vaixlns-continuous-promotion-plan-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "base_branch": "main",
            "human_approval_required": True,
            "draft_pull_requests_allowed": False,
            "all_observed_checks_must_pass": True,
            "missing_check_evidence_fails_closed": True,
            "merge_or_deploy_performed_by_planner": False,
        },
        "summary": {
            "pull_requests_seen": len(evaluated),
            "ready_to_merge": len(eligible),
            "held": len(evaluated) - len(eligible),
        },
        "eligible_pr_numbers": eligible,
        "pull_requests": evaluated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSON file to read, or '-' for stdin.")
    parser.add_argument("--output", default="-", help="Output JSON file, or '-' for stdout.")
    args = parser.parse_args()

    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        source = json.loads(raw)
        plan = build_plan(source)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({
            "schema_version": "vaixlns-continuous-promotion-plan-v1",
            "decision": "HOLD",
            "error": str(exc),
        }, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2

    rendered = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output == "-":
        sys.stdout.write(rendered)
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Wrote promotion evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
