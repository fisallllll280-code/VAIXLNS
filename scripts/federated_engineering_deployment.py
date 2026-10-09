"""Plan federated engineering deployments and route tasks with hard safety gates.

This reference planner emits an auditable plan only. It does not deploy, mutate
repositories, start services, or grant production authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


RELEASE_GATES = (
    "PINNED_SOURCE_REVISION",
    "DEPENDENCIES_RESOLVED",
    "BUILD_AND_TEST_PASS",
    "SANDBOX_STARTUP_AND_HEALTH_PASS",
    "INTEGRATION_SMOKE_PASS",
    "INDEPENDENT_VERIFICATION_PASS",
    "EVIDENCE_AND_ROLLBACK_READY",
    "SEPARATE_GOVERNANCE_ADMISSION",
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _stable_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:24]}"


def _load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_manifest(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema") != "vaixlns.federated-engineering-deployment.v1":
        raise ValueError("UNSUPPORTED_DEPLOYMENT_MANIFEST_SCHEMA")
    if manifest.get("mode") != "PLAN_ONLY":
        raise ValueError("DEPLOYMENT_PLANNER_REQUIRES_PLAN_ONLY_MODE")
    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict):
        raise ValueError("DEPLOYMENT_DEFAULTS_MUST_BE_AN_OBJECT")
    if defaults.get("execution_enabled") is not False:
        raise ValueError("REFERENCE_PLANNER_MUST_NOT_ENABLE_EXECUTION")
    if defaults.get("automatic_production_deployment") is not False:
        raise ValueError("AUTOMATIC_PRODUCTION_DEPLOYMENT_MUST_REMAIN_DISABLED")

    systems = manifest.get("systems")
    if not isinstance(systems, list) or not systems:
        raise ValueError("SYSTEMS_MUST_BE_A_NONEMPTY_LIST")

    by_id: dict[str, dict[str, Any]] = {}
    for system in systems:
        if not isinstance(system, dict):
            raise ValueError("SYSTEM_ENTRY_MUST_BE_AN_OBJECT")
        system_id = system.get("system_id")
        if not isinstance(system_id, str) or not system_id.strip():
            raise ValueError("SYSTEM_ID_REQUIRED")
        if system_id in by_id:
            raise ValueError(f"DUPLICATE_SYSTEM_ID:{system_id}")
        if system.get("identity_status") not in {"VERIFIED", "UNVERIFIED", "CONFLICT"}:
            raise ValueError(f"INVALID_IDENTITY_STATUS:{system_id}")
        repos = system.get("repositories")
        if not isinstance(repos, list) or not repos:
            raise ValueError(f"SYSTEM_REPOSITORIES_REQUIRED:{system_id}")
        for repository in repos:
            full_name = repository.get("full_name") if isinstance(repository, dict) else None
            if not isinstance(full_name, str) or len(full_name.split("/")) != 2:
                raise ValueError(f"INVALID_REPOSITORY_FULL_NAME:{system_id}")
        deps = system.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            raise ValueError(f"INVALID_DEPENDENCY_LIST:{system_id}")
        by_id[system_id] = system

    for system_id, system in by_id.items():
        for dependency in system.get("depends_on", []):
            if dependency not in by_id:
                raise ValueError(f"UNKNOWN_DEPENDENCY:{system_id}:{dependency}")
            if dependency == system_id:
                raise ValueError(f"SELF_DEPENDENCY:{system_id}")

    # A DFS detects indirect dependency cycles before building rollout waves.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(system_id: str) -> None:
        if system_id in visiting:
            raise ValueError(f"DEPENDENCY_CYCLE:{system_id}")
        if system_id in visited:
            return
        visiting.add(system_id)
        for dependency in by_id[system_id].get("depends_on", []):
            visit(dependency)
        visiting.remove(system_id)
        visited.add(system_id)

    for system_id in sorted(by_id):
        visit(system_id)

    return systems


def _depths(systems: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    by_id = {str(system["system_id"]): system for system in systems}
    depths: dict[str, int] = {}

    def depth(system_id: str) -> int:
        if system_id not in depths:
            dependencies = by_id[system_id].get("depends_on", [])
            depths[system_id] = 0 if not dependencies else 1 + max(depth(dep) for dep in dependencies)
        return depths[system_id]

    for system_id in sorted(by_id):
        depth(system_id)
    return depths


def build_plan(
    manifest: Mapping[str, Any],
    environment: str = "sandbox",
    target_system_ids: Sequence[str] | None = None,
    max_parallelism: int | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-executing deployment plan."""
    systems = validate_manifest(manifest)
    by_id = {str(system["system_id"]): system for system in systems}
    requested = set(target_system_ids or by_id.keys())
    unknown = requested - set(by_id)
    if unknown:
        raise ValueError("UNKNOWN_TARGET_SYSTEMS:" + ",".join(sorted(unknown)))

    # Include dependency closure so a subset cannot skip a required parent.
    closure = set(requested)
    pending = list(requested)
    while pending:
        current = pending.pop()
        for dependency in by_id[current].get("depends_on", []):
            if dependency not in closure:
                closure.add(dependency)
                pending.append(dependency)

    depths = _depths(systems)
    configured_parallelism = int(
        max_parallelism
        if max_parallelism is not None
        else manifest.get("defaults", {}).get("max_parallel_system_rollouts", 1)
    )
    if configured_parallelism < 1:
        raise ValueError("MAX_PARALLELISM_MUST_BE_POSITIVE")
    if environment == "production":
        production_blocker = "PRODUCTION_DEPLOYMENT_REQUIRES_SEPARATE_AUTHORIZED_RELEASE_CONTROLLER"
    elif environment not in {"sandbox", "ci"}:
        raise ValueError("UNSUPPORTED_ENVIRONMENT")

    planned: dict[str, dict[str, Any]] = {}
    for system_id in sorted(closure, key=lambda key: (depths[key], key)):
        system = by_id[system_id]
        blockers: list[str] = []
        if system.get("identity_status") != "VERIFIED":
            blockers.append("SYSTEM_IDENTITY_NOT_VERIFIED")
        if environment == "production":
            blockers.append(production_blocker)

        for dependency in system.get("depends_on", []):
            dependency_plan = planned.get(dependency)
            if dependency_plan is None or dependency_plan["status"] == "HOLD":
                blockers.append(f"DEPENDENCY_NOT_READY:{dependency}")

        repository_rows = []
        for repository in system["repositories"]:
            repository_rows.append({
                "full_name": repository["full_name"],
                "surface": repository.get("surface", "UNSPECIFIED"),
                "observed_runtime_status": repository.get("runtime_status", "UNKNOWN"),
                "required_revision": "IMMUTABLE_COMMIT_SHA_REQUIRED",
                "execution_status": "NOT_RUN",
            })

        status = "HOLD" if blockers else "PLAN_READY"
        plan_row = {
            "system_id": system_id,
            "role": system["role"],
            "identity_status": system["identity_status"],
            "status": status,
            "rollout_wave": None if blockers else depths[system_id] + 1,
            "depends_on": list(system.get("depends_on", [])),
            "repositories": repository_rows,
            "required_release_gates": list(manifest.get("release_gates", RELEASE_GATES)),
            "blockers": sorted(set(blockers)),
            "execution_authorized": False,
            "production_mutation_authorized": False,
            "actual_deployment_observed": False,
        }
        plan_row["system_plan_id"] = _stable_id("VXDEPLOY", plan_row)
        planned[system_id] = plan_row

    grouped: dict[int, list[str]] = {}
    for system_id in sorted(planned):
        row = planned[system_id]
        if row["status"] == "PLAN_READY":
            grouped.setdefault(int(row["rollout_wave"]), []).append(system_id)

    waves = []
    for wave_number in sorted(grouped):
        members = grouped[wave_number]
        # Parallel fan-out is bounded; it is a proposed schedule, not a live rollout.
        for offset in range(0, len(members), configured_parallelism):
            batch = members[offset:offset + configured_parallelism]
            waves.append({
                "wave": wave_number,
                "system_ids": batch,
                "parallelism": len(batch),
                "strategy": "BOUNDED_PARALLEL_AFTER_DEPENDENCY_AND_POLICY_GATES",
                "execution_started": False,
            })

    ordered_systems = [planned[key] for key in sorted(planned, key=lambda key: (depths[key], key))]
    plan_material = {
        "manifest_schema": manifest["schema"],
        "environment": environment,
        "systems": ordered_systems,
        "waves": waves,
        "max_parallelism": configured_parallelism,
    }
    return {
        "schema": "vaixlns.federated-engineering-deployment-plan.v1",
        "plan_id": _stable_id("VXRELEASEPLAN", plan_material),
        "authority": manifest.get("authority", "UNSPECIFIED"),
        "mode": "PLAN_ONLY",
        "environment": environment,
        "target_system_count": len(ordered_systems),
        "plan_ready_count": sum(row["status"] == "PLAN_READY" for row in ordered_systems),
        "held_count": sum(row["status"] == "HOLD" for row in ordered_systems),
        "max_parallelism": configured_parallelism,
        "waves": waves,
        "systems": ordered_systems,
        "latency_policy": {
            "hard_identity_authority_health_and_data_classification_gates_precede_ranking": True,
            "worker_selection": "MINIMUM_ESTIMATED_COMPLETION_LATENCY_AMONG_ELIGIBLE_WORKERS",
            "queue_depth_and_transfer_cost_are_included": True,
            "uncached_or_unverified_outputs_are_not_reused_as_proof": True,
        },
        "required_global_gates": [
            "PINNED_SOURCE_REVISION",
            "DEPENDENCIES_RESOLVED",
            "BUILD_AND_TEST_PASS",
            "SANDBOX_STARTUP_AND_HEALTH_PASS",
            "INTEGRATION_SMOKE_PASS",
            "INDEPENDENT_VERIFICATION_PASS",
            "EVIDENCE_AND_ROLLBACK_READY",
            "SEPARATE_GOVERNANCE_ADMISSION",
        ],
        "execution_authorized": False,
        "canonical_promotion_allowed": False,
        "invariants": [
            "UNVERIFIED_SYSTEM_IDENTITY_MEANS_HOLD",
            "CI_PASS_DOES_NOT_EQUAL_DEPLOYMENT",
            "DEPLOYMENT_DOES_NOT_EQUAL_AUTHORIZATION",
            "NO_AUTOMATIC_PRODUCTION_MUTATION",
            "PRESERVE_REPOSITORY_AND_SYSTEM_IDENTITY_BOUNDARIES",
        ],
    }


def choose_worker(task: Mapping[str, Any], workers: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Choose the lowest predicted-latency worker after non-negotiable eligibility gates.

    Required task fields: capability, authority_scope, data_classification.
    Worker fields include identity_status, state, capabilities, authority_scopes,
    allowed_data_classifications, queue_depth, queue_wait_ms, service_p95_ms,
    network_penalty_ms, cold_start_ms, cached_keys, and cache_savings_ms.
    """
    required = {
        "capability": task.get("capability"),
        "authority_scope": task.get("authority_scope"),
        "data_classification": task.get("data_classification", "PUBLIC"),
    }
    if not required["capability"] or not required["authority_scope"]:
        raise ValueError("TASK_CAPABILITY_AND_AUTHORITY_SCOPE_REQUIRED")

    candidates = []
    rejected = []
    for worker in workers:
        worker_id = worker.get("worker_id")
        reason = None
        if not isinstance(worker_id, str) or not worker_id:
            reason = "WORKER_ID_MISSING"
        elif worker.get("identity_status") != "VERIFIED":
            reason = "WORKER_IDENTITY_NOT_VERIFIED"
        elif worker.get("state") != "ACTIVE":
            reason = "WORKER_NOT_ACTIVE"
        elif required["capability"] not in worker.get("capabilities", []):
            reason = "CAPABILITY_MISMATCH"
        elif required["authority_scope"] not in worker.get("authority_scopes", []):
            reason = "AUTHORITY_SCOPE_MISMATCH"
        elif required["data_classification"] not in worker.get("allowed_data_classifications", []):
            reason = "DATA_CLASSIFICATION_MISMATCH"

        if reason:
            rejected.append({"worker_id": worker_id or "UNKNOWN", "reason": reason})
            continue

        queue_depth = max(0, int(worker.get("queue_depth", 0)))
        queue_wait_ms = max(0, int(worker.get("queue_wait_ms", 0)))
        service_ms = max(0, int(worker.get("service_p95_ms", 0)))
        transfer_ms = max(0, int(worker.get("network_penalty_ms", 0)))
        startup_ms = max(0, int(worker.get("cold_start_ms", 0)))
        cache_savings = 0
        cache_key = task.get("cache_key")
        if cache_key and cache_key in worker.get("cached_keys", []):
            cache_savings = max(0, int(worker.get("cache_savings_ms", 0)))

        estimated_ms = max(0, queue_depth * queue_wait_ms + service_ms + transfer_ms + startup_ms - cache_savings)
        candidates.append({
            "worker_id": worker_id,
            "estimated_completion_ms": estimated_ms,
            "capability": required["capability"],
            "authority_scope": required["authority_scope"],
            "data_classification": required["data_classification"],
        })

    if not candidates:
        return {
            "status": "HOLD_NO_ELIGIBLE_WORKER",
            "selected_worker_id": None,
            "estimated_completion_ms": None,
            "rejected_workers": sorted(rejected, key=lambda item: str(item["worker_id"])),
        }

    selected = sorted(candidates, key=lambda item: (item["estimated_completion_ms"], item["worker_id"]))[0]
    risk = str(task.get("risk", "HIGH")).upper()
    fast_path = (
        risk == "LOW"
        and task.get("read_only") is True
        and task.get("idempotent") is True
        and task.get("side_effects") is False
    )
    return {
        "status": "ROUTED_FOR_PLANNING",
        **selected,
        "route_class": "FAST_PATH" if fast_path else "CONTROLLED_PATH",
        "execution_authorized": False,
        "rejected_workers": sorted(rejected, key=lambda item: str(item["worker_id"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to the federation deployment JSON manifest")
    parser.add_argument("--environment", default="sandbox", choices=("ci", "sandbox", "production"))
    parser.add_argument("--target", action="append", default=None, help="Optional system ID; repeat for multiple targets")
    parser.add_argument("--max-parallelism", type=int, default=None)
    parser.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")
    args = parser.parse_args()

    plan = build_plan(
        _load_json(args.manifest),
        environment=args.environment,
        target_system_ids=args.target,
        max_parallelism=args.max_parallelism,
    )
    rendered = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(rendered, end="")
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
