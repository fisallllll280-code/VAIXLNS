# VAIXLNS Discovery Routing Contract V1

**Status:** PROPOSED — canonical adoption pending governance review  
**Canonical owner:** VAIXLNS  
**Scope:** research discoveries routed to financial and engineering VX workstreams under family-level authority  
**Compatibility:** extends the existing agent operating model and NEXENT boundary; does not replace either.

## 1. Purpose

Every research discovery MUST become a traceable record and be routed to the correct workstream(s) according to the governing parent directive, affected family relationships, evidence quality, capability requirements, and authority constraints.

A route is not an approval to execute. Discovery, classification, routing, verification, admission, and execution are distinct states.

## 2. Authority boundary

The governing order is:

~~~text
CONSTITUTION / CANONICAL GOVERNANCE
  -> PARENT DIRECTIVE (policy and family priorities)
  -> DISCOVERY ROUTER (classification and destination proposal)
  -> VX WORKSTREAM (financial and/or engineering)
  -> EVIDENCE / SECURITY / LICENSE / CONTRACT CHECKS
  -> ADMISSION GATE
  -> AUTHORIZED EXECUTION
  -> EVENT / STATE / LEDGER / REPLAY RECORD
~~~

- The “parent” is a policy authority, not an unrestricted agent.
- A research agent may recommend a destination but may not grant itself authority.
- The router applies approved policies; it cannot rewrite them.
- VX workstreams may analyze and propose changes within their registered capability and authority scope.
- Only the designated governance/admission boundary can authorize canonical adoption or consequential execution.
- Unknown or conflicting parent/family mappings remain unresolved and MUST NOT be guessed.

## 3. Destination model

Destinations below are logical workstreams. Their existence as separate deployed runtime instances must be verified independently.

### VX-FINANCIAL
Handles financial analysis such as cost, resource demand, operational expense, budget fit, revenue hypotheses, economic feasibility, and financial risk.

### VX-ENGINEERING
Handles algorithms, architecture, source repositories, implementation plans, prototypes, dependency graphs, tests, reliability, security remediation, and technical feasibility.

### Multi-route discoveries
A discovery can route to both workstreams. The canonical record is stored once; each route references the same discovery ID and records its own status, output, and evidence. Neither route may overwrite the other's findings.

### Other or unclear domains
Send the record to PARENT_REVIEW / CLASSIFICATION_HOLD until an authorized policy resolves its family and destination. Do not force an unknown discovery into a financial or engineering category.

## 4. Required discovery record

Every discovery record MUST include:

- discovery_id: stable unique identifier
- created_at and record_version
- origin_agent_id and research_task_id
- objective and discovery_summary
- source_refs[], source revision/date, and content hashes where available
- claims[], evidence references, uncertainty, and contradictions
- candidate_families[] and affected_systems[]
- parent_directive_id and the policy version used
- classification with rationale
- routes[] with destination, priority rationale, required capabilities, status, and assigned agent/workstream
- security_status, license_status, and privacy_status
- dependency_refs[], related_discovery_refs[], and lineage
- verification_status, proof obligations, and verification evidence
- execution_authorization (default false)
- decision_record_ref and audit/event references

Do not store secrets, credentials, or unnecessary personal data in discovery records.

## 5. Routing algorithm

1. **Capture:** preserve the discovery and its source provenance before interpretation.
2. **Deduplicate carefully:** compute a stable fingerprint where practical; link possible duplicates without merging distinct records automatically.
3. **Check authority:** resolve the applicable parent directive and policy version. If absent, expired, or contradictory, hold for review.
4. **Resolve family:** use registered canonical identities, aliases, dependencies, and lineage. Mark unverified identity mappings as unresolved.
5. **Classify:** identify financial and engineering relevance separately. One discovery may have multiple destinations.
6. **Score priority:** apply the approved policy to impact, urgency, evidence quality, dependency criticality, cost, risk, and family priorities. Store score inputs and rationale; never emit a score without its policy/version.
7. **Check capability:** route only to workstreams with registered capabilities and permitted tools.
8. **Create handoffs:** send typed, expiring handoff events with input IDs, evidence refs, constraints, expected output, and authority scope.
9. **Verify:** require independent checks proportional to risk; model agreement alone is not proof.
10. **Admit or hold:** execution remains disabled until all required gates pass and explicit authorization is recorded.
11. **Record and replay:** record route decisions, state transitions, tool events, outputs, evidence, and final disposition.
12. **Re-evaluate:** re-route when source evidence, policy, family mappings, dependencies, or risk materially changes.

## 6. Route statuses

Allowed route states:

- RECEIVED
- CLASSIFICATION_PENDING
- ROUTED
- IN_PROGRESS
- WAITING_FOR_EVIDENCE
- CONFLICT_HOLD
- SECURITY_HOLD
- LICENSE_HOLD
- PARENT_REVIEW
- VERIFIED
- ADMISSION_PENDING
- ADMITTED
- REJECTED
- SUPERSEDED
- CLOSED

A state transition must record actor, time, reason, input/output references, and policy version. VERIFIED does not imply ADMITTED; ADMITTED does not imply successful execution.

## 7. Priority policy

Priority is policy-derived, not hard-coded as an unexplained number. A versioned scoring policy may consider:

- strategic fit to the parent directive;
- affected family criticality;
- evidence quality and independent corroboration;
- urgency and time sensitivity;
- capability/dependency unblock value;
- expected engineering benefit;
- expected financial impact and cost;
- security, legal, operational, and reversibility risk.

Risk and authority are gates, not merely score penalties. A high score cannot bypass a failed safety, license, evidence, or authorization gate. Missing values must be marked unknown rather than silently treated as zero.

## 8. Conflict and failure rules

- Conflicting directives -> CONFLICT_HOLD and escalation to the governing authority.
- Unknown family or unverified identity -> CLASSIFICATION_PENDING or PARENT_REVIEW.
- Missing or weak evidence -> WAITING_FOR_EVIDENCE.
- Unsafe artifact or suspected malicious code -> SECURITY_HOLD; do not execute it to “see what happens.”
- Unclear license or redistribution rights -> LICENSE_HOLD.
- Missing capability or tool permission -> hold or route to an authorized capable workstream.
- Router timeout or partial failure -> retain the discovery and event log; retry idempotently using the same discovery/route IDs.
- Duplicate delivery -> do not create duplicate side effects; use idempotency keys.
- Parent directive changes -> record a new decision; do not erase the prior decision.

## 9. Minimal record example

~~~yaml
discovery_id: "disc-<stable-id>"
origin_agent_id: "AG-005"
record_version: 1
parent_directive_id: "directive-<registered-id>"
classification:
  status: "PROVISIONAL"
  candidate_families: []
  rationale: "Evidence-linked explanation required"
routes:
  - destination: "VX-ENGINEERING"
    status: "CLASSIFICATION_PENDING"
    priority_policy: "<policy-id>@<version>"
    required_capabilities: []
  - destination: "VX-FINANCIAL"
    status: "CLASSIFICATION_PENDING"
    priority_policy: "<policy-id>@<version>"
    required_capabilities: []
evidence:
  source_refs: []
  claims: []
  contradictions: []
  verification_status: "UNVERIFIED"
security_status: "PENDING"
license_status: "PENDING"
execution_authorization: false
lineage:
  related_discovery_refs: []
decision_record_ref: null
~~~

This is a template, not a valid production record until IDs and schema constraints are supplied.

## 10. Conformance tests required before implementation claims

1. Every accepted discovery has a stable ID, source provenance, and decision record.
2. Unknown parent directive causes a hold, never an implicit default route.
3. An engineering-only discovery is not sent to the financial route unless policy says it has financial relevance.
4. A financial discovery with engineering dependencies can create linked routes without duplicating the canonical record.
5. Conflicting family policies cannot be resolved by the research agent.
6. Low evidence quality cannot be marked verified solely because several models agree.
7. No route can set execution_authorization=true without the designated admission authority.
8. A security/license hold blocks execution.
9. Retries are idempotent and preserve event lineage.
10. Replay with identical inputs and policy version reproduces the same route decision or explicitly explains nondeterministic inputs.
11. Every score includes its policy version, component values, and rationale.
12. Changes to policies or family mappings create new decision records rather than rewriting history.

## 11. Implementation boundary and status

This document defines a contract only. It does not prove that the router, financial/engineering workstreams, family registry links, schemas, or tests are implemented or running.

Implementation should proceed in this order:
1. inspect the canonical registry and existing VX contracts;
2. define the discovery-record and route-event schemas;
3. implement a deterministic policy-driven router;
4. add tests for holds, multi-route cases, conflicts, and idempotency;
5. connect evidence and admission gates;
6. validate runtime event/state/ledger/replay integration;
7. submit for governance review before canonical adoption.
