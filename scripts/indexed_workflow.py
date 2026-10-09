#!/usr/bin/env python3
"""Index-driven VAIXLNS workflow planner.

This is a deterministic, provider-neutral reference planner. It validates a
system/agent routing registry and emits a traceable dispatch plan. It does not
invoke external models, write repositories, approve changes, or execute VX work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "registry" / "agents" / "indexed-workflow.v1.json"
MUTATION_SCOPES = {"NONE", "DOCUMENTATION", "REPOSITORY", "CANONICAL", "PRODUCTION", "EXTERNAL"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
WORKFLOW_TYPES = {
    "archive_recovery", "indexing", "research", "architecture", "innovation",
    "engineering", "integration", "execution", "operations",
}
TARGET_SYSTEMS = {"VAIXLNS", "NEXENT", "VX", "XV", "VV"}
REQUEST_FIELDS = {"request_id", "intent", "work_type", "target_system_id", "requested_capabilities", "mutation_scope", "risk_level", "source_refs", "constraints", "approval_ref", "metadata"}


class WorkflowError(ValueError):
    """Raised when a request or routing registry violates the workflow contract."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"cannot read valid JSON from {path}: {exc}") from exc


def validate_registry(registry: Mapping[str, Any]) -> None:
    if registry.get("registry_id") != "VAIXLNS.INDEXED_WORKFLOW.V1":
        raise WorkflowError("registry_id must be VAIXLNS.INDEXED_WORKFLOW.V1")
    if registry.get("canonical_owner") != "VAIXLNS" or registry.get("master_index_id") != "Ω.000":
        raise WorkflowError("registry must bind to canonical owner VAIXLNS and master index Ω.000")
    if registry.get("runtime_claim") != "REFERENCE_PLANNER_ONLY; no live agent/provider or repository mutation is invoked":
        raise WorkflowError("runtime_claim must retain the reference-only safety boundary")

    systems = registry.get("system_registry")
    agents = registry.get("agents")
    pipelines = registry.get("pipelines")
    if not isinstance(systems, list) or not systems:
        raise WorkflowError("system_registry must be a non-empty list")
    if not isinstance(agents, list) or not agents:
        raise WorkflowError("agents must be a non-empty list")
    if not isinstance(pipelines, dict) or not pipelines:
        raise WorkflowError("pipelines must be a non-empty object")

    system_ids = [item.get("system_id") for item in systems]
    agent_ids = [item.get("agent_id") for item in agents]
    if len(system_ids) != len(set(system_ids)) or None in system_ids:
        raise WorkflowError("system IDs must exist and be unique")
    if len(agent_ids) != len(set(agent_ids)) or None in agent_ids:
        raise WorkflowError("agent IDs must exist and be unique")

    known_systems, known_agents = set(system_ids), set(agent_ids)
    if known_systems != TARGET_SYSTEMS:
        raise WorkflowError(f"system registry must declare exactly {sorted(TARGET_SYSTEMS)}")
    required_agent_ids = {f"AG-{number:03d}" for number in range(1, 14)}
    if known_agents != required_agent_ids:
        raise WorkflowError(f"agent registry must declare AG-001 through AG-013; found {sorted(known_agents)}")
    if set(pipelines) != WORKFLOW_TYPES:
        raise WorkflowError(f"pipeline registry must declare exactly {sorted(WORKFLOW_TYPES)}")
    by_agent = {item["agent_id"]: item for item in agents}
    for system in systems:
        if system.get("may_grant_runtime_authority") is not False:
            raise WorkflowError(f"system {system.get('system_id')} must not self-grant runtime authority")
    for agent in agents:
        if agent.get("primary_system_id") not in known_systems:
            raise WorkflowError(f"agent {agent.get('agent_id')} refers to an unknown primary system")
        for field in ("capabilities", "allowed_actions", "forbidden_actions", "evidence_requirements", "outputs"):
            if not isinstance(agent.get(field), list) or not agent[field]:
                raise WorkflowError(f"agent {agent.get('agent_id')} must declare non-empty {field}")
    required_prohibitions = {
        "AG-001": "delete_legacy_records",
        "AG-002": "silently_merge_entities",
        "AG-007": "canonical_promotion",
        "AG-008": "production_mutation",
        "AG-013": "self_grant_authority",
    }
    for agent_id, prohibition in required_prohibitions.items():
        if prohibition not in by_agent[agent_id]["forbidden_actions"]:
            raise WorkflowError(f"agent {agent_id} must explicitly forbid {prohibition}")
    if by_agent["AG-011"]["primary_system_id"] != "VX":
        raise WorkflowError("AG-011 must remain attached to VX")
    if by_agent["AG-013"]["primary_system_id"] != "VAIXLNS":
        raise WorkflowError("AG-013 must remain attached to VAIXLNS")

    for workflow_type, route in pipelines.items():
        if workflow_type not in WORKFLOW_TYPES:
            raise WorkflowError(f"unsupported pipeline key: {workflow_type}")
        if not isinstance(route, list) or not route:
            raise WorkflowError(f"pipeline {workflow_type} must be a non-empty list")
        if len(route) != len(set(route)):
            raise WorkflowError(f"pipeline {workflow_type} repeats an agent")
        unknown = [agent_id for agent_id in route if agent_id not in known_agents]
        if unknown:
            raise WorkflowError(f"pipeline {workflow_type} refers to unknown agents: {unknown}")
        if "AG-011" in route and route.index("AG-013") > route.index("AG-011"):
            raise WorkflowError(f"pipeline {workflow_type} places execution before governance review")
        if "AG-011" in route and "AG-010" in route and route.index("AG-010") > route.index("AG-011"):
            raise WorkflowError(f"pipeline {workflow_type} places execution before verification")

    invariants = set(registry.get("global_invariants", []))
    required = {
        "historical_sources_are_append_only",
        "unknown_legacy_ids_remain_unmapped",
        "agent_identity_never_implies_authority",
        "NEXENT_proposes_but_does_not_execute_canonical_changes",
        "VX_execution_requires_independent_admission_authority",
        "verification_and_authority_are_separate",
        "runtime_execution_is_disabled_in_reference_planner",
        "a_proposal_never_self_promotes_to_verified_or_canonical",
    }
    if not required.issubset(invariants):
        raise WorkflowError(f"missing registry invariants: {sorted(required - invariants)}")


def validate_request(request: Mapping[str, Any], registry: Mapping[str, Any]) -> None:
    unknown_fields = set(request) - REQUEST_FIELDS
    if unknown_fields:
        raise WorkflowError(f"unsupported request fields: {sorted(unknown_fields)}")
    if request.get("request_id") is not None and (not isinstance(request.get("request_id"), str) or not request["request_id"].strip()):
        raise WorkflowError("request_id must be a non-empty string when supplied")
    if not isinstance(request.get("intent"), str) or len(request["intent"].strip()) < 8:
        raise WorkflowError("intent must contain at least 8 non-whitespace characters")
    if request.get("work_type") not in WORKFLOW_TYPES:
        raise WorkflowError(f"work_type must be one of {sorted(WORKFLOW_TYPES)}")
    if request.get("mutation_scope") not in MUTATION_SCOPES:
        raise WorkflowError(f"mutation_scope must be one of {sorted(MUTATION_SCOPES)}")
    if request.get("risk_level") not in RISK_LEVELS:
        raise WorkflowError(f"risk_level must be one of {sorted(RISK_LEVELS)}")
    target = request.get("target_system_id")
    if target is not None and target not in {item["system_id"] for item in registry["system_registry"]}:
        raise WorkflowError(f"unknown target_system_id: {target}")
    capabilities = request.get("requested_capabilities", [])
    if not isinstance(capabilities, list) or any(not isinstance(item, str) or not item.strip() for item in capabilities):
        raise WorkflowError("requested_capabilities must be a list of non-empty strings")
    if len(capabilities) != len(set(capabilities)):
        raise WorkflowError("requested_capabilities cannot contain duplicates")
    for field in ("source_refs", "constraints"):
        value = request.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise WorkflowError(f"{field} must be a list of non-empty strings")
    if request.get("approval_ref") is not None and (not isinstance(request.get("approval_ref"), str) or not request["approval_ref"].strip()):
        raise WorkflowError("approval_ref must be a non-empty string reference when supplied")
    if request.get("metadata") is not None and not isinstance(request.get("metadata"), dict):
        raise WorkflowError("metadata must be an object when supplied")


def _make_event(event_type: str, sequence: int, payload: Mapping[str, Any], previous_hash: str) -> dict[str, Any]:
    base = {
        "sequence": sequence,
        "event_type": event_type,
        "payload": dict(payload),
        "previous_event_hash": previous_hash,
    }
    return {**base, "event_hash": digest(base)}


def build_plan(request: Mapping[str, Any], registry: Mapping[str, Any], registry_digest: str) -> dict[str, Any]:
    validate_registry(registry)
    validate_request(request, registry)

    agent_map = {agent["agent_id"]: agent for agent in registry["agents"]}
    system_map = {system["system_id"]: system for system in registry["system_registry"]}
    route = registry["pipelines"][request["work_type"]]
    requested_capabilities = set(request.get("requested_capabilities", []))
    route_capabilities = {cap for agent_id in route for cap in agent_map[agent_id]["capabilities"]}
    unmatched = sorted(requested_capabilities - route_capabilities)
    if unmatched:
        raise WorkflowError(f"requested capabilities are not covered by the selected pipeline: {unmatched}")

    request_payload = dict(request)
    request_payload.setdefault("source_refs", [])
    request_payload.setdefault("constraints", [])
    request_payload.setdefault("requested_capabilities", [])
    request_id = request_payload.get("request_id") or f"WF-{digest(request_payload)[:12].upper()}"
    mutation_scope = request_payload["mutation_scope"]
    elevated_risk = request_payload["risk_level"] in {"HIGH", "CRITICAL"}
    runtime_work = request_payload["work_type"] == "execution"
    authority_required = mutation_scope != "NONE" or elevated_risk or runtime_work

    steps: list[dict[str, Any]] = []
    for index, agent_id in enumerate(route, start=1):
        agent = agent_map[agent_id]
        is_executor = agent_id == "AG-011"
        status = "PLANNED"
        if is_executor:
            status = "BLOCKED_REFERENCE_PLANNER_ONLY"
        elif agent_id == "AG-013" and authority_required:
            status = "HOLD_FOR_INDEPENDENT_AUTHORITY_REVIEW"
        elif agent_id == "AG-010":
            status = "PLANNED_INDEPENDENT_VERIFICATION"
        steps.append({
            "step": index,
            "agent_id": agent_id,
            "agent_name": agent["canonical_name"],
            "primary_system_id": agent["primary_system_id"],
            "system_role": system_map[agent["primary_system_id"]]["role"],
            "capabilities": agent["capabilities"],
            "expected_outputs": agent["outputs"],
            "status": status,
            "authority_ceiling": agent["authority_ceiling"],
            "forbidden_actions": agent["forbidden_actions"],
            "handoff_to": route[index] if index < len(route) else None,
            "handoff_requires_contract_validation": index < len(route),
        })

    if authority_required:
        plan_status = "HOLD_FOR_AUTHORITY_AND_ADAPTER"
        blocked_reasons = []
        if mutation_scope != "NONE":
            blocked_reasons.append(f"MUTATION_SCOPE_REQUIRES_AUTHORIZATION:{mutation_scope}")
        if elevated_risk:
            blocked_reasons.append(f"RISK_REQUIRES_INDEPENDENT_REVIEW:{request_payload['risk_level']}")
        if runtime_work:
            blocked_reasons.append("RUNTIME_EXECUTION_DISABLED_IN_REFERENCE_PLANNER")
        blocked_reasons.append("NO_VERIFIABLE_AUTHORITY_ISSUER_OR_LIVE_ADAPTER_CONFIGURED")
    else:
        plan_status = "PLAN_READY_NOT_EXECUTED"
        blocked_reasons = ["REFERENCE_PLANNER_EMITS_A_PLAN_ONLY"]

    base: dict[str, Any] = {
        "schema_version": "1.0.0",
        "plan_kind": "VAIXLNS_INDEX_DRIVEN_WORKFLOW_PLAN",
        "plan_status": plan_status,
        "request_id": request_id,
        "intent": request_payload["intent"],
        "work_type": request_payload["work_type"],
        "target_system_id": request_payload.get("target_system_id"),
        "requested_capabilities": request_payload["requested_capabilities"],
        "mutation_scope": mutation_scope,
        "risk_level": request_payload["risk_level"],
        "authority_required": authority_required,
        "blocked_reasons": blocked_reasons,
        "master_index_id": registry.get("master_index_id", "Ω.000"),
        "master_index_item_mapping": registry.get("master_index_item_mapping"),
        "source_refs": request_payload["source_refs"],
        "constraints": request_payload["constraints"],
        "metadata": request_payload.get("metadata", {}),
        "approval_reference_not_verified": request_payload.get("approval_ref"),
        "registry_id": registry["registry_id"],
        "registry_sha256": registry_digest,
        "execution": {
            "mode": "PLAN_ONLY_REFERENCE",
            "external_agent_calls_performed": False,
            "repository_mutations_performed": False,
            "vx_runtime_calls_performed": False,
            "canonical_promotion_performed": False,
            "approval_ref_is_verified": False,
        },
        "steps": steps,
    }
    base["plan_id"] = f"PLAN-{digest(base)[:16].upper()}"
    events = []
    previous = "GENESIS"
    first = _make_event("WORKFLOW_PLAN_CREATED", 1, {"request_id": request_id, "plan_id": base["plan_id"], "plan_status": plan_status}, previous)
    events.append(first)
    previous = first["event_hash"]
    if authority_required:
        second = _make_event("AUTHORITY_GATE_HOLD", 2, {"request_id": request_id, "blocked_reasons": blocked_reasons}, previous)
        events.append(second)
    base["trace_events"] = events
    base["trace_scope"] = "DETERMINISTIC_PLAN_TRACE_NOT_A_RUNTIME_LEDGER_OR_PROOF"
    base["plan_sha256"] = digest(base)
    return base


def validate_plan(plan: Mapping[str, Any], registry: Mapping[str, Any]) -> None:
    previous_hash = "GENESIS"
    for expected_sequence, event in enumerate(plan.get("trace_events", []), start=1):
        event_body = {key: value for key, value in event.items() if key != "event_hash"}
        if event.get("sequence") != expected_sequence or event.get("previous_event_hash") != previous_hash:
            raise WorkflowError("trace event sequence or previous hash is invalid")
        if event.get("event_hash") != digest(event_body):
            raise WorkflowError("trace event hash is invalid")
        previous_hash = event["event_hash"]
    expected_plan_digest = plan.get("plan_sha256")
    digest_body = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if expected_plan_digest != digest(digest_body):
        raise WorkflowError("plan_sha256 does not match the rendered plan body")
    if plan.get("execution", {}).get("mode") != "PLAN_ONLY_REFERENCE":
        raise WorkflowError("reference planner must never claim executable mode")
    for field in ("external_agent_calls_performed", "repository_mutations_performed", "vx_runtime_calls_performed", "canonical_promotion_performed", "approval_ref_is_verified"):
        if plan.get("execution", {}).get(field) is not False:
            raise WorkflowError(f"reference planner safety flag must remain false: {field}")
    known_agents = {agent["agent_id"] for agent in registry["agents"]}
    known_systems = {system["system_id"] for system in registry["system_registry"]}
    for step in plan.get("steps", []):
        if step.get("agent_id") not in known_agents:
            raise WorkflowError(f"unknown agent in plan: {step.get('agent_id')}")
        if step.get("primary_system_id") not in known_systems:
            raise WorkflowError(f"unknown primary system in plan: {step.get('primary_system_id')}")
        if step.get("agent_id") == "AG-011" and step.get("status") != "BLOCKED_REFERENCE_PLANNER_ONLY":
            raise WorkflowError("runtime/integration agent must remain blocked in the reference planner")


def generate(request_path: Path, registry_path: Path) -> dict[str, Any]:
    request = read_json(request_path)
    registry = read_json(registry_path)
    validate_registry(registry)
    plan = build_plan(request, registry, file_digest(registry_path))
    validate_plan(plan, registry)
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic VAIXLNS index-driven workflow plan.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="path to the system/agent routing registry")
    parser.add_argument("--request", type=Path, help="JSON workflow request; required unless --validate-registry is used")
    parser.add_argument("--output", type=Path, help="optional output path; defaults to stdout")
    parser.add_argument("--validate-registry", action="store_true", help="validate routing contracts and exit")
    args = parser.parse_args(argv)

    try:
        registry = read_json(args.registry)
        validate_registry(registry)
        if args.validate_registry:
            result: dict[str, Any] = {
                "status": "REGISTRY_VALID",
                "registry_id": registry["registry_id"],
                "system_count": len(registry["system_registry"]),
                "agent_count": len(registry["agents"]),
                "pipeline_count": len(registry["pipelines"]),
                "registry_sha256": file_digest(args.registry),
            }
        else:
            if args.request is None:
                parser.error("--request is required unless --validate-registry is used")
            result = generate(args.request, args.registry)
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except WorkflowError as exc:
        print(f"WORKFLOW_CONTRACT_FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
