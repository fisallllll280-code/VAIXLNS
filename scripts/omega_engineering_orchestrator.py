#!/usr/bin/env python3
"""Link VAIXLNS engineering indexes, automation outputs and evidence into one review graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "vaixlns.omega-engineering-orchestration.v1"

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def digest_json(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))

def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "MISSING"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "UNREADABLE"
    if not isinstance(value, dict):
        return None, "INVALID_ROOT_TYPE"
    return value, None

def embedded_hash_state(payload: dict[str, Any] | None, key: str) -> str:
    if payload is None:
        return "NOT_AVAILABLE"
    claimed = payload.get(key)
    if not isinstance(claimed, str) or not re.fullmatch(r"[a-f0-9]{64}", claimed):
        return "HASH_MISSING_OR_INVALID"
    core = {k: v for k, v in payload.items() if k != key}
    return "HASH_VALID" if digest_json(core) == claimed else "HASH_MISMATCH"

def inspect_json(root: Path, relative: str, hash_key: str | None = None,
                 schema_value: str | None = None, optional: bool = False) -> dict[str, Any]:
    path = root / relative
    payload, error = load_json(path)
    if error:
        return {
            "id": relative.replace("/", "_").replace(".", "_"),
            "path": relative, "present": False, "state": "OPTIONAL_MISSING" if optional and error == "MISSING" else error,
            "file_sha256": None, "embedded_hash_state": "NOT_AVAILABLE", "schema_state": "NOT_AVAILABLE",
            "blocks_readiness": not optional,
        }
    assert payload is not None
    hash_state = embedded_hash_state(payload, hash_key) if hash_key else "NOT_REQUIRED"
    schema_state = "SCHEMA_VALID" if schema_value is None or payload.get("schema") == schema_value else "SCHEMA_MISMATCH"
    integrity_ok = hash_state in {"HASH_VALID", "NOT_REQUIRED"} and schema_state == "SCHEMA_VALID"
    return {
        "id": relative.replace("/", "_").replace(".", "_"),
        "path": relative, "present": True,
        "state": "PRESENT_HASH_VALID" if integrity_ok else "INTEGRITY_OR_SCHEMA_FAILURE",
        "file_sha256": digest_bytes(path.read_bytes()),
        "embedded_hash_state": hash_state, "schema_state": schema_state,
        "declared_revision": payload.get("repository_revision"),
        "blocks_readiness": not integrity_ok and not optional,
        "summary": payload.get("summary", {}),
    }

def inspect_test_log(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"state": "MISSING", "test_count": None, "summary_line": None, "file_sha256": None}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"state": "UNREADABLE", "test_count": None, "summary_line": None, "file_sha256": None}
    matches = re.findall(r"\bRan\s+(\d+)\s+tests?\s+in\s+[0-9.]+\s*s", text)
    count = int(matches[-1]) if matches else None
    summary_line = next((line.strip() for line in reversed(text.splitlines()) if re.fullmatch(r"OK(?:\s+\(.*\))?", line.strip())), None)
    failed = bool(re.search(r"(?m)^FAILED\s*\(", text)) or "ERROR: test suite failed" in text
    if failed:
        state = "FAIL"
    elif count is not None and summary_line is not None:
        state = "PASS"
    else:
        state = "UNKNOWN"
    return {"state": state, "test_count": count, "summary_line": summary_line,
            "file_sha256": digest_bytes(path.read_bytes())}

def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    artifact_specs = [
        ("innovation-network.json", "network_sha256", "vaixlns.innovation-network.v1", False),
        ("omega-research-results.json", "result_sha256", "vaixlns.omega-research-fabric.v1", False),
        ("engineering-execution-plan.json", "plan_sha256", "vaixlns.engineering-agent-fabric.v1", False),
        ("omega-error-triage.json", "report_sha256", "vaixlns.omega-error-locator.v1", True),
        ("omega-revenue-portfolio.json", "report_sha256", "vaixlns.omega-revenue-portfolio-report.v1", True),
        ("omega-server-placement-plan.json", "plan_sha256", "vaixlns.omega-server-placement-plan.v1", True),
    ]
    artifacts = []
    for relative, hash_key, schema, optional in artifact_specs:
        artifacts.append(inspect_json(root, relative, hash_key, schema, optional))
    artifact_by_path = {a["path"]: a for a in artifacts}
    tests = inspect_test_log(root / "test-suite.log")

    links = [
        {"from": "repository_inventory", "to": "omega-research-results.json", "relation": "INDEXES_PINNED_REPOSITORY_CONTENT"},
        {"from": "innovation-network.json", "to": "engineering-execution-plan.json", "relation": "SUPPLIES_STABLE_RESEARCH_WORKPACKET_CONTEXT"},
        {"from": "omega-research-results.json", "to": "engineering-execution-plan.json", "relation": "HASH_CHECKED_RESEARCH_CONTEXT"},
        {"from": "test-suite.log", "to": "omega-error-triage.json", "relation": "FAILURE_LOG_LOCALIZATION", "condition": "ONLY_WHEN_TESTS_FAIL"},
        {"from": "omega-revenue-portfolio.json", "to": "commercial_prioritization", "relation": "RANKS_OFFERS_USING_RECORDED_UNIT_ECONOMICS", "blocks_engineering_ci": False},
        {"from": "innovation-network.json", "to": "omega-server-placement-plan.json", "relation": "PLANS_CAPABILITY_AWARE_TASK_PLACEMENT", "dispatch_state": "NOT_DISPATCHED"},
        {"from": "omega-server-placement-plan.json", "to": "engineering-execution-plan.json", "relation": "SERVER_CAPABILITY_PLAN_IS_ADVISORY_NOT_RUNTIME_PROOF"},
        {"from": "all_artifacts", "to": "engineering_review", "relation": "HASHED_EVIDENCE_BUNDLE"},
    ]

    required = [a for a in artifacts if a.get("blocks_readiness", True)]
    invalid_required = [a["path"] for a in required if a["state"] != "PRESENT_HASH_VALID"]
    missing_test_evidence = tests["state"] in {"MISSING", "UNREADABLE", "UNKNOWN"}
    mismatched = [a["path"] for a in required if a["embedded_hash_state"] == "HASH_MISMATCH" or a["schema_state"] == "SCHEMA_MISMATCH"]
    if mismatched:
        readiness = "BLOCKED_INTEGRITY_OR_SCHEMA_FAILURE"
    elif tests["state"] == "FAIL":
        readiness = "BLOCKED_TEST_FAILURE_DIAGNOSTIC_REQUIRED"
    elif invalid_required or missing_test_evidence:
        readiness = "BLOCKED_MISSING_OR_INCOMPLETE_EVIDENCE"
    else:
        readiness = "READY_FOR_ENGINEERING_REVIEW_NOT_AUTO_RELEASED"

    errors = artifact_by_path["omega-error-triage.json"]
    if tests["state"] == "FAIL":
        diagnostic_state = "REPORT_PRESENT" if errors["state"] == "PRESENT_HASH_VALID" else "DIAGNOSTIC_MISSING_OR_INVALID"
    elif tests["state"] == "PASS":
        diagnostic_state = "NOT_NEEDED_TESTS_PASSED"
    else:
        diagnostic_state = "WAITING_FOR_TEST_EVIDENCE"

    core = {
        "schema": SCHEMA,
        "state": readiness,
        "source_revision": next((a.get("declared_revision") for a in artifacts if a.get("declared_revision")), None),
        "tool_chain": [
            {"step": 1, "tool": "Ω research index", "input": "repository inventory", "output": "omega-research-results.json", "execution_claim": "REQUIRES_SUCCESSFUL_CI_STEP"},
            {"step": 2, "tool": "federated innovation planner", "input": "innovation-federation.json", "output": "innovation-network.json", "execution_claim": "REQUIRES_SUCCESSFUL_CI_STEP"},
            {"step": 3, "tool": "engineering agent planner", "input": ["repository inventory", "omega-research-results.json"], "output": "engineering-execution-plan.json", "execution_claim": "PLAN_ONLY_NO_LIVE_AGENT_DISPATCH"},
            {"step": 4, "tool": "Ω Error Locator", "input": "test-suite.log", "output": "omega-error-triage.json", "execution_claim": "CONDITIONAL_ON_FAILURE"},
            {"step": 5, "tool": "Ω Revenue Portfolio", "input": "commercial evidence and unit economics", "output": "omega-revenue-portfolio.json", "execution_claim": "MODELS_ONLY_NO_REVENUE_GUARANTEE"},
            {"step": 6, "tool": "Ω Engineering Orchestrator", "input": "all produced artifacts", "output": "engineering-orchestration.json", "execution_claim": "LINKS_AND_GATES_EVIDENCE_NO_AUTO_MERGE"},
        ],
        "artifacts": artifacts,
        "test_evidence": tests,
        "failure_diagnostic_state": diagnostic_state,
        "links": links,
        "external_systems": {
            "VLNS": "ENDPOINT_CONFIGURATION_AND_LIVE_CONFORMANCE_REQUIRED",
            "VX": "ENDPOINT_CONFIGURATION_AND_SANDBOXED_EXECUTION_EVIDENCE_REQUIRED",
            "NEXNET": "ENDPOINT_CONFIGURATION_AND_LIVE_CONFORMANCE_REQUIRED",
            "connectivity_verified": False,
        },
        "release_policy": {
            "auto_merge": False, "auto_deploy": False, "canonical_promotion": "EXPLICIT_AUTHORITY_DECISION_REQUIRED",
            "verified_requires": ["pinned inputs", "reproducible command", "exit code and logs", "hash-bound evidence", "counterevidence review"],
        },
        "blockers": {
            "required_artifacts_not_ready": invalid_required,
            "integrity_failures": mismatched,
            "test_evidence_state": tests["state"],
        },
    }
    return {**core, "report_sha256": digest_json(core)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--output", default="engineering-orchestration.json", help="Output report")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"repository root is not a directory: {root}")
    try:
        report = build_report(root)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(output), "state": report["state"], "report_sha256": report["report_sha256"],
                      "test_state": report["test_evidence"]["state"], "artifact_count": len(report["artifacts"])}, sort_keys=True))
    # The report is evidence for review, not a workflow control that masks failed tests.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
