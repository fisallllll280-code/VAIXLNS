"""Isolated, dependency-free work planner for evaluating agent orchestration adapters.

This module creates plans only. It never invokes an LLM, executes a task, calls a
server, or mutates canonical VAIXLNS state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


class PlanError(ValueError):
    """Raised when a work graph or its capability policy is invalid."""


@dataclass(frozen=True)
class AgentCapability:
    agent_id: str
    capabilities: tuple[str, ...]
    allowed_effects: tuple[str, ...] = ("read_only",)

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise PlanError("AGENT_ID_REQUIRED")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise PlanError("DUPLICATE_AGENT_CAPABILITY")
        if any(effect not in {"read_only", "workspace_write", "external_effect", "canonical_write"}
               for effect in self.allowed_effects):
            raise PlanError("UNKNOWN_EFFECT_CLASS")
        if "canonical_write" in self.allowed_effects:
            raise PlanError("CANONICAL_WRITE_FORBIDDEN_IN_EXPERIMENT")


@dataclass(frozen=True)
class WorkItem:
    task_id: str
    role: str
    required_capabilities: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    effect_class: str = "read_only"

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.role.strip():
            raise PlanError("TASK_ID_AND_ROLE_REQUIRED")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise PlanError("DUPLICATE_DEPENDENCY")
        if self.effect_class not in {"read_only", "workspace_write", "external_effect", "canonical_write"}:
            raise PlanError("UNKNOWN_EFFECT_CLASS")
        if self.effect_class in {"external_effect", "canonical_write"}:
            raise PlanError("EFFECT_CLASS_FORBIDDEN_IN_PLAN_ONLY_EXPERIMENT")


@dataclass(frozen=True)
class PlannedTask:
    task_id: str
    agent_id: str
    depends_on: tuple[str, ...]
    effect_class: str


@dataclass(frozen=True)
class PlanReceipt:
    schema_version: str
    mode: str
    tasks: tuple[PlannedTask, ...]
    events: tuple[dict[str, object], ...]
    plan_hash: str


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def build_plan(work_items: Iterable[WorkItem], agents: Iterable[AgentCapability]) -> PlanReceipt:
    """Validate capabilities and dependencies, then produce a deterministic plan."""
    items = tuple(work_items)
    roster = tuple(agents)
    by_task = {item.task_id: item for item in items}
    by_agent = {agent.agent_id: agent for agent in roster}

    if len(by_task) != len(items):
        raise PlanError("DUPLICATE_TASK_ID")
    if len(by_agent) != len(roster):
        raise PlanError("DUPLICATE_AGENT_ID")
    if not items:
        raise PlanError("EMPTY_WORK_GRAPH")

    for item in items:
        unknown = set(item.depends_on) - set(by_task)
        if unknown:
            raise PlanError("UNKNOWN_DEPENDENCY:" + ",".join(sorted(unknown)))
        if item.task_id in item.depends_on:
            raise PlanError("SELF_DEPENDENCY:" + item.task_id)

    # Stable topological sort: among ready tasks, preserve declared input order.
    input_order = {item.task_id: i for i, item in enumerate(items)}
    pending = set(by_task)
    ordered: list[WorkItem] = []
    completed: set[str] = set()
    while pending:
        ready = sorted(
            (task_id for task_id in pending if set(by_task[task_id].depends_on) <= completed),
            key=input_order.__getitem__,
        )
        if not ready:
            raise PlanError("DEPENDENCY_CYCLE")
        for task_id in ready:
            ordered.append(by_task[task_id])
            completed.add(task_id)
            pending.remove(task_id)

    planned: list[PlannedTask] = []
    for item in ordered:
        eligible = [
            agent for agent in roster
            if set(item.required_capabilities) <= set(agent.capabilities)
            and item.effect_class in agent.allowed_effects
        ]
        if not eligible:
            raise PlanError("NO_ELIGIBLE_AGENT:" + item.task_id)
        # Stable selection makes identical inputs produce identical plans.
        chosen = sorted(eligible, key=lambda agent: agent.agent_id)[0]
        planned.append(PlannedTask(
            task_id=item.task_id,
            agent_id=chosen.agent_id,
            depends_on=tuple(item.depends_on),
            effect_class=item.effect_class,
        ))

    events: list[dict[str, object]] = []
    previous_hash = "0" * 64
    for sequence, task in enumerate(planned, start=1):
        body: dict[str, object] = {
            "sequence": sequence,
            "event_type": "TASK_PLANNED",
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "depends_on": list(task.depends_on),
            "effect_class": task.effect_class,
            "previous_hash": previous_hash,
        }
        event_hash = _hash(body)
        event = {**body, "event_hash": event_hash}
        events.append(event)
        previous_hash = event_hash

    plan_body = {
        "schema_version": "1.0.0",
        "mode": "PLAN_ONLY",
        "tasks": [
            {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "depends_on": list(task.depends_on),
                "effect_class": task.effect_class,
            }
            for task in planned
        ],
        "events": events,
    }
    return PlanReceipt(
        schema_version="1.0.0",
        mode="PLAN_ONLY",
        tasks=tuple(planned),
        events=tuple(events),
        plan_hash=_hash(plan_body),
    )
