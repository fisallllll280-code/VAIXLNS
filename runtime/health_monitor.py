"""Runtime health snapshots without claiming external service liveness."""
from __future__ import annotations
from typing import Any
from .agent_registry import AgentRegistry
from .task_scheduler import TaskScheduler, TaskState

class HealthMonitor:
    def snapshot(self, registry: AgentRegistry, scheduler: TaskScheduler) -> dict[str, Any]:
        agents = registry.snapshot()
        tasks = scheduler.snapshot()
        return {"status": "DEGRADED" if any(t["state"] == TaskState.FAILED.value for t in tasks) else "LOCAL_READY",
                "health_scope": "local_metadata_only", "registered_agents": len(agents),
                "enabled_agents": sum(1 for a in agents if a["enabled"]),
                "tasks_total": len(tasks),
                "tasks_by_state": {state.value: sum(1 for t in tasks if t["state"] == state.value) for state in TaskState}}
