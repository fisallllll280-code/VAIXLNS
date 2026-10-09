#!/usr/bin/env python3
"""Plan deterministic, policy-constrained task placement across Ω server pools.

This tool is a planner only: it does not provision servers, call endpoints,
transfer code or data, start containers, or dispatch any task.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA = "vaixlns.omega-server-fabric.v1"
TASKS_SCHEMA = "vaixlns.omega-server-workload.v1"
REPORT_SCHEMA = "vaixlns.omega-server-placement-plan.v1"
DATA_RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
VALID_POOL_STATES = {"NOT_PROVISIONED", "PROVISIONED_UNVERIFIED", "READY_VERIFIED"}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value

def validate_inputs(manifest: dict[str, Any], workload: dict[str, Any]) -> None:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"manifest schema must be {MANIFEST_SCHEMA}")
    if workload.get("schema") != TASKS_SCHEMA:
        raise ValueError(f"workload schema must be {TASKS_SCHEMA}")
    if manifest.get("control_mode") != "PLAN_ONLY":
        raise ValueError("server fabric planner accepts PLAN_ONLY manifests exclusively")
    pools = manifest.get("server_pools")
    tasks = workload.get("tasks")
    if not isinstance(pools, list) or not pools:
        raise ValueError("manifest server_pools must be a non-empty list")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("workload tasks must be a non-empty list")
    pool_ids = []
    for pool in pools:
        if not isinstance(pool, dict):
            raise ValueError("every server pool must be an object")
        pool_id = pool.get("pool_id")
        if not isinstance(pool_id, str) or not pool_id.strip():
            raise ValueError("every server pool needs a non-empty pool_id")
        pool_ids.append(pool_id)
        if pool.get("operational_state") not in VALID_POOL_STATES:
            raise ValueError(f"invalid operational_state for pool {pool_id}")
        if pool.get("max_data_classification") not in DATA_RANK:
            raise ValueError(f"invalid max_data_classification for pool {pool_id}")
        if not isinstance(pool.get("task_types"), list) or not isinstance(pool.get("capabilities"), list):
            raise ValueError(f"pool {pool_id} needs task_types and capabilities arrays")
        if not isinstance(pool.get("max_parallel_tasks"), int) or pool["max_parallel_tasks"] < 1:
            raise ValueError(f"pool {pool_id} max_parallel_tasks must be a positive integer")
        if pool.get("network_egress_policy") not in {"DENY_BY_DEFAULT", "ALLOWLIST_ONLY", "EXPLICITLY_APPROVED"}:
            raise ValueError(f"pool {pool_id} has invalid network egress policy")
        capacity = pool.get("capacity_estimate")
        if not isinstance(capacity, dict):
            raise ValueError(f"pool {pool_id} needs a capacity_estimate object")
        for field in ("cpu_units_per_task", "memory_gib_per_task"):
            value = capacity.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"pool {pool_id} {field} must be a positive number")
        if not isinstance(capacity.get("gpu_capable"), bool):
            raise ValueError(f"pool {pool_id} gpu_capable must be boolean")
        if pool.get("endpoint") not in (None, ""):
            raise ValueError("PLAN_ONLY example must not contain live endpoints")
    if len(set(pool_ids)) != len(pool_ids):
        raise ValueError("pool_id values must be unique")
    task_ids = []
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("every task must be an object")
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("every task needs a non-empty task_id")
        task_ids.append(task_id)
        if task.get("data_classification") not in DATA_RANK:
            raise ValueError(f"task {task_id} has invalid data_classification")
        if not isinstance(task.get("task_type"), str) or not task["task_type"]:
            raise ValueError(f"task {task_id} needs task_type")
        if not isinstance(task.get("priority"), int) or not 0 <= task["priority"] <= 100:
            raise ValueError(f"task {task_id} priority must be an integer from 0 to 100")
        if not isinstance(task.get("requires_isolation", False), bool):
            raise ValueError(f"task {task_id} requires_isolation must be boolean")
        if not isinstance(task.get("requires_gpu", False), bool):
            raise ValueError(f"task {task_id} requires_gpu must be boolean")
        for field in ("estimated_cpu_units", "estimated_memory_gib"):
            value = task.get(field, 0)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError(f"task {task_id} {field} must be a non-negative number")
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("task_id values must be unique")

def compatible(pool: dict[str, Any], task: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons = []
    if task["task_type"] not in pool["task_types"]:
        reasons.append("TASK_TYPE_UNSUPPORTED")
    if DATA_RANK[pool["max_data_classification"]] < DATA_RANK[task["data_classification"]]:
        reasons.append("DATA_CLASSIFICATION_EXCEEDS_POOL_POLICY")
    if task.get("requires_isolation", False) and not pool.get("isolated_execution", False):
        reasons.append("ISOLATION_REQUIRED")
    if DATA_RANK[task["data_classification"]] >= DATA_RANK["CONFIDENTIAL"] and pool["network_egress_policy"] != "DENY_BY_DEFAULT":
        reasons.append("CONFIDENTIAL_TASK_REQUIRES_EGRESS_DENY")
    capacity = pool.get("capacity_estimate", {})
    if task.get("estimated_cpu_units", 0) > capacity.get("cpu_units_per_task", 0):
        reasons.append("CPU_CAPACITY_INSUFFICIENT")
    if task.get("estimated_memory_gib", 0) > capacity.get("memory_gib_per_task", 0):
        reasons.append("MEMORY_CAPACITY_INSUFFICIENT")
    if task.get("requires_gpu", False) and not capacity.get("gpu_capable", False):
        reasons.append("GPU_REQUIRED")
    if not isinstance(pool.get("capabilities"), list):
        reasons.append("CAPABILITIES_NOT_DECLARED")
    return not reasons, reasons

def build_plan(manifest: dict[str, Any], workload: dict[str, Any]) -> dict[str, Any]:
    validate_inputs(manifest, workload)
    pools = sorted(manifest["server_pools"], key=lambda row: row["pool_id"])
    tasks = sorted(workload["tasks"], key=lambda row: (-row["priority"], row["task_id"]))
    placements = []
    assigned: dict[str, int] = {pool["pool_id"]: 0 for pool in pools}

    for task in tasks:
        candidates = []
        rejected = []
        for pool in pools:
            is_compatible, reasons = compatible(pool, task)
            if not is_compatible:
                rejected.append({"pool_id": pool["pool_id"], "reasons": reasons})
                continue
            planned_count = assigned[pool["pool_id"]]
            max_parallel = pool["max_parallel_tasks"]
            ratio = planned_count / max_parallel
            state_penalty = {"READY_VERIFIED": 0, "PROVISIONED_UNVERIFIED": 100, "NOT_PROVISIONED": 200}[pool["operational_state"]]
            # Candidate preference is deterministic and does not claim to represent observed runtime load.
            score = ratio * 1000 + state_penalty - min(task["priority"], 100) * 0.01
            candidates.append((score, pool["pool_id"], pool, ratio))
        if not candidates:
            placements.append({
                "task_id": task["task_id"], "task_type": task["task_type"],
                "priority": task["priority"], "data_classification": task["data_classification"],
                "placement_state": "BLOCKED_NO_COMPATIBLE_POOL",
                "recommended_pool_id": None, "dispatch_state": "NOT_DISPATCHED",
                "eligible_candidates": [], "rejected_pools": rejected,
                "reason": "No pool satisfies task-type, data-classification, isolation and egress-policy constraints.",
            })
            continue
        candidates.sort(key=lambda row: (row[0], row[1]))
        _, pool_id, pool, ratio = candidates[0]
        assigned[pool_id] += 1
        state = "PROPOSED_UNPROVISIONED" if pool["operational_state"] == "NOT_PROVISIONED" else (
            "PROPOSED_UNVERIFIED_POOL" if pool["operational_state"] == "PROVISIONED_UNVERIFIED" else "PROPOSED_READY_POOL_REQUIRES_RUNTIME_AUTH"
        )
        placements.append({
            "task_id": task["task_id"], "task_type": task["task_type"],
            "priority": task["priority"], "data_classification": task["data_classification"],
            "placement_state": state, "recommended_pool_id": pool_id,
            "pool_operational_state": pool["operational_state"],
            "planned_share_before_assignment": round(ratio, 4),
            "dispatch_state": "NOT_DISPATCHED",
            "required_preconditions": [
                "immutable task and input references",
                "verified workload identity and authorization",
                "provisioned pool health and measured capacity",
                "approved data-residency and egress policy",
                "sandbox and time/resource limits when execution is required",
            ],
            "eligible_candidates": [row[1] for row in candidates],
            "rejected_pools": rejected,
        })

    core = {
        "schema": REPORT_SCHEMA,
        "state": "PLANNED_NOT_DISPATCHED",
        "manifest_sha256": sha256_json(manifest),
        "workload_sha256": sha256_json(workload),
        "policy_version": manifest.get("policy_version", "UNSPECIFIED"),
        "scheduler": {
            "name": "DETERMINISTIC_POLICY_CONSTRAINED_PLACEMENT",
            "observed_load_used": False,
            "runtime_benchmark_used": False,
            "cost_optimizer_used": False,
            "automatic_provisioning": False,
            "external_dispatch": False,
        },
        "placements": placements,
        "capacity_plan": [
            {"pool_id": pool["pool_id"], "operational_state": pool["operational_state"],
             "configured_max_parallel_tasks": pool["max_parallel_tasks"],
             "planned_assignments": assigned[pool["pool_id"]],
             "planning_utilization_ratio": round(assigned[pool["pool_id"]] / pool["max_parallel_tasks"], 4)}
            for pool in pools
        ],
        "summary": {
            "task_count": len(placements),
            "placement_proposed_count": sum(item["recommended_pool_id"] is not None for item in placements),
            "blocked_count": sum(item["recommended_pool_id"] is None for item in placements),
            "dispatched_count": 0,
            "servers_provisioned_by_tool": 0,
            "server_connectivity_verified": False,
            "performance_claim": "NONE",
        },
        "safety": {
            "source_code_executed": False,
            "data_transmitted": False,
            "credentials_used": False,
            "automatic_merge_or_deploy": False,
            "private_data_requires_compatible_declared_classification": True,
        },
    }
    return {**core, "plan_sha256": sha256_json(core)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Server pool manifest JSON")
    parser.add_argument("--tasks", required=True, help="Task workload JSON")
    parser.add_argument("--output", default="omega-server-placement-plan.json", help="Placement proposal output")
    args = parser.parse_args()
    try:
        manifest = load_object(Path(args.manifest))
        workload = load_object(Path(args.tasks))
        plan = build_plan(manifest, workload)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(output), "state": plan["state"], **plan["summary"],
                      "plan_sha256": plan["plan_sha256"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
