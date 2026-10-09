"""Typed adapter for the canonical VAIXLNS agent registry.

The registry JSON remains the source of truth. This module validates and exposes
agent definitions; it does not start agent processes or grant runtime authority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "registry" / "agent_registry.v1.json"

# This sequence describes a governed handoff path. It is a routing proposal,
# not an automatic execution grant; the governance judge precedes runtime work.
DEFAULT_HANDOFF_CHAIN = (
    "AG-001",  # index archaeology
    "AG-002",  # identity and lineage
    "AG-003",  # capability analysis
    "AG-004",  # architecture
    "AG-005",  # research and source evidence
    "AG-006",  # contradiction and reality audit
    "AG-007",  # innovation synthesis
    "AG-008",  # architecture forge
    "AG-009",  # adversarial security
    "AG-010",  # proof and verification
    "AG-013",  # governance/admission judgment
    "AG-011",  # gated runtime/integration
    "AG-012",  # operations and recovery
)


class AgentRegistryError(ValueError):
    """Raised when the canonical registry is invalid."""


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    canonical_name: str
    family: str
    capabilities: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    authority_scope: str
    primary_output: str
    hard_rule: str
    lifecycle: tuple[str, ...] = ()
    handoff_format: tuple[str, ...] = ()


class AgentRegistry:
    """Read-only typed adapter over registry/agent_registry.v1.json."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else REGISTRY_PATH
        self._agents = self._load()

    def _load(self) -> tuple[AgentDefinition, ...]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AgentRegistryError(f"cannot load agent registry {self.path}: {exc}") from exc
        if not isinstance(document, dict) or not isinstance(document.get("agents"), list):
            raise AgentRegistryError("agent_registry_must_contain_agents_array")

        agents: list[AgentDefinition] = []
        seen: set[str] = set()
        for row in document["agents"]:
            if not isinstance(row, dict):
                raise AgentRegistryError("agent_entry_must_be_object")
            agent_id = row.get("agent_id")
            name = row.get("canonical_name")
            if not isinstance(agent_id, str) or not agent_id.strip():
                raise AgentRegistryError("agent_id_required")
            if agent_id in seen:
                raise AgentRegistryError(f"duplicate_agent_id:{agent_id}")
            if not isinstance(name, str) or not name.strip():
                raise AgentRegistryError(f"canonical_name_required:{agent_id}")
            seen.add(agent_id)
            agents.append(AgentDefinition(
                agent_id=agent_id,
                canonical_name=name,
                family=str(row.get("family", "UNCLASSIFIED")),
                capabilities=tuple(_string_list(row.get("capabilities", []), agent_id, "capabilities")),
                allowed_tools=tuple(_string_list(row.get("allowed_tools", []), agent_id, "allowed_tools")),
                authority_scope=str(row.get("authority_scope", "UNSET")),
                primary_output=str(row.get("primary_output", "UNSET")),
                hard_rule=str(row.get("hard_rule", "UNSET")),
                lifecycle=tuple(_string_list(row.get("lifecycle", []), agent_id, "lifecycle")),
                handoff_format=tuple(_string_list(row.get("handoff_format", []), agent_id, "handoff_format")),
            ))
        if not agents:
            raise AgentRegistryError("agent_registry_empty")
        return tuple(agents)

    def all(self) -> tuple[AgentDefinition, ...]:
        """Return all registered definitions in canonical file order."""
        return self._agents

    def get(self, agent_id: str) -> AgentDefinition:
        """Resolve an exact case-insensitive agent ID."""
        key = agent_id.strip().casefold()
        for agent in self._agents:
            if agent.agent_id.casefold() == key:
                return agent
        raise KeyError(f"unknown_agent_id:{agent_id}")

    def capable_of(
        self,
        required: Iterable[str],
        *,
        authority_scopes: Iterable[str] = (),
    ) -> tuple[AgentDefinition, ...]:
        """Return registry definitions whose declared capabilities cover all requirements.

        This is metadata filtering only; it does not authenticate a caller or authorize
        a runtime action. Authority enforcement remains a separate gate.
        """
        needed = {item.strip().casefold() for item in required if item.strip()}
        scopes = {item.strip().casefold() for item in authority_scopes if item.strip()}
        return tuple(
            agent for agent in self._agents
            if needed.issubset({item.casefold() for item in agent.capabilities})
            and (not scopes or agent.authority_scope.casefold() in scopes)
        )


def _string_list(value: object, agent_id: str, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AgentRegistryError(f"invalid_{field_name}:{agent_id}")
    return value
