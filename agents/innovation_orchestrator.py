"""Deterministic planner for governed multi-agent engineering missions.

This module plans agent work; it does not invoke models, tools, or external effects.
Runtime/provider connectivity must be implemented and evidenced separately.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Any, Iterable

from agents.agent_fabric import AgentRegistry, DEFAULT_HANDOFF_CHAIN

PLAN_SCHEMA = "vaixlns.agent-mission-plan.v1"
TERMINAL_STATES = {"BLOCKED", "CANCELLED", "COMPLETED"}
FORBIDDEN_AUTHORITY = {"canonical-write", "production-deploy", "self-promote", "financial-transfer"}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _clean_text(value: str, field: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise ValueError(f"{field.upper()}_REQUIRED")
    return value


def _safe_ref(ref: str) -> str:
    ref = _clean_text(ref, "source_ref")
    if ref.startswith(("http://", "https://", "git@", "file://")):
        return ref
    if ref.startswith("/") or ".." in ref.replace("\\", "/").split("/"):
        raise ValueError("SOURCE_REF_MUST_NOT_ESCAPE_WORKSPACE")
    return ref


@dataclass(frozen=True)
class MissionRequest:
    intent: str
    required_capabilities: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    requested_actions: tuple[str, ...] = ()
    mission_id: str | None = None

    def normalized(self) -> dict[str, Any]:
        intent = _clean_text(self.intent, "intent")
        capabilities = tuple(sorted({_clean_text(x, "capability") for x in self.required_capabilities}))
        constraints = tuple(sorted({_clean_text(x, "constraint") for x in self.constraints}))
        refs = tuple(sorted({_safe_ref(x) for x in self.source_refs}))
        actions = tuple(sorted({_clean_text(x, "requested_action").lower() for x in self.requested_actions}))
        prohibited = sorted(set(actions).intersection(FORBIDDEN_AUTHORITY))
        if prohibited:
            raise PermissionError("PROHIBITED_AUTONOMOUS_ACTION:" + ",".join(prohibited))
        return {"intent": intent, "required_capabilities": list(capabilities),
                "constraints": list(constraints), "source_refs": list(refs),
                "requested_actions": list(actions)}


@dataclass(frozen=True)
class PlannedTask:
    task_id: str
    agent_id: str
    role: str
    objective: str
    depends_on: tuple[str, ...]
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    state: str = "PLANNED"
    authority_scope: tuple[str, ...] = ("read:assigned-evidence",)
    execution_permitted: bool = False
    promotion_permitted: bool = False


def build_mission_plan(request: MissionRequest, registry: AgentRegistry | None = None) -> dict[str, Any]:
    registry = registry or AgentRegistry()
    errors = registry.validate_handoff_chain(DEFAULT_HANDOFF_CHAIN)
    if errors:
        raise ValueError("AGENT_HANDOFF_CONTRACT_INVALID:" + "|".join(errors))
    mission = request.normalized()
    available = {cap for agent in registry.all() for cap in agent.capabilities}
    missing = sorted(set(mission["required_capabilities"]) - available)
    canonical_request = {"schema_version": PLAN_SCHEMA, "mission": mission,
                         "handoff_chain": list(DEFAULT_HANDOFF_CHAIN)}
    mission_hash = canonical_hash(canonical_request)
    mission_id = request.mission_id or "MIS-" + mission_hash[:16]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", mission_id):
        raise ValueError("MISSION_ID_INVALID")
    tasks: list[PlannedTask] = []
    previous: str | None = None
    for index, agent_id in enumerate(DEFAULT_HANDOFF_CHAIN):
        agent = registry.get(agent_id)
        task_material = {"mission_hash": mission_hash, "agent_id": agent_id, "sequence": index + 1}
        task_id = "TASK-" + canonical_hash(task_material)[:16]
        objective = agent.mission
        if agent_id == "AG-00-ORCHESTRATOR":
            objective = "Decompose and route mission: " + mission["intent"]
        elif agent_id == "AG-01-SOURCE-DISCOVERY":
            objective = "Collect version-pinned sources for the mission and record coverage gaps."
        elif agent_id == "AG-04-NOVELTY-LINEAGE":
            objective = "Compare candidates with indexed innovations and preserve unresolved lineage."
        elif agent_id == "AG-05-COUNTEREVIDENCE":
            objective = "Search for counterevidence, falsifying cases, and alternative explanations."
        elif agent_id == "AG-10-TEST-VERIFICATION":
            objective = "Create reproducible tests for explicit engineering invariants and failure cases."
        elif agent_id == "AG-11-PROOF-INTEGRITY":
            objective = "Validate source lineage, artifact digests, replay evidence, and proof completeness."
        elif agent_id == "AG-12-GOVERNANCE-REVIEW":
            objective = "Prepare a decision package; do not approve or commit changes."
        inputs = agent.accepts
        outputs = agent.emits
        # Source references and user constraints are context, never executable instructions.
        if index == 0:
            inputs = ("mission_request",)
        tasks.append(PlannedTask(task_id, agent_id, agent.role, objective,
            (previous,) if previous else (), tuple(inputs), tuple(outputs),
            tuple(sorted(set(agent.capabilities).intersection(mission["required_capabilities"])))))
        previous = task_id
    payload = {
        "schema_version": PLAN_SCHEMA,
        "mission_id": mission_id,
        "mission_hash": mission_hash,
        "plan_hash": "",
        "status": "BLOCKED" if missing else "PLANNED",
        "status_reason": ("UNSUPPORTED_REQUIRED_CAPABILITIES:" + ",".join(missing)) if missing else "PLAN_ONLY_NO_AGENT_PROVIDER_EXECUTED",
        "mission": mission,
        "source_context": {"refs": mission["source_refs"], "pinned_revision_required": True,
                           "evidence_state": "UNVERIFIED_UNTIL_RETRIEVED"},
        "tasks": [asdict(task) for task in tasks],
        "coverage": {"required_capabilities": mission["required_capabilities"],
                     "unsupported_capabilities": missing, "agent_count": len(tasks),
                     "handoff_contract": "PASS", "all_tasks_have_explicit_state": True},
        "governance": {"authority_decision": "PENDING", "self_authority": False,
                       "canonical_write_permitted": False, "production_execution_permitted": False,
                       "financial_execution_permitted": False},
        "evidence": {"provider_calls": 0, "tool_calls": 0, "execution_events": [],
                     "semantic_correctness": "NOT_CLAIMED", "proof_status": "PENDING"},
    }
    payload["plan_hash"] = canonical_hash(payload)
    return payload


def validate_mission_plan(plan: dict[str, Any], registry: AgentRegistry | None = None) -> tuple[str, ...]:
    registry = registry or AgentRegistry()
    errors: list[str] = []
    if plan.get("schema_version") != PLAN_SCHEMA:
        errors.append("PLAN_SCHEMA_INVALID")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != len(DEFAULT_HANDOFF_CHAIN):
        return tuple(errors + ["TASK_COUNT_INVALID"])
    seen: set[str] = set()
    previous: str | None = None
    for index, task in enumerate(tasks):
        if task.get("agent_id") != DEFAULT_HANDOFF_CHAIN[index]:
            errors.append(f"TASK_ORDER_INVALID:{index}")
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id or task_id in seen:
            errors.append(f"TASK_ID_INVALID:{index}")
        seen.add(task_id)
        expected_deps = (previous,) if previous else ()
        if task.get("depends_on") != expected_deps:
            errors.append(f"TASK_DEPENDENCY_INVALID:{task_id}")
        if task.get("state") != "PLANNED":
            errors.append(f"TASK_STATE_INVALID:{task_id}")
        if task.get("execution_permitted") is not False or task.get("promotion_permitted") is not False:
            errors.append(f"TASK_AUTHORITY_ESCALATION:{task_id}")
        try:
            agent = registry.get(task.get("agent_id", ""))
            if tuple(task.get("expected_outputs", ())) != agent.emits:
                errors.append(f"TASK_OUTPUT_CONTRACT_INVALID:{task_id}")
        except KeyError:
            errors.append(f"TASK_AGENT_UNKNOWN:{task_id}")
        previous = task_id
    governance = plan.get("governance", {})
    if governance.get("self_authority") is not False:
        errors.append("SELF_AUTHORITY_MUST_BE_FALSE")
    if governance.get("authority_decision") != "PENDING":
        errors.append("AUTHORITY_DECISION_MUST_REMAIN_PENDING")
    if governance.get("canonical_write_permitted") is not False:
        errors.append("CANONICAL_WRITE_MUST_REMAIN_DISABLED")
    if governance.get("production_execution_permitted") is not False:
        errors.append("PRODUCTION_EXECUTION_MUST_REMAIN_DISABLED")
    return tuple(errors)


__all__ = ["MissionRequest", "PlannedTask", "build_mission_plan", "validate_mission_plan", "canonical_hash"]
