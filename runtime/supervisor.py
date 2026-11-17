"""Governed worker supervisor: explicit capability routing, bounded retries, fail-closed."""
from __future__ import annotations
from typing import Any
from .agent_registry import AgentRegistry
from .task_scheduler import TaskScheduler, TaskState, Task

class Supervisor:
    def __init__(self, registry: AgentRegistry, scheduler: TaskScheduler | None = None, *, require_approval: bool = True) -> None:
        self.registry = registry
        self.scheduler = scheduler or TaskScheduler()
        self.require_approval = require_approval

    def dispatch(self, capability: str, payload: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        task = self.scheduler.submit(capability, payload)
        if self.require_approval and not approved:
            task.state = TaskState.BLOCKED
            task.error = "human approval required before worker execution"
            return self._receipt(task)
        try:
            agent = self.registry.resolve(capability)
        except LookupError as exc:
            task.state = TaskState.BLOCKED
            task.error = str(exc)
            return self._receipt(task)
        task.state = TaskState.RUNNING
        last_error: Exception | None = None
        for _ in range(agent.max_attempts):
            try:
                result = agent.handler(dict(task.payload))
                if not isinstance(result, dict):
                    raise TypeError("worker handler must return a dict")
                task.result = result
                task.state = TaskState.SUCCEEDED
                task.error = None
                return self._receipt(task)
            except Exception as exc:  # bounded retries; error is recorded, not hidden
                last_error = exc
        task.state = TaskState.FAILED
        task.error = f"{type(last_error).__name__}: {last_error}" if last_error else "worker failed"
        return self._receipt(task)

    @staticmethod
    def _receipt(task: Task) -> dict[str, Any]:
        return {"task_id": task.task_id, "capability": task.capability, "state": task.state.value,
                "result": task.result, "error": task.error}
