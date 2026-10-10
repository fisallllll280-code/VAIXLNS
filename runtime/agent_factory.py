"""Constrained manifest-only agent factory; never generates executable code."""
from dataclasses import dataclass
from runtime.supervised_runtime import AgentManifest, digest

@dataclass(frozen=True)
class FactoryArtifact:
    manifest: AgentManifest
    artifact_hash: str
    validation_status: str = "MANIFEST_SCHEMA_VALIDATED"
    deployment_status: str = "BLOCKED_PENDING_VALIDATION_AND_HUMAN_APPROVAL"

class AgentFactory:
    def create_manifest(self, *, agent_id, version, creator_id, requested_capabilities, creator_ceiling):
        capabilities = tuple(sorted(set(requested_capabilities)))
        if not capabilities: raise ValueError("CAPABILITY_REQUIRED")
        if not set(capabilities).issubset(creator_ceiling): raise PermissionError("FACTORY_AUTHORITY_ESCALATION_DENIED")
        manifest = AgentManifest(agent_id, version, creator_id, capabilities, 0)
        return FactoryArtifact(manifest, digest(manifest.__dict__))
    @staticmethod
    def deployment_decision(artifact, *, supplied_hash, validation_status, approved_by):
        if supplied_hash != artifact.artifact_hash: return "REJECTED_HASH_MISMATCH"
        if validation_status != "ISOLATED_TESTS_PASSED": return "BLOCKED_VALIDATION_NOT_PASSED"
        if not isinstance(approved_by, str) or not approved_by.strip(): return "BLOCKED_HUMAN_APPROVAL_REQUIRED"
        return "ELIGIBLE_FOR_SEPARATE_DEPLOYMENT_GATE"
