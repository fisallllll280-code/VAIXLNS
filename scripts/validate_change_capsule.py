#!/usr/bin/env python3
"""Validate a VAIXLNS Ω Change Capsule using only the Python standard library.

This checks structural and admission invariants. It does not execute tests, authenticate
evidence, or independently prove that a claimed result is true.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA64 = re.compile(r"^[a-f0-9]{64}$")
CHECK_RESULTS = {"PASS", "FAIL", "SKIP", "INCONCLUSIVE"}
ADMISSION_STATES = {"PROPOSED", "BLOCKED", "INCONCLUSIVE", "ADMITTED"}


class CapsuleError(ValueError):
    """Raised when a capsule violates its contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CapsuleError(message)


def _safe_repo_path(value: object, field: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{field}: expected non-empty path")
    path = PurePosixPath(value)
    _require(not path.is_absolute(), f"{field}: absolute paths are prohibited: {value}")
    _require(".." not in path.parts, f"{field}: parent traversal is prohibited: {value}")
    _require(chr(92) not in value and chr(0) not in value, f"{field}: invalid path: {value}")
    return value


def validate_capsule(capsule: object) -> list[str]:
    _require(isinstance(capsule, dict), "root: expected object")
    required = {"capsule_version", "capsule_id", "task", "repository", "change", "verification", "admission"}
    _require(required <= capsule.keys(), f"root: missing fields {sorted(required - capsule.keys())}")
    _require(capsule["capsule_version"] == "1.0.0", "capsule_version: expected 1.0.0")
    _require(isinstance(capsule["capsule_id"], str) and capsule["capsule_id"].strip(), "capsule_id: expected non-empty string")

    task = capsule["task"]
    _require(isinstance(task, dict), "task: expected object")
    for key in ("task_id", "summary"):
        _require(isinstance(task.get(key), str) and task[key].strip(), f"task.{key}: expected non-empty string")
    criteria = task.get("acceptance_criteria")
    _require(isinstance(criteria, list) and criteria and all(isinstance(x, str) and x.strip() for x in criteria),
             "task.acceptance_criteria: expected non-empty string array")

    repository = capsule["repository"]
    _require(isinstance(repository, dict), "repository: expected object")
    _require(isinstance(repository.get("repository"), str) and repository["repository"].strip(), "repository.repository: required")
    _require(isinstance(repository.get("base_revision"), str) and SHA40.fullmatch(repository["base_revision"]),
             "repository.base_revision: expected 40-character lowercase Git SHA")

    change = capsule["change"]
    _require(isinstance(change, dict), "change: expected object")
    allowed_raw, changed_raw = change.get("allowed_paths"), change.get("changed_paths")
    _require(isinstance(allowed_raw, list), "change.allowed_paths: expected array")
    _require(isinstance(changed_raw, list), "change.changed_paths: expected array")
    allowed = {_safe_repo_path(p, "change.allowed_paths") for p in allowed_raw}
    changed = [_safe_repo_path(p, "change.changed_paths") for p in changed_raw]
    _require(len(changed) == len(set(changed)), "change.changed_paths: duplicate paths are prohibited")
    outside = sorted(set(changed) - allowed)
    _require(not outside, f"change.changed_paths: paths outside authorized scope: {outside}")
    _require(isinstance(change.get("diff_sha256"), str) and SHA64.fullmatch(change["diff_sha256"]),
             "change.diff_sha256: expected 64-character lowercase SHA-256")

    verification = capsule["verification"]
    _require(isinstance(verification, dict), "verification: expected object")
    _require(isinstance(verification.get("environment"), str) and verification["environment"].strip(),
             "verification.environment: required")
    checks = verification.get("checks")
    _require(isinstance(checks, list), "verification.checks: expected array")
    for index, check in enumerate(checks):
        _require(isinstance(check, dict), f"verification.checks[{index}]: expected object")
        _require(isinstance(check.get("name"), str) and check["name"].strip(), f"verification.checks[{index}].name: required")
        _require(check.get("result") in CHECK_RESULTS, f"verification.checks[{index}].result: invalid result")
    evidence = verification.get("evidence_refs")
    _require(isinstance(evidence, list) and all(isinstance(x, str) and x.strip() for x in evidence),
             "verification.evidence_refs: expected string array")

    admission = capsule["admission"]
    _require(isinstance(admission, dict), "admission: expected object")
    state = admission.get("state")
    _require(state in ADMISSION_STATES, "admission.state: invalid state")
    _require(isinstance(admission.get("reason"), str) and admission["reason"].strip(), "admission.reason: required")

    failures = [f"{c['name']}={c['result']}" for c in checks if c["result"] != "PASS"]
    if state == "ADMITTED":
        _require(bool(checks), "admission: ADMITTED requires at least one verification check")
        _require(not failures, f"admission: ADMITTED is prohibited while checks are not PASS: {failures}")
        _require(bool(evidence), "admission: ADMITTED requires at least one evidence reference")
    if state in {"BLOCKED", "INCONCLUSIVE"}:
        _require(bool(admission["reason"]), f"admission: {state} requires a reason")

    return [
        "capsule structure: PASS",
        f"authorized path scope: PASS ({len(changed)} changed path(s))",
        f"verification checks: {len(checks)}",
        f"admission state: {state}",
        "note: evidence authenticity and execution claims require independent verification",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capsule", type=Path, help="Path to a JSON capsule")
    args = parser.parse_args()
    try:
        with args.capsule.open("r", encoding="utf-8") as handle:
            capsule = json.load(handle)
        for line in validate_capsule(capsule):
            print(line)
        return 0
    except (OSError, json.JSONDecodeError, CapsuleError) as exc:
        print(f"CAPSULE INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
