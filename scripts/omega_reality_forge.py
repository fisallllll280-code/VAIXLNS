#!/usr/bin/env python3
"""Ω Reality Forge: deterministic, evidence-gated task admission prototype.

This module plans work; it does not execute arbitrary agent commands or deploy systems.
Every task remains PENDING_VERIFICATION until required evidence is supplied and validated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
ALLOWED_EVIDENCE_STATES = {"OBSERVED", "TESTED", "ATTESTED"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("schema") != "vaixl.omega.reality-forge.plan.v1":
        errors.append("unsupported or missing plan schema")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a non-empty list"]
    seen: set[str] = set()
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{i}] must be an object")
            continue
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"tasks[{i}] missing task_id")
            continue
        if task_id in seen:
            errors.append(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        if not isinstance(task.get("owner_agent"), str) or not task["owner_agent"].strip():
            errors.append(f"{task_id}: owner_agent is required")
        deps = task.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            errors.append(f"{task_id}: depends_on must be a list of task IDs")
    for task in tasks:
        if isinstance(task, dict):
            for dep in task.get("depends_on", []) if isinstance(task.get("depends_on", []), list) else []:
                if dep not in seen:
                    errors.append(f"{task.get('task_id', '<unknown>')}: unknown dependency {dep}")
    return errors


def evaluate(plan: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    errors = validate_plan(plan)
    if errors:
        raise ValueError("; ".join(errors))
    evidence_map = evidence.get("evidence", {})
    if not isinstance(evidence_map, dict):
        raise ValueError("evidence.evidence must be an object keyed by task_id")

    tasks = {task["task_id"]: task for task in plan["tasks"]}
    states: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    # Repeated stable passes resolve dependency states without relying on input order.
    for task_id in sorted(tasks):
        states[task_id] = "PENDING_VERIFICATION"
    changed = True
    while changed:
        changed = False
        for task_id in sorted(tasks):
            task = tasks[task_id]
            if states[task_id] == "READY_FOR_REVIEW":
                continue
            deps = task.get("depends_on", [])
            if any(states.get(dep) != "READY_FOR_REVIEW" for dep in deps):
                new_state = "BLOCKED_DEPENDENCY"
            else:
                item = evidence_map.get(task_id)
                required = task.get("required_evidence", [])
                valid = isinstance(item, dict) and bool(required)
                if valid:
                    artifacts = item.get("artifacts", [])
                    valid = isinstance(artifacts, list)
                    by_kind = {
                        a.get("kind"): a for a in artifacts
                        if isinstance(a, dict) and isinstance(a.get("kind"), str)
                    }
                    for kind in required:
                        artifact = by_kind.get(kind)
                        if not artifact:
                            valid = False
                            break
                        if artifact.get("state") not in ALLOWED_EVIDENCE_STATES:
                            valid = False
                            break
                        claimed = artifact.get("sha256", "")
                        payload = artifact.get("payload")
                        if not isinstance(payload, str) or not isinstance(claimed, str):
                            valid = False
                            break
                        if hashlib.sha256(payload.encode("utf-8")).hexdigest() != claimed:
                            valid = False
                            break
                new_state = "READY_FOR_REVIEW" if valid else "PENDING_VERIFICATION"
            if new_state != states[task_id]:
                states[task_id] = new_state
                changed = True

    previous = GENESIS
    for task_id in sorted(tasks):
        task = tasks[task_id]
        body = {
            "task_id": task_id,
            "owner_agent": task["owner_agent"],
            "depends_on": sorted(task.get("depends_on", [])),
            "state": states[task_id],
            "evidence_digest": digest(evidence_map.get(task_id, {})),
            "policy": "HUMAN_APPROVAL_REQUIRED_FOR_EXECUTION_OR_PROMOTION",
        }
        record_hash = hashlib.sha256(bytes.fromhex(previous) + canonical_json(body)).hexdigest()
        records.append({**body, "previous_record_sha256": previous, "record_sha256": record_hash})
        previous = record_hash

    return {
        "schema": "vaixl.omega.reality-forge.receipt.v1",
        "plan_sha256": digest(plan),
        "evidence_bundle_sha256": digest(evidence),
        "status": "PENDING_HUMAN_REVIEW",
        "promotion_performed": False,
        "execution_performed": False,
        "task_states": states,
        "event_chain_head_sha256": previous,
        "events": records,
        "limitations": [
            "This prototype validates evidence payload hashes, not the truth of claims.",
            "READY_FOR_REVIEW is not VERIFIED and is not authorization to execute.",
            "External signatures, identity/authority checks, sandbox execution, and restore tests are not implemented here."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.plan.read_text(encoding="utf-8")),
                          json.loads(args.evidence.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{result['status']}: receipt={args.output} head={result['event_chain_head_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
