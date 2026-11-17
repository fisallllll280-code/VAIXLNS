"""Fail-closed registry for explicitly registered worker capabilities."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any

Worker = Callable[[dict[str, Any]], dict[str, Any]]

@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    capabilities: frozenset[str]
    handler: Worker
    enabled: bool = True
    max_attempts: int = 1

class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentProfile] = {}

    def register(self, profile: AgentProfile) -> None:
        if not profile.agent_id.strip():
            raise ValueError("agent_id is required")
        if profile.agent_id in self._agents:
            raise ValueError(f"duplicate agent_id: {profile.agent_id}")
        if not profile.capabilities:
            raise ValueError("at least one capability is required")
        if profile.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self._agents[profile.agent_id] = profile

    def resolve(self, capability: str) -> AgentProfile:
        matches = [a for a in self._agents.values() if a.enabled and capability in a.capabilities]
        if len(matches) != 1:
            raise LookupError(f"expected exactly one enabled worker for capability {capability!r}; found {len(matches)}")
        return matches[0]

    def snapshot(self) -> list[dict[str, Any]]:
        return [{"agent_id": a.agent_id, "capabilities": sorted(a.capabilities), "enabled": a.enabled,
                 "max_attempts": a.max_attempts} for a in sorted(self._agents.values(), key=lambda x: x.agent_id)]
