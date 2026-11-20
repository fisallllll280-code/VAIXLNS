# VAIXLNS — Agent Identity / Workflow Stage Binding Contract V1

**Status:** PROPOSED / ENGINEERING CONTRACT  
**Authority:** `project.genome::v1.0.0` · `Ω0_GENESIS_CORE` · `Ω.000`  
**Scope:** bind persistent agent-role identities to workflow-stage contracts without merging their identity namespaces or transferring authority.  
**Compatibility:** extends `agents/agent_fabric.py`, `registry/agent_registry.v1.json`, `docs/agents/AGENT_FABRIC_V1.md`, and the VX admission boundary. It does not replace them.

## 1. Problem statement

The repository currently represents two distinct concepts:

- Persistent role identities in `registry/agent_registry.v1.json`: `AG-001` through `AG-013`.
- Workflow-stage roles in `agents/agent_fabric.py`: `AG-00-ORCHESTRATOR` through `AG-12-GOVERNANCE-REVIEW`.

The sets both contain thirteen records, but the identifiers and decomposition are different. Equal cardinality is not evidence of identity equivalence. A silent one-to-one mapping would therefore be unsafe and could create incorrect capability, tool, or authority assignments.

## 2. Four distinct entities

| Entity | Meaning | Authoritative source |
|---|---|---|
| `AgentRoleIdentity` | Stable registered role identity, owner, family and declared capability profile | `registry/agent_registry.v1.json` |
| `WorkflowStage` | A bounded step in a versioned task pipeline, with input/output artifact contracts | Agent Fabric stage definition |
| `RuntimePrincipal` | An actually provisioned execution identity, such as a provider-backed worker or VX executor | Runtime/provider admission registry (must be evidenced) |
| `AuthorityGrant` | Time-bounded permission for a principal to perform specific effects on scoped resources | Governance/VX authorization record |

These entities MUST NOT be conflated. A role is not a running model. A stage is not an identity. A model endpoint is not a permission grant. A permission grant is not evidence that a task succeeded.

## 3. Binding record

An `AgentStageBinding` is a versioned relationship between one persistent role identity and one workflow stage. It records compatibility; it does not create authority.

Required fields:

- `binding_id`, `binding_version`, `status`, and timestamps;
- `agent_entity_id` and `workflow_stage_id`, preserved in their original namespaces;
- source role/stage versions and provenance references;
- required and provided capability references;
- accepted input and emitted output artifact types/contracts;
- allowed tool names as a declared allowlist (not credentials);
- `runtime_principal_ref` only when an actual admitted runtime principal exists;
- `authority_profile_ref` and optional `execution_grant_ref` as references, never embedded bearer credentials;
- declared effects, policy reference, effective window, reviewer and disposition.

Suggested lifecycle states: `PROPOSED`, `UNDER_REVIEW`, `ACTIVE`, `SUSPENDED`, `EXPIRED`, `REVOKED`, `SUPERSEDED`, `QUARANTINED`, `REJECTED`.

## 4. Non-negotiable invariants

1. **Namespace preservation:** never rewrite an `AG-001` identity as an `AG-00` stage or vice versa.
2. **No inferred crosswalk:** only explicit, reviewed binding records may connect a role and a stage.
3. **Capability compatibility:** the role's registered capabilities must satisfy the stage's declared requirements; partial overlap is not sufficient unless the stage contract explicitly allows it.
4. **Artifact compatibility:** the role's output contract must satisfy the next stage's input contract. Unknown schemas or versions fail closed.
5. **No authority transfer:** a binding cannot grant new tool permissions, external side effects, repository writes, production deployment, or canonical promotion.
6. **VX mediation:** effectful actions require a distinct runtime principal and a current, scoped, expiring grant checked by the VX policy/admission gate.
7. **Provider truth:** a model/provider field is accepted only with deployment and health evidence. A role registry record alone does not prove a live model endpoint.
8. **Append-only history:** binding revisions, suspensions, revocations and corrections are new events; prior records are not silently overwritten.
9. **Independent verification:** the producer cannot self-verify high-impact changes or self-promote the binding.
10. **Unknown is not pass:** absent mappings, missing contract versions, stale evidence or unresolved conflicts produce `HOLD` or `QUARANTINE`.

## 5. Binding resolution algorithm

1. Validate the binding against `schemas/agent-identity-stage-binding.v1.schema.json`.
2. Resolve `agent_entity_id` against the pinned agent registry version.
3. Resolve `workflow_stage_id` against the pinned Agent Fabric version.
4. Verify both source revisions, owner, lifecycle status and lineage.
5. Compare declared role capabilities with stage requirements.
6. Check input/output artifact contract compatibility and tool allowlist intersection.
7. If the task has side effects, separately validate runtime principal, VX grant, scope, expiry, policy and idempotency key.
8. Emit a `BindingResolutionReceipt` with PASS / HOLD / REJECT / QUARANTINE, reasons, source references, evaluator version and evidence digests.
9. Require authorized governance admission before marking a binding ACTIVE.

Resolution result is a compatibility assessment, not an authorization token.

## 6. Failure semantics

| Condition | Disposition |
|---|---|
| Unknown role or stage | `HOLD_UNKNOWN_REFERENCE` |
| Duplicate active binding for a conflicting scope | `QUARANTINE_BINDING_CONFLICT` |
| Capability requirement not met | `REJECT_CAPABILITY_MISMATCH` |
| Input/output contract mismatch | `REJECT_CONTRACT_MISMATCH` |
| Stale or missing source revision | `HOLD_STALE_PROVENANCE` |
| Missing runtime principal for an effectful task | `HOLD_RUNTIME_NOT_ADMITTED` |
| Missing, expired, revoked or out-of-scope VX grant | `REJECT_AUTHORITY_GRANT` |
| Provider/model health not evidenced | `HOLD_PROVIDER_UNVERIFIED` |
| Attempted self-promotion or authority expansion | `REJECT_AUTHORITY_ESCALATION` |

## 7. Required conformance tests

1. Every role and stage ID is preserved exactly and resolves in its own registry.
2. Unknown or ambiguous identifiers never receive an inferred mapping.
3. Duplicate binding IDs and conflicting active bindings are rejected or quarantined.
4. Capability and artifact contract mismatch prevents activation.
5. Tool allowlists are intersected; bindings cannot add tools absent from the registered policy.
6. A binding without a runtime principal can be used for planning/research only, not side-effect execution.
7. An expired, revoked, mismatched or out-of-scope VX grant is rejected.
8. Provider/model identity without deployment-health evidence remains unverified.
9. Binding state cannot transition to ACTIVE without a governance decision reference.
10. State transitions append records and preserve superseded/revoked history.
11. Deterministic resolution on the same pinned sources and policy produces the same decision semantics.
12. Receipt contains binding ID/version, source revisions, evaluator/policy version, evidence references and unresolved gaps.

## 8. Phased adoption

### Phase A — Read-only reconciliation
- Inventory both existing role sets without renaming them.
- Extract input/output and capability contracts from each definition.
- Produce candidate mappings and explicit `UNRESOLVED` entries.
- Human/authorized reviewer approves or rejects each mapping.

### Phase B — Registry/schema integration
- Add the binding schema and versioned registry.
- Add a deterministic resolver and `BindingResolutionReceipt`.
- Add unit and property tests for all failure semantics above.
- Keep all new bindings `PROPOSED` until review.

### Phase C — Runtime admission
- Connect only admitted runtime principals.
- Require VX authorization for all effects.
- Emit trace, event, evidence, replay and revocation records.
- Verify live health and policy conformance before each admission window.

## 9. Explicit non-goals

- This contract does not map the thirteen existing identities to the thirteen stages.
- It does not create or deploy new agents, models, APIs or servers.
- It does not grant agents repository write access or production authority.
- It does not promote any innovation or alter the canonical master index.
- It does not claim tests have passed; the conformance list is a proposed acceptance suite.

**Current disposition: PROPOSED / HOLD_FOR_REVIEW.**