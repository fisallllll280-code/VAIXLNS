"""Canonical, capability-bounded research and engineering agent roster.

This registry defines roles and handoff contracts, not running model instances.
Runtime adapters must supply the implementation and prove its health separately.
No agent in the roster may self-authorize canonical changes or directly promote a
candidate. Admission remains an external governance decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    role: str
    mission: str
    capabilities: tuple[str, ...]
    accepts: tuple[str, ...]
    emits: tuple[str, ...]
    authority_scope: tuple[str, ...] = ("read:assigned-evidence",)
    may_execute: bool = False
    may_promote: bool = False

    def __post_init__(self) -> None:
        if not self.agent_id.strip() or not self.role.strip() or not self.mission.strip():
            raise ValueError("AGENT_ID_ROLE_AND_MISSION_REQUIRED")
        if not self.capabilities or not self.accepts or not self.emits:
            raise ValueError("AGENT_CAPABILITIES_AND_HANDOFF_CONTRACTS_REQUIRED")
        if self.may_promote:
            raise ValueError("AGENT_SELF_PROMOTION_IS_FORBIDDEN")


DEFAULT_HANDOFF_CHAIN = (
    "AG-00-ORCHESTRATOR",
    "AG-01-SOURCE-DISCOVERY",
    "AG-02-ARCHIVE-RECOVERY",
    "AG-03-CLAIM-ATOMIZER",
    "AG-04-NOVELTY-LINEAGE",
    "AG-05-COUNTEREVIDENCE",
    "AG-06-ARCHITECTURE-SYNTHESIS",
    "AG-07-ENGINEERING-CONTRACT",
    "AG-08-IMPLEMENTATION-PLANNER",
    "AG-09-SECURITY-ADVERSARY",
    "AG-10-TEST-VERIFICATION",
    "AG-11-PROOF-INTEGRITY",
    "AG-12-GOVERNANCE-REVIEW",
)


DEFAULT_AGENTS = (
    AgentDefinition(
        "AG-00-ORCHESTRATOR", "RESEARCH_ORCHESTRATOR",
        "Decompose the mission, assign bounded lanes, and reconcile reports.",
        ("mission_decomposition", "task_routing", "coverage_tracking"),
        ("mission_request",), ("mission_packet",),
        ("read:assigned-evidence", "route:approved-agents"),
    ),
    AgentDefinition(
        "AG-01-SOURCE-DISCOVERY", "SOURCE_DISCOVERY",
        "Search connected providers and report source coverage, revisions, and failures.",
        ("github_search", "web_search", "repository_search", "source_coverage"),
        ("mission_packet",), ("source_corpus",),
        ("read:search", "read:public-repositories"),
    ),
    AgentDefinition(
        "AG-02-ARCHIVE-RECOVERY", "ARCHIVE_RECOVERY",
        "Recover historical terms and map legacy identifiers without inventing missing rows.",
        ("archive_retrieval", "legacy_id_mapping", "source_hashing"),
        ("source_corpus",), ("recovered_corpus",),
        ("read:project-archives",),
    ),
    AgentDefinition(
        "AG-03-CLAIM-ATOMIZER", "CLAIM_EVIDENCE_ATOMIZATION",
        "Convert source statements into claim-level records with traceable excerpts.",
        ("claim_extraction", "provenance_linking", "uncertainty_labeling"),
        ("recovered_corpus",), ("claim_evidence_graph",),
        ("read:source-corpus",),
    ),
    AgentDefinition(
        "AG-04-NOVELTY-LINEAGE", "NOVELTY_AND_LINEAGE",
        "Compare candidates with existing innovations, aliases, families, and supersession links.",
        ("duplicate_screening", "lineage_resolution", "semantic_overlap_review"),
        ("claim_evidence_graph",), ("lineage_report",),
        ("read:innovation-registry",),
    ),
    AgentDefinition(
        "AG-05-COUNTEREVIDENCE", "ADVERSARIAL_RESEARCH",
        "Seek counterexamples, contrary evidence, alternative explanations, and known failure cases.",
        ("counterevidence_search", "contradiction_detection", "falsification_planning"),
        ("lineage_report",), ("counterevidence_report",),
        ("read:source-corpus", "read:test-results"),
    ),
    AgentDefinition(
        "AG-06-ARCHITECTURE-SYNTHESIS", "COUNTERFACTUAL_ARCHITECTURE",
        "Compose competing architectures and state trade-offs without selecting by model preference alone.",
        ("architecture_synthesis", "counterfactual_design", "dependency_mapping"),
        ("counterevidence_report",), ("candidate_architectures",),
        ("read:research-bundle",),
    ),
    AgentDefinition(
        "AG-07-ENGINEERING-CONTRACT", "ENGINEERING_CONTRACT",
        "Translate the selected candidate into explicit interfaces, invariants, state, and failure contracts.",
        ("contract_design", "schema_design", "invariant_definition"),
        ("candidate_architectures",), ("engineering_contract",),
        ("read:architecture-candidates",),
    ),
    AgentDefinition(
        "AG-08-IMPLEMENTATION-PLANNER", "IMPLEMENTATION_PLANNING",
        "Create a bounded implementation plan with dependencies, rollback, and acceptance criteria.",
        ("implementation_planning", "dependency_ordering", "rollback_design"),
        ("engineering_contract",), ("implementation_plan",),
        ("read:engineering-contract",),
    ),
    AgentDefinition(
        "AG-09-SECURITY-ADVERSARY", "SECURITY_AND_FAILURE_ANALYSIS",
        "Challenge authority boundaries, attack surfaces, resource limits, recovery and blast radius.",
        ("security_review", "failure_injection_design", "authority_boundary_review"),
        ("implementation_plan",), ("threat_report",),
        ("read:implementation-plan",),
    ),
    AgentDefinition(
        "AG-10-TEST-VERIFICATION", "TEST_AND_REPLAY_VERIFICATION",
        "Turn contracts and failure hypotheses into deterministic tests, replay cases, and expected outputs.",
        ("test_generation", "replay_design", "acceptance_evaluation"),
        ("threat_report",), ("test_and_replay_evidence",),
        ("read:contracts", "request:sandbox-test"),
    ),
    AgentDefinition(
        "AG-11-PROOF-INTEGRITY", "PROVENANCE_AND_PROOF_INTEGRITY",
        "Check evidence identity, freshness, source lineage, verifier independence, and proof completeness.",
        ("digest_verification", "proof_package_review", "evidence_freshness"),
        ("test_and_replay_evidence",), ("evidence_package",),
        ("read:test-evidence", "read:provenance"),
    ),
    AgentDefinition(
        "AG-12-GOVERNANCE-REVIEW", "GOVERNANCE_RECOMMENDATION",
        "Summarize gate results and unresolved risks for the authorized decision-maker.",
        ("gate_summary", "readiness_recommendation", "decision_record_drafting"),
        ("evidence_package",), ("admission_recommendation",),
        ("read:decision-package", "recommend:admission"),
    ),
)


class AgentRegistry:
    """Deterministic in-memory registry for role identity and allowed handoffs."""

    def __init__(self, agents: Iterable[AgentDefinition] = DEFAULT_AGENTS) -> None:
        items = tuple(agents)
        by_id: dict[str, AgentDefinition] = {}
        for agent in items:
            if agent.agent_id in by_id:
                raise ValueError(f"DUPLICATE_AGENT_ID:{agent.agent_id}")
            by_id[agent.agent_id] = agent
        self._order = tuple(agent.agent_id for agent in items)
        self._agents = by_id

    def all(self) -> tuple[AgentDefinition, ...]:
        return tuple(self._agents[agent_id] for agent_id in self._order)

    def get(self, agent_id: str) -> AgentDefinition:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"UNKNOWN_AGENT_ID:{agent_id}") from exc

    def by_capability(self, capability: str) -> tuple[AgentDefinition, ...]:
        return tuple(agent for agent in self.all() if capability in agent.capabilities)

    def validate_handoff_chain(self, chain: tuple[str, ...] = DEFAULT_HANDOFF_CHAIN) -> tuple[str, ...]:
        errors: list[str] = []
        if not chain:
            return ("HANDOFF_CHAIN_EMPTY",)
        if len(chain) != len(set(chain)):
            errors.append("HANDOFF_CHAIN_CONTAINS_DUPLICATE_AGENT")
        for agent_id in chain:
            if agent_id not in self._agents:
                errors.append(f"HANDOFF_UNKNOWN_AGENT:{agent_id}")
        for source_id, target_id in zip(chain, chain[1:]):
            source = self._agents.get(source_id)
            target = self._agents.get(target_id)
            if source is None or target is None:
                continue
            if not set(source.emits).intersection(target.accepts):
                errors.append(f"HANDOFF_CONTRACT_MISMATCH:{source_id}->{target_id}")
        return tuple(errors)


__all__ = ["AgentDefinition", "AgentRegistry", "DEFAULT_AGENTS", "DEFAULT_HANDOFF_CHAIN"]
