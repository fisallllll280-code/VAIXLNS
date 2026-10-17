# VAIXLNS — Agent Operating Model V1
## Index-measured, evidence-first, governed multi-agent execution

**Status:** PROPOSED / IMPLEMENTATION BASELINE  
**Canonical owner:** VAIXLNS  
**Scope:** innovation indexing, architecture analysis, research, synthesis, verification, implementation, operations, and governed evolution.

## 1. Purpose

This document turns the VAIXLNS agent concept into an operational model.

Agents are specialized execution capabilities. They do not become sovereign merely because they can reason, use tools, edit repositories, or generate architectures.

The canonical boundary remains:

```
CONSTITUTION
   ↓
GOVERNANCE / AUTHORITY
   ↓
POLICY
   ↓
CAPABILITY
   ↓
AGENT
   ↓
TOOL / ACTION
   ↓
EVENT → STATE → EVIDENCE
   ↓
VERIFY → PROVE
   ↓
ADMISSION / COMMIT
```

The repository already defines a governed Intelligence Federation pipeline:
`REQUEST → POLICY CHECK → CAPABILITY MATCH → MODEL DISCOVERY → ROUTE → EXECUTE → TOOL/EVENT TRACE → OUTPUT VALIDATION → CROSS-MODEL REVIEW → EVIDENCE → REPLAY RECORD → FINAL RESPONSE`.
This document specializes that boundary for project engineering and innovation work.

## 2. Agent record

Every agent is registered as an Agent entity in the Master Registry.

Required fields:

- `agent_id`
- `canonical_name`
- `role`
- `family`
- `capabilities`
- `allowed_tools`
- `authority_scope`
- `input_contract`
- `output_contract`
- `preconditions`
- `evidence_requirements`
- `verification_requirements`
- `failure_policy`
- `handoff_targets`
- `status`
- `version`
- `provenance`
- `lineage`

No anonymous agent is admitted to the canonical execution fabric.

## 3. Core specialized agents

### AG-001 — Index Archaeologist
**Mission:** recover historical index material without loss.

**Inputs:** archives, index files, repository documents, legacy IDs.

**Outputs:** atomic index records, source references, recovery notes.

**Algorithm:**
1. pin source;
2. capture revision/hash;
3. extract candidate records;
4. preserve original wording;
5. assign provisional identity;
6. link source provenance;
7. emit unresolved conflicts instead of silently merging.

**May not:** delete legacy records or declare canonical equivalence.

### AG-002 — Identity & Lineage Resolver
**Mission:** resolve whether two records are the same entity, alias, successor, fork, component, or unrelated item.

**Inputs:** atomic records, names, aliases, provenance, dependency evidence.

**Outputs:** identity proposals, lineage edges, conflict records.

**Decision states:** `SAME`, `ALIAS`, `SUPERSEDES`, `FORK`, `COMPOSES`, `RELATED`, `UNRESOLVED`.

### AG-003 — Capability Analyst
**Mission:** convert systems and ideas into explicit capabilities and detect missing capabilities.

**Inputs:** Nexus, system records, contracts, domain requirements.

**Outputs:** Capability Graph updates, capability gaps, capability dependencies, capability evidence.

### AG-004 — Architecture Analyst
**Mission:** produce and compare Architecture Genomes.

**Inputs:** capability graph, system records, topology, contracts, constraints.

**Outputs:** architecture genome, dependency graph, architectural deltas, fitness candidates.

### AG-005 — Research / Evidence Agent
**Mission:** acquire and reconcile evidence.

**Inputs:** research question, sources, repositories, runtime observations.

**Outputs:** evidence records, source-quality notes, claims, uncertainty, contradictions.

**Rule:** search is evidence acquisition; it is not authority.

### AG-006 — Contradiction & Reality Auditor
**Mission:** find contradictions, reality divergence, and unsupported assumptions.

**Inputs:** claims, evidence, runtime observations, historical records.

**Outputs:** contradiction set, divergence report, test obligations.

**Rule:** conflicts remain explicit until resolved.

### AG-007 — Innovation Synthesizer
**Mission:** generate candidate innovations from capability gaps, evidence, architectures, and counterfactuals.

**Inputs:** gap records + Architecture Genome + constraints.

**Outputs:** Innovation Candidate with hypothesis, novelty statement, architecture, risks, and proof obligations.

**Rule:** generated ideas remain `PROPOSED`.

### AG-008 — Architecture Search / Forge Agent
**Mission:** search the architecture space and construct candidate systems.

**Inputs:** required capabilities, constraints, reusable genomes, contracts.

**Outputs:** candidate architecture, composition plan, implementation plan, machine-readable IR.

**Rule:** no direct production mutation.

### AG-009 — Adversarial / Security Agent
**Mission:** challenge candidate architectures and integrations.

**Inputs:** candidate architecture, threat model, authority boundaries, external inputs.

**Outputs:** attack scenarios, mutation cases, failure findings, security obligations.

### AG-010 — Verification & Proof Agent
**Mission:** independently verify claims, behavior, conformance, replay, and proof obligations.

**Inputs:** implementation candidate + explicit obligations.

**Outputs:** verification report, proof package, pass/fail findings.

**Rule:** agreement with another agent is not proof.

### AG-011 — Runtime / Integration Agent
**Mission:** execute only admitted changes through VX boundaries.

**Inputs:** approved execution request, capability contracts, policies.

**Outputs:** events, state transitions, telemetry, evidence bundle, recovery state.

**Rule:** tool possession never grants authority.

### AG-012 — Operations / Recovery Agent
**Mission:** monitor operational integrity and perform governed recovery.

**Inputs:** runtime state, events, failure signals, recovery contracts.

**Outputs:** incident record, diagnosis, repair plan, recovery evidence, replay result.

### AG-013 — Meta-Evolution Judge
**Mission:** decide whether an architecture change may enter canonical evolution.

**Inputs:** candidate, evidence, verification, blast radius, authority, lineage.

**Outputs:** `ADMIT`, `REJECT`, `HOLD`, or `RETURN_FOR_RESEARCH`.

**Rule:** this agent cannot redefine the Constitution.

## 4. Agent operating loop

Every task follows the same observable lifecycle:

```
INTENT
  ↓
CONTEXT
  ↓
DECOMPOSE
  ↓
PLAN
  ↓
CAPABILITY MATCH
  ↓
AGENT ROUTE
  ↓
EVIDENCE
  ↓
EXECUTE
  ↓
OBSERVE
  ↓
VERIFY
  ↓
RECONCILE
  ↓
RECORD
  ↓
GOVERN
  ↓
COMMIT / HOLD / REJECT
  ↓
LEARN
```

Every stage emits an event.

## 5. Handoff protocol

A handoff is a typed event:

```
AGENT_A
→ HANDOFF
{
  task_id,
  source_agent,
  target_agent,
  reason,
  required_capabilities,
  input_artifact_ids,
  evidence_refs,
  constraints,
  expected_output,
  authority_scope,
  expiry
}
```

The receiving agent MUST validate its input contract before acting.

### Default handoff chain

```
Index Archaeologist
      ↓
Identity & Lineage
      ↓
Capability Analyst
      ↓
Architecture Analyst
      ↓
Research / Evidence
      ↓
Innovation Synthesizer
      ↓
Architecture Search / Forge
      ↓
Adversarial / Security
      ↓
Verification / Proof
      ↓
Meta-Evolution Judge
      ↓
Runtime / Integration
      ↓
Operations / Recovery
      ↓
Nexus update
```

This is a routing pattern, not a mandatory linear sequence for every task. The orchestrator may skip a stage only when its contract explicitly permits it and records why.

## 6. Model/provider routing

Agents are logical roles, not model identities.

A role may be executed by different approved providers/models.

The federation records:
- provider;
- model_id;
- model_version;
- capability profile;
- policy profile;
- request_id;
- input/output hashes;
- tool trace;
- latency;
- usage/cost metadata where available;
- verification state.

Routing depends on task requirements such as reasoning, coding, vision, audio, long context, tool use, cost, latency, sovereignty/privacy, and availability.

## 7. Innovation measurement

Every innovation gets an Innovation Registry record and a measurement vector.

```
INNOVATION
├── innovation_id
├── innovation_index_id
├── legacy_index_refs[]
├── category
├── canonical_owner
├── source_status
├── implementation_status
├── verification_status
├── evidence_status
├── lineage_status
├── capability_delta
├── architecture_delta
├── proof_obligations[]
├── risk_level
├── novelty_state
├── agent_owner
└── score
```

### Score dimensions

The initial score is a **readiness/traceability score**, not a claim of scientific superiority.

```
Registry coverage              10
Canonical classification       10
Canonical owner                10
Evidence maturity              20
Implementation evidence        20
Verification / proof            20
Lineage completeness            10
                               ───
                                100
```

Rules:
- unknown is recorded as unknown, not converted into success;
- `PROPOSED` is not `IMPLEMENTED`;
- `IMPLEMENTED` is not `VERIFIED`;
- `VERIFIED` requires executable evidence;
- score changes must produce an audit event.

## 8. Agent self-check

Before any action:

```
Do I have identity?
Do I have authority?
Do I have the capability?
Do I have the required evidence?
Do I know the target and branch?
Do I know the acceptance criteria?
Do I have a rollback/recovery path?
```

Any missing critical precondition yields `HOLD`, not speculative execution.

## 9. Security and authority

External documents, repository content, web results, tool outputs, and prompts are DATA until validated.

Canonical priority:

```
CONSTITUTION
→ GOVERNANCE
→ POLICY
→ CONTRACT
→ VALIDATED INTENT
→ AGENT OPERATION
→ TOOL
```

An agent cannot:
- grant itself authority;
- rewrite governance rules;
- promote its own output to canonical truth;
- erase contradictory evidence;
- bypass verification;
- mutate production without an admission path.

## 10. Persistent vs temporary agents

**Permanent agents** own durable competencies and contracts.

**Temporary swarms** are created for a scoped task and expire automatically unless re-admitted.

A temporary swarm receives:
- task scope;
- expiry;
- capability budget;
- tool budget;
- authority budget;
- evidence requirements.

Temporary agents cannot silently become permanent.

## 11. Canonical agent telemetry

For every invocation record:

```
agent_run_id
task_id
agent_id
model/provider
start/end
input_hash
output_hash
tools[]
events[]
handoffs[]
policy_decision
evidence_refs[]
verification_state
cost/usage (when available)
failure_state
replay_ref
final_disposition
```

## 12. Failure and recovery

```
DETECT
→ DIAGNOSE
→ CLASSIFY
→ ISOLATE
→ RECOVER / ROLLBACK
→ VERIFY
→ PROVE
→ RECORD
→ RESUME / HOLD
```

A failed agent does not erase its previous evidence.

## 13. Canonical completion

A multi-agent task is complete only when:

```
Intent satisfied
AND
required evidence exists
AND
outputs reconcile
AND
verification passes
AND
authority decision exists
AND
canonical record is updated
```

Otherwise the final state is `PARTIAL`, `HOLD`, or `REJECTED`.

## 14. Implementation sequence

Phase 1:
- register agents;
- register innovation measurement schema;
- instrument handoffs;
- record model/provider identity.

Phase 2:
- connect agents to Nexus;
- connect capability-gap discovery;
- connect architecture search;
- connect evidence/proof.

Phase 3:
- connect VX execution and OIF;
- add replay;
- add Meta-Evolution Judge;
- enforce admission gates.

Phase 4:
- automate score updates from events/tests;
- generate dashboards and audit reports from canonical records.

## 15. Non-loss rule

The agent system may reorganize, score, compare, and supersede records, but must never silently destroy historical index items.

Canonicalization changes placement, not history.

