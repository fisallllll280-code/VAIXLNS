"""Canonical agent registry adapter for the governed mind federation.

The registry file is the source of truth. This module provides a small typed
read-only view; it does not grant tool permissions or execute agents.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "registry" / "agent_registry.v1.json"
)

# Explicitly ordered hand-off path: evidence and verification precede governed
# runtime operations, and the meta-evolution judge closes the review cycle.
DEFAULT_HANDOFF_CHAIN: tuple[str, ...] = tuple(
    f"AG-{number:03d}" for number in range(1, 14)
)


@dataclass(frozen=True)
class Agent:
    agent_id: str
    canonical_name: str
    family: str
    capabilities: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    authority_scope: str
    primary_output: str
    hard_rule: str

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "Agent":
        required = (
            "agent_id",
            "canonical_name",
            "family",
            "capabilities",
            "allowed_tools",
            "authority_scope",
            "primary_output",
            "hard_rule",
        )
        missing = [key for key in required if key not in record]
        if missing:
            raise ValueError("agent_record_missing:" + ",".join(missing))
        for key in ("agent_id", "canonical_name", "family", "authority_scope", "primary_output", "hard_rule"):
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError(f"agent_record_invalid:{key}")
        for key in ("capabilities", "allowed_tools"):
            value = record[key]
            if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
                raise ValueError(f"agent_record_invalid:{key}")
        return cls(
            agent_id=record["agent_id"],
            canonical_name=record["canonical_name"],
            family=record["family"],
            capabilities=tuple(record["capabilities"]),
            allowed_tools=tuple(record["allowed_tools"]),
            authority_scope=record["authority_scope"],
            primary_output=record["primary_output"],
            hard_rule=record["hard_rule"],
        )


class AgentRegistry:
    """Load and validate the canonical agent registry without mutating it."""

    def __init__(self, registry_path: str | Path | None = None) -> None:
        self.path = Path(registry_path) if registry_path is not None else DEFAULT_REGISTRY_PATH
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"agent_registry_unreadable:{self.path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"agent_registry_invalid_json:{self.path}") from exc

        if not isinstance(document, dict) or not isinstance(document.get("agents"), list):
            raise ValueError("agent_registry_invalid_shape")
        records = document["agents"]
        self._agents = tuple(
            Agent.from_record(record) if isinstance(record, dict)
            else (_ for _ in ()).throw(ValueError("agent_record_must_be_object"))
            for record in records
        )
        ids = [agent.agent_id for agent in self._agents]
        if len(ids) != len(set(ids)):
            raise ValueError("agent_registry_duplicate_id")
        if not self._agents:
            raise ValueError("agent_registry_empty")

        known = set(ids)
        unknown = [agent_id for agent_id in DEFAULT_HANDOFF_CHAIN if agent_id not in known]
        if unknown:
            raise ValueError("default_handoff_chain_unknown_agents:" + ",".join(unknown))

    def all(self) -> tuple[Agent, ...]:
        """Return agents in canonical registry order."""
        return self._agents

    def get(self, agent_id: str) -> Agent:
        """Return one agent or raise KeyError for an unknown identifier."""
        for agent in self._agents:
            if agent.agent_id == agent_id:
                return agent
        raise KeyError(agent_id)
