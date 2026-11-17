"""Fail-closed supervisor for bounded VAIXLNS agent work."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

ALLOWED_OPERATIONS = frozenset({"OBSERVE", "RESEARCH", "PROPOSE"})
DENIED_OPERATIONS = frozenset({
    "BRANCH_MUTATE", "CANONICAL_WRITE", "RELEASE_DEPLOY",
    "PRODUCTION_MUTATE", "IRREVERSIBLE_OR_PHYSICAL",
})


class AgentAdapter(Protocol):
    def execute(self, task: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class RuntimePolicy:
    max_tasks: int = 8
    max_input_bytes: int = 64_000
    require_evidence_refs: bool = True

    def __post_init__(self) -> None:
        if self.max_tasks < 1 or self.max_input_bytes < 1:
            raise ValueError("RUNTIME_BUDGET_MUST_BE_POSITIVE")


class RuntimeHold(RuntimeError):
    """Raised when a task fails the runtime admission boundary."""


class RuntimeSupervisor:
    """Dispatch bounded tasks without granting extra authority."""

    def __init__(self, adapters: Mapping[str, AgentAdapter] | None = None,
                 policy: RuntimePolicy = RuntimePolicy()) -> None:
        self._adapters = dict(adapters or {})
        self._policy = policy
        self._dispatch_count = 0

    @property
    def dispatch_count(self) -> int:
        return self._dispatch_count

    def dispatch(self, task: Mapping[str, Any]) -> dict[str, Any]:
        self._validate(task)
        if self._dispatch_count >= self._policy.max_tasks:
            raise RuntimeHold("TASK_BUDGET_EXCEEDED")
        adapter_id = str(task["adapter_id"])
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            raise RuntimeHold("ADAPTER_NOT_CONFIGURED_HOLD")
        self._dispatch_count += 1
        result = adapter.execute(dict(task))
        if not isinstance(result, Mapping):
            raise RuntimeHold("ADAPTER_RESULT_MUST_BE_MAPPING")
        return {
            "task_id": task["task_id"],
            "agent_id": task["agent_id"],
            "status": "PROPOSED",
            "evidence_refs": list(task.get("evidence_refs", [])),
            "result": dict(result),
            "canonical_write": False,
            "promotion": "NOT_PERMITTED",
            "adapter_id": adapter_id,
        }

    def _validate(self, task: Mapping[str, Any]) -> None:
        required = ("task_id", "agent_id", "adapter_id", "operation", "input")
        if any(not str(task.get(key, "")).strip() for key in required):
            raise RuntimeHold("REQUIRED_TASK_FIELD_MISSING")
        operation = str(task["operation"]).upper()
        if operation in DENIED_OPERATIONS:
            raise RuntimeHold("OPERATION_DENIED")
        if operation not in ALLOWED_OPERATIONS:
            raise RuntimeHold("UNKNOWN_OPERATION_HOLD")
        if task.get("may_promote") is True or task.get("canonical_write") is True:
            raise RuntimeHold("AGENT_AUTHORITY_ESCALATION_DENIED")
        evidence = task.get("evidence_refs", [])
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence):
            raise RuntimeHold("EVIDENCE_REFS_MALFORMED")
        if self._policy.require_evidence_refs and operation != "OBSERVE" and not evidence:
            raise RuntimeHold("EVIDENCE_REQUIRED_HOLD")
        if len(repr(task["input"]).encode("utf-8")) > self._policy.max_input_bytes:
            raise RuntimeHold("INPUT_BUDGET_EXCEEDED")
