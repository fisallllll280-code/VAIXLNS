#!/usr/bin/env python3
"""Deterministic offline reference simulator for the VAIXLNS agent fabric.

It does not call model providers, run shell commands, use networks, or modify repositories.
Its output is not production execution evidence and cannot assert VERIFIED.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

GENESIS_HASH = "0" * 64
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
CHECK_RESULTS = {"PASS", "FAIL", "INCONCLUSIVE", "SKIP"}
PROTECTED_PATHS = {"project.genome", "registry/omega/omega-000-master-index.json"}
ROLE_TOOLS = {
    "context_cartographer": {"repo.read", "docs.read", "history.read", "registry.read"},
    "system_architect": {"repo.read", "docs.read", "graph.read", "tests.read", "docs.propose"},
    "task_compiler": {"repo.read", "graph.read", "tests.read", "plan.write"},
    "implementation_planner": {"repo.read", "docs.read", "graph.read", "workspace.write", "tests.read"},
    "implementation_worker": {"repo.read", "workspace.write", "tests.run", "build.run"},
    "adversarial_challenger": {"repo.read", "diff.read", "tests.read", "tests.run", "security.scan"},
    "evidence_referee": {"repo.read", "diff.read", "tests.read", "evidence.read", "replay.read"},
    "registry_steward": {"registry.read", "registry.propose", "provenance.read"},
}


class ScenarioError(ValueError):
    """Raised when a scenario is structurally unsafe or ambiguous."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def safe_repo_path(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw or raw.strip() != raw:
        raise ScenarioError(f"{field}: expected normalized non-empty repository path")
    if chr(92) in raw or chr(0) in raw:
        raise ScenarioError(f"{field}: backslash and NUL are prohibited")
    path = PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("/") or ".." in path.parts or "." in path.parts:
        raise ScenarioError(f"{field}: absolute and traversal paths are prohibited: {raw}")
    if str(path) != raw or "//" in raw:
        raise ScenarioError(f"{field}: path must be normalized: {raw}")
    return raw


def path_is_authorized(path: str, grants: list[str]) -> bool:
    return any(path == grant or path.startswith(grant.rstrip("/") + "/") for grant in grants)


def topological_layers(tasks: list[dict[str, Any]]) -> list[list[str]]:
    by_id = {task["task_id"]: task for task in tasks}
    indegree = {task_id: 0 for task_id in by_id}
    children: dict[str, list[str]] = {task_id: [] for task_id in by_id}
    for task in tasks:
        for dep in task.get("depends_on", []):
            if dep not in by_id:
                raise ScenarioError(f"{task['task_id']}: unknown dependency {dep}")
            if dep == task["task_id"]:
                raise ScenarioError(f"{task['task_id']}: task cannot depend on itself")
            indegree[task["task_id"]] += 1
            children[dep].append(task["task_id"])
    layers: list[list[str]] = []
    ready = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    visited = 0
    while ready:
        layer = ready
        layers.append(layer)
        visited += len(layer)
        next_ready: list[str] = []
        for task_id in layer:
            for child in children[task_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    next_ready.append(child)
        ready = sorted(next_ready)
    if visited != len(tasks):
        raise ScenarioError("dependency graph contains a cycle")
    return layers


def validate_scenario(scenario: Any) -> tuple[dict[str, dict[str, Any]], list[list[str]]]:
    if not isinstance(scenario, dict):
        raise ScenarioError("root: expected an object")
    if scenario.get("mode") != "SIMULATION":
        raise ScenarioError("mode must be SIMULATION; live execution is not implemented here")
    if not isinstance(scenario.get("simulation_id"), str) or not scenario["simulation_id"].strip():
        raise ScenarioError("simulation_id: required")
    if not isinstance(scenario.get("systems"), list) or not scenario["systems"]:
        raise ScenarioError("systems: expected a non-empty array")
    if any(not isinstance(s, dict) or not s.get("system_id") for s in scenario["systems"]):
        raise ScenarioError("systems: every entry requires system_id")
    budgets = scenario.get("budgets")
    if not isinstance(budgets, dict):
        raise ScenarioError("budgets: expected an object")
    for key in ("max_tasks", "max_parallelism", "max_estimated_cost"):
        if not isinstance(budgets.get(key), int) or isinstance(budgets[key], bool) or budgets[key] < 1:
            raise ScenarioError(f"budgets.{key}: expected a positive integer")
    tasks = scenario.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ScenarioError("tasks: expected a non-empty array")
    if len(tasks) > budgets["max_tasks"]:
        raise ScenarioError("task count exceeds budgets.max_tasks")
    required = {"task_id", "goal", "role", "depends_on", "risk", "authorized_paths",
                "write_paths", "allowed_tools", "requested_tools", "estimated_cost",
                "verification", "requires_human_approval"}
    by_id: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ScenarioError(f"tasks[{index}]: expected an object")
        missing = sorted(required - task.keys())
        if missing:
            raise ScenarioError(f"tasks[{index}]: missing fields {missing}")
        task_id = task["task_id"]
        if not isinstance(task_id, str) or not task_id.strip() or task_id in by_id:
            raise ScenarioError(f"tasks[{index}].task_id: must be unique and non-empty")
        if not isinstance(task["goal"], str) or not task["goal"].strip():
            raise ScenarioError(f"{task_id}.goal: required")
        if task["risk"] not in RISK_LEVELS:
            raise ScenarioError(f"{task_id}.risk: invalid risk level")
        if not isinstance(task["requires_human_approval"], bool):
            raise ScenarioError(f"{task_id}.requires_human_approval: expected boolean")
        cost = task["estimated_cost"]
        if not isinstance(cost, int) or isinstance(cost, bool) or cost < 0:
            raise ScenarioError(f"{task_id}.estimated_cost: expected non-negative integer")
        for field in ("depends_on", "authorized_paths", "write_paths", "allowed_tools", "requested_tools"):
            if not isinstance(task[field], list) or any(not isinstance(item, str) for item in task[field]):
                raise ScenarioError(f"{task_id}.{field}: expected a string array")
        task["authorized_paths"] = [safe_repo_path(p, f"{task_id}.authorized_paths") for p in task["authorized_paths"]]
        task["write_paths"] = [safe_repo_path(p, f"{task_id}.write_paths") for p in task["write_paths"]]
        if len(task["write_paths"]) != len(set(task["write_paths"])):
            raise ScenarioError(f"{task_id}.write_paths: duplicate paths are prohibited")
        verification = task["verification"]
        if not isinstance(verification, dict):
            raise ScenarioError(f"{task_id}.verification: expected an object")
        for check in ("tests", "adversarial", "replay"):
            if verification.get(check) not in CHECK_RESULTS:
                raise ScenarioError(f"{task_id}.verification.{check}: invalid result")
        refs = verification.get("evidence_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ScenarioError(f"{task_id}.verification.evidence_refs: expected string array")
        by_id[task_id] = task
    return by_id, topological_layers(tasks)


def _emit(events: list[dict[str, Any]], event_type: str, task_id: str | None, details: dict[str, Any]) -> None:
    previous = events[-1]["event_hash"] if events else GENESIS_HASH
    body = {"sequence": len(events) + 1, "logical_tick": len(events) + 1,
            "event_type": event_type, "task_id": task_id, "details": details,
            "previous_hash": previous}
    events.append({**body, "event_hash": sha256_json(body)})


def verify_event_chain(events: Any) -> bool:
    if not isinstance(events, list):
        return False
    previous = GENESIS_HASH
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict) or event.get("sequence") != index or event.get("logical_tick") != index:
            return False
        if event.get("previous_hash") != previous:
            return False
        body = {key: value for key, value in event.items() if key != "event_hash"}
        if event.get("event_hash") != sha256_json(body):
            return False
        previous = event["event_hash"]
    return True


def _tool_denials(task: dict[str, Any]) -> list[str]:
    granted_by_role = ROLE_TOOLS.get(task["role"])
    if granted_by_role is None:
        return [f"unknown role profile: {task['role']}"]
    requested = set(task["requested_tools"])
    denials = [f"tool not in task grant: {tool}" for tool in sorted(requested - set(task["allowed_tools"]))]
    denials.extend(f"role does not grant: {tool}" for tool in sorted(requested - granted_by_role))
    return denials


def _path_denials(task: dict[str, Any]) -> list[str]:
    denials = []
    for path in task["write_paths"]:
        if path in PROTECTED_PATHS:
            denials.append(f"canonical authority path requires a separate approved change protocol: {path}")
        if not path_is_authorized(path, task["authorized_paths"]):
            denials.append(f"path outside task grant: {path}")
    return denials


def _choose_topology(task_ids: list[str], by_id: dict[str, dict[str, Any]], limit: int) -> str:
    if len(task_ids) == 1:
        return "ESCALATED_REVIEW" if by_id[task_ids[0]]["risk"] in {"HIGH", "CRITICAL"} else "SINGLE_WORKER"
    if len(task_ids) > limit:
        return "BOUNDED_SERIAL_WAVES"
    writes = [set(by_id[task_id]["write_paths"]) for task_id in task_ids]
    if any(left & right for i, left in enumerate(writes) for right in writes[i + 1:]):
        return "SERIAL_CONFLICT_AVOIDANCE"
    if any(by_id[task_id]["risk"] in {"HIGH", "CRITICAL"} for task_id in task_ids):
        return "ISOLATED_PARALLEL_WITH_ESCALATION"
    return "ISOLATED_PARALLEL_PLAN"


def simulate(scenario: Any) -> dict[str, Any]:
    by_id, layers = validate_scenario(scenario)
    budgets = scenario["budgets"]
    total_cost = sum(task["estimated_cost"] for task in by_id.values())
    events: list[dict[str, Any]] = []
    outcomes: dict[str, dict[str, Any]] = {}
    _emit(events, "simulation.started", None, {"simulation_id": scenario["simulation_id"],
          "mode": "SIMULATION", "systems_count": len(scenario["systems"]),
          "task_count": len(by_id), "estimated_cost": total_cost})
    if total_cost > budgets["max_estimated_cost"]:
        _emit(events, "budget.gate", None, {"result": "BLOCKED", "estimated_cost": total_cost,
              "limit": budgets["max_estimated_cost"]})
    schedule: list[dict[str, Any]] = []
    for layer_no, layer_ids in enumerate(layers, start=1):
        chunks = [layer_ids[i:i + budgets["max_parallelism"]]
                  for i in range(0, len(layer_ids), budgets["max_parallelism"])]
        for wave_no, chunk in enumerate(chunks, start=1):
            topology = _choose_topology(chunk, by_id, budgets["max_parallelism"])
            schedule.append({"layer": layer_no, "wave": wave_no, "task_ids": chunk,
                             "topology": topology, "execution_claim": "PLAN_ONLY_NOT_CONCURRENT_RUNTIME"})
            _emit(events, "router.topology_selected", None, {"layer": layer_no, "wave": wave_no,
                  "task_ids": chunk, "topology": topology,
                  "reason": "dependency layer, write-set overlap, risk and concurrency budget"})
            for task_id in chunk:
                task = by_id[task_id]
                reasons: list[str] = []
                failed_deps = [dep for dep in task["depends_on"]
                               if outcomes.get(dep, {}).get("status") != "SIMULATION_PASS"]
                if total_cost > budgets["max_estimated_cost"]:
                    reasons.append("aggregate budget exceeded")
                if task["estimated_cost"] > budgets["max_estimated_cost"]:
                    reasons.append("task exceeds cost budget")
                if failed_deps:
                    reasons.append("dependency not simulation-passed: " + ", ".join(failed_deps))
                reasons.extend(_tool_denials(task))
                reasons.extend(_path_denials(task))
                if task["risk"] in {"HIGH", "CRITICAL"} and not task["requires_human_approval"]:
                    reasons.append("high-impact task lacks explicit human approval requirement")
                if reasons:
                    status = "BLOCKED"
                    _emit(events, "policy.gate", task_id, {"result": status, "reasons": reasons})
                    outcomes[task_id] = {"task_id": task_id, "status": status, "reasons": reasons, "topology": topology}
                    continue
                _emit(events, "policy.gate", task_id, {"result": "SIMULATION_CLEAR",
                      "role": task["role"], "risk": task["risk"],
                      "authorized_paths": task["authorized_paths"], "requested_tools": task["requested_tools"]})
                _emit(events, "task.simulation_started", task_id, {"goal": task["goal"],
                      "note": "No external worker was invoked"})
                checks = task["verification"]
                failed = [name for name in ("tests", "adversarial", "replay") if checks[name] != "PASS"]
                refs = checks["evidence_refs"]
                if failed:
                    status = "SIMULATION_FAIL" if any(checks[name] == "FAIL" for name in failed) else "INCONCLUSIVE"
                    reasons = [f"simulated check not PASS: {name}={checks[name]}" for name in failed]
                elif not refs:
                    status, reasons = "INCONCLUSIVE", ["required evidence references absent in scenario"]
                elif task["risk"] in {"HIGH", "CRITICAL"} or task["requires_human_approval"]:
                    status, reasons = "BLOCKED", ["simulation cannot satisfy human approval or high-impact admission gate"]
                else:
                    status, reasons = "SIMULATION_PASS", []
                _emit(events, "verification.simulated", task_id, {"results": {name: checks[name] for name in ("tests", "adversarial", "replay")},
                      "evidence_reference_count": len(refs), "evidence_is_synthetic": True})
                _emit(events, "referee.simulated", task_id, {"verdict": status,
                      "reason_count": len(reasons), "independent_referee_invoked": False})
                outcomes[task_id] = {"task_id": task_id, "status": status, "reasons": reasons,
                      "topology": topology, "synthetic_evidence_refs": refs,
                      "check_results": {name: checks[name] for name in ("tests", "adversarial", "replay")}}
    _emit(events, "simulation.completed", None, {"event_chain_valid_before_completion_event": verify_event_chain(events),
          "simulation_only": True})
    counts: dict[str, int] = {}
    for outcome in outcomes.values():
        counts[outcome["status"]] = counts.get(outcome["status"], 0) + 1
    result = {
        "schema_version": "1.0.0", "simulation_id": scenario["simulation_id"], "mode": "SIMULATION_ONLY",
        "production_execution_performed": False, "model_provider_invoked": False,
        "repository_modified": False, "external_network_used": False, "canonical_status_changed": False,
        "event_chain": {"algorithm": "SHA-256", "valid": verify_event_chain(events), "event_count": len(events)},
        "schedule": schedule,
        "system_snapshot": [{"system_id": s["system_id"], "reported_state": s.get("reported_state", "UNKNOWN"),
                             "connection_state": "NOT_CONNECTED_IN_SIMULATION"} for s in scenario["systems"]],
        "outcomes": [outcomes[t["task_id"]] for t in scenario["tasks"]],
        "metrics": {"tasks_total": len(outcomes), "outcomes_by_status": counts,
                    "estimated_cost": total_cost, "max_estimated_cost": budgets["max_estimated_cost"]},
        "events": events,
        "assurance_notice": "Deterministic fixture simulation, not execution evidence; cannot claim VERIFIED, ADMITTED, merged or production-connected."
    }
    if not result["event_chain"]["valid"]:
        raise RuntimeError("internal event chain verification failed")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True, help="JSON simulation fixture")
    parser.add_argument("--output", type=Path, help="Optional destination for result JSON")
    args = parser.parse_args(argv)
    try:
        with args.scenario.open("r", encoding="utf-8") as handle:
            scenario = json.load(handle)
        rendered = json.dumps(simulate(scenario), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, json.JSONDecodeError, ScenarioError) as exc:
        print(f"SIMULATION INPUT INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
