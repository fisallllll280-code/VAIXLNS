"""Small deterministic in-memory scheduler; persistence is intentionally external."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

class TaskState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"

@dataclass
class Task:
    capability: str
    payload: dict[str, Any]
    task_id: str = field(default_factory=lambda: str(uuid4()))
    state: TaskState = TaskState.QUEUED
    result: dict[str, Any] | None = None
    error: str | None = None

class TaskScheduler:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def submit(self, capability: str, payload: dict[str, Any]) -> Task:
        if not capability.strip():
            raise ValueError("capability is required")
        task = Task(capability=capability, payload=dict(payload))
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def snapshot(self) -> list[dict[str, Any]]:
        return [{"task_id": t.task_id, "capability": t.capability, "state": t.state.value,
                 "error": t.error} for t in self._tasks.values()]
