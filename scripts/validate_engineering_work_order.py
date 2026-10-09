#!/usr/bin/env python3
"""Read-only semantic validator and deterministic planner for VAIXLNS work orders.

This tool validates the work-order contract and DAG; it does not execute tasks,
call agents, connect to workers, write repositories, or authorize side effects.
It intentionally uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXECUTION_RANK = {"PLAN_ONLY": 0, "SANDBOX": 1, "AUTHORIZED_EXECUTION": 2}
DATA_RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
ACTIVE_STATES = {"QUEUED", "LEASED", "RUNNING", "RESULT_SUBMITTED", "VERIFYING", "ACCEPTED"}


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def deterministic_task_order(work_order: dict[str, Any]) -> list[str]:
    """Return a stable topological order, or raise ValueError for a cyclic graph."""
    tasks = work_order.get("tasks", [])
    by_id = {task["task_id"]: task for task in tasks}
    indegree = {task_id: 0 for task_id in by_id}
    outgoing: dict[str, list[str]] = {task_id: [] for task_id in by_id}

    for task in tasks:
        task_id = task["task_id"]
        for dep in task.get("depends_on", []):
            if dep not in by_id:
                raise ValueError(f"{task_id}: unknown dependency {dep}")
            outgoing[dep].append(task_id)
            indegree[task_id] += 1

    ready = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    ordered: list[str] = []
    while ready:
        current = ready.popleft()
        ordered.append(current)
        for child in sorted(outgoing[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready = deque(sorted(ready))

    if len(ordered) != len(by_id):
        cyclic = sorted(task_id for task_id, degree in indegree.items() if degree > 0)
        raise ValueError("dependency cycle detected involving: " + ", ".join(cyclic))
    return ordered


def validate_work_order(work_order: Any, schema: Any | None = None) -> list[str]:
    """Return semantic contract violations. An empty list means this validator's checks passed."""
    errors: list[str] = []
    if not isinstance(work_order, dict):
        return ["work order must be a JSON object"]
    if not isinstance(schema, dict):
        errors.append("schema must be a JSON object")
        schema = {}

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for key in required:
        if key not in work_order:
            errors.append(f"missing required field: {key}")

    if work_order.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if not isinstance(work_order.get("work_order_id"), str) or not work_order["work_order_id"].strip():
        errors.append("work_order_id must be a non-empty string")

    tasks = work_order.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a non-empty array")
        tasks = []

    task_ids: list[str] = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{index}] must be an object")
            continue
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"tasks[{index}].task_id must be a non-empty string")
        else:
            task_ids.append(task_id)
        if task.get("execution_mode") not in EXECUTION_RANK:
            errors.append(f"{task_id or index}: invalid execution_mode")
        if not isinstance(task.get("depends_on"), list):
            errors.append(f"{task_id or index}: depends_on must be an array")
        elif len(task["depends_on"]) != len(set(task["depends_on"])):
            errors.append(f"{task_id or index}: duplicate dependency")
    if len(task_ids) != len(set(task_ids)):
        errors.append("task_id values must be unique")

    known_ids = set(task_ids)
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("task_id", "<unknown>")
        for dep in task.get("depends_on", []) if isinstance(task.get("depends_on"), list) else []:
            if dep not in known_ids:
                errors.append(f"{task_id}: unknown dependency {dep}")

    if not errors:
        try:
            deterministic_task_order(work_order)
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(str(exc))

    policy = work_order.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
        policy = {}

    work_mode = policy.get("execution_mode")
    if work_mode not in EXECUTION_RANK:
        errors.append("policy.execution_mode is invalid")
    else:
        for task in tasks:
            if not isinstance(task, dict) or task.get("execution_mode") not in EXECUTION_RANK:
                continue
            if EXECUTION_RANK[task["execution_mode"]] > EXECUTION_RANK[work_mode]:
                errors.append(
                    f"{task.get('task_id', '<unknown>')}: task execution mode exceeds work-order policy"
                )

    approval_refs = policy.get("approval_refs", [])
    if not isinstance(approval_refs, list):
        errors.append("policy.approval_refs must be an array")
        approval_refs = []
    for effect in ("external_writes", "physical_actuation"):
        if policy.get(effect) is True:
            if work_mode != "AUTHORIZED_EXECUTION":
                errors.append(f"policy.{effect} requires AUTHORIZED_EXECUTION mode")
            if not approval_refs:
                errors.append(f"policy.{effect} requires at least one approval reference")
    if policy.get("approval_required_for_side_effects") is not True:
        errors.append("policy.approval_required_for_side_effects must be true")
    if policy.get("network_access") is True and not policy.get("allowed_domains"):
        errors.append("network access requires an explicit non-empty allowed_domains list")

    budget = work_order.get("resource_budget")
    if not isinstance(budget, dict):
        errors.append("resource_budget must be an object")
        budget = {}
    for key in ("max_wall_time_seconds", "max_cpu_cores", "max_parallel_tasks"):
        value = budget.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"resource_budget.{key} must be a positive integer")
    gpu = budget.get("max_gpu_units")
    if not isinstance(gpu, int) or isinstance(gpu, bool) or gpu < 0:
        errors.append("resource_budget.max_gpu_units must be a non-negative integer")
    cost = budget.get("max_cost_usd")
    if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
        errors.append("resource_budget.max_cost_usd must be a non-negative number")

    federation = work_order.get("federation")
    if not isinstance(federation, dict):
        errors.append("federation must be an object")
        federation = {}
    targets = federation.get("targets", [])
    if not isinstance(targets, list):
        errors.append("federation.targets must be an array")
        targets = []
    target_by_id = {
        target.get("target_id"): target
        for target in targets
        if isinstance(target, dict) and isinstance(target.get("target_id"), str)
    }
    requested_targets = federation.get("requested_target_ids", [])
    if not isinstance(requested_targets, list):
        errors.append("federation.requested_target_ids must be an array")
        requested_targets = []
    for target_id in requested_targets:
        if target_id not in target_by_id:
            errors.append(f"requested target does not exist in federation.targets: {target_id}")

    if work_order.get("state") in ACTIVE_STATES:
        tenant_id = policy.get("tenant_id")
        data_class = policy.get("data_classification")
        for target_id in requested_targets:
            target = target_by_id.get(target_id)
            if not target:
                continue
            if target.get("connection_state") != "HEALTHY":
                errors.append(f"active work requires HEALTHY target: {target_id}")
            if target.get("tenant_id") != tenant_id:
                errors.append(f"tenant mismatch for target: {target_id}")
            target_class = target.get("max_data_classification")
            if data_class not in DATA_RANK or target_class not in DATA_RANK:
                errors.append(f"unknown data classification for target: {target_id}")
            elif DATA_RANK[target_class] < DATA_RANK[data_class]:
                errors.append(f"target does not permit work-order data classification: {target_id}")
            if target.get("kind") == "PARTNER_WORKER" and not target.get("authorization_ref"):
                errors.append(f"partner target requires authorization_ref: {target_id}")

    provenance = work_order.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for key in ("created_by", "created_at", "source_revision"):
            if not isinstance(provenance.get(key), str) or not provenance[key].strip():
                errors.append(f"provenance.{key} must be a non-empty string")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_order", help="Path to a work-order JSON file")
    parser.add_argument("--schema", default=str(ROOT / "schemas" / "engineering-work-order.schema.json"))
    parser.add_argument("--plan-only", action="store_true", help="Print deterministic task order after validation")
    args = parser.parse_args()

    try:
        schema = read_json(args.schema)
        work_order = read_json(args.work_order)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, indent=2))
        return 2

    errors = validate_work_order(work_order, schema)
    if errors:
        print(json.dumps({"result": "INVALID", "errors": errors}, indent=2))
        return 2

    result: dict[str, Any] = {
        "result": "CONTRACT_VALID",
        "work_order_id": work_order["work_order_id"],
        "state": work_order["state"],
        "task_count": len(work_order["tasks"]),
        "execution_performed": False,
        "network_access_performed": False,
        "external_writes_performed": False,
        "physical_actuation_performed": False
    }
    if args.plan_only:
        result["deterministic_task_order"] = deterministic_task_order(work_order)
        result["plan_state"] = "PLAN_ONLY_NOT_DISPATCHED"
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
