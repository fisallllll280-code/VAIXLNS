# VAIXLNS Agent Orchestration Kernel V1
## Kernel contract for specialist agents, evidence, authority, and governed evolution

**Status:** Design + implementation contract for the next executable slice
**Parent:** VAIXLNS / VCRE multidomain synthesis
**Scope:** Agent task orchestration and result admission; no claim that remote agents are currently running.

## 1. The key architectural decision

Agents are not a collection of prompts. They are bounded workers in an evidence-producing, authority-constrained control system.

An agent can propose, inspect, implement within an assigned workspace, test, or challenge a candidate. It cannot grant itself capabilities, certify its own consequential work, alter constitutional policy, bypass a failed gate, or promote its own output into production.

The kernel separates five independent questions:
1. **Identity:** Which registered principal emitted this result?
2. **Capability:** Is that principal permitted and technically able to perform this task?
3. **Authority:** Does the task grant authorize this action on this resource, revision, and time window?
4. **Evidence:** Which reproducible artifacts support the result?
5. **Admission:** Which independent policy decision permits the next state transition?

A valid identity is not proof of competence; competence is not authority; authority is not evidence; evidence does not automatically imply admission.

## 2. Immutable task envelope

Each dispatched task carries a schema version, task/run/candidate IDs, candidate fingerprint, source revision, role and registered principal, capability contract, input artifact references, output contract, proof obligations, resource budgets, permitted tools, authority-grant reference, issue/expiry times, idempotency key, and fail-closed policy.

Runtime must validate actual IDs, clock bounds, schema, grant state, candidate fingerprint, and artifact existence. No secret values belong in the envelope; use scoped secret handles issued by a secret manager.

## 3. Specialist roles and separation of duties

| Role | Produces | Cannot do alone |
|---|---|---|
| ARCHITECT | Candidate graph, interface contracts, dependency and blast-radius map | Approve own architecture |
| MATHEMATICAL_FORMALIST | Equations, assumptions, proof obligations, counterexamples | Claim proof without proof artifact |
| COMPUTATIONAL_SCIENTIST | Algorithm choice, convergence/error analysis, resource profile | Equate convergence with model truth |
| PHYSICS_SPECIALIST | Units, invariants, validity domain, validation proposal | Infer experimental validity from simulation alone |
| IMPLEMENTER | Candidate-branch patch, build/test receipts | Merge or deploy own consequential patch |
| INTEGRATION_ENGINEER | Adapter, schema, failure-mode evidence | Widen permission scope silently |
| ADVERSARIAL_REVIEWER | Threat model, fault injection, negative tests | Suppress or rewrite audit records |
| INDEPENDENT_VERIFIER | Independent replay and discrepancy report | Rely only on producer's uninspected conclusion |
| EVOLUTION_JUDGE | ADMIT / HOLD / REJECT recommendation | Grant authority beyond own scope |
| MEMORY_CURATOR | Source-linked summaries, failure cases, reusable patterns | Rewrite source evidence or erase lineage |

Roles are profiles mapped to registered agent identities and capabilities. A role name does not create a principal, runtime, tool connection, or permission.

## 4. Dispatch state machine

PROPOSED → CONTRACT_VALIDATED → IDENTITY_BOUND → CAPABILITY_CHECKED → AUTHORITY_GRANTED → DISPATCHED → RESULT_QUARANTINED → OUTPUT_CONTRACT_VALIDATED → EVIDENCE_RECORDED → INDEPENDENTLY_CHECKED → ADMISSION_DECIDED → CLOSED

Any invalid or missing mandatory condition transitions to HOLD or REJECTED. Timeouts, malformed output, identity mismatch, expired grants, candidate revision drift, duplicate non-idempotent actions, and missing evidence must not be converted to success.

The result is quarantined first. The agent's own success flag is not a trusted completion receipt.

## 5. Scheduling as constrained optimization

Choose tasks to maximize expected evidence value while respecting precedence, resource budgets, independence, and authority:

max over S: sum(i in S) [evidence_value_i - lambda_r * resource_cost_i - lambda_u * uncertainty_i]

Subject to dependency ordering, concurrency and budget limits, serialization of shared mutable state, distinct producer/verifier principals for consequential work, and explicit task-scoped tool and authority grants.

These scores are scheduling heuristics, not safety proofs. Hard constraints are checked separately and cannot be compensated by utility. Use bounded queues, per-principal quotas, cancellation propagation, backpressure, and fairness.

## 6. Evidence graph and provenance

Represent work as a DAG of immutable artifacts and decisions. Edges include derived_from, tested_by, reviewed_by, supersedes, and admitted_by.

Each evidence record binds artifact digest and media type; producing principal and task; candidate fingerprint and source revision; tool/runtime identity and version; environment/dependency-lock digest; invocation parameters and seed policy; timestamps; exit status and measured values; tolerances and limitations; verifier identity/verdict; and counterevidence.

A digest gives integrity linkage, not truth. A log line is not automatically an evidence artifact.

## 7. Independent verification

For consequential work, producer and verifier must be distinct registered principals. The verifier receives the candidate and raw evidence, not merely the producer's narrative. Verification checks revision/fingerprint, obligations against artifacts, independent replay, residuals/tolerances, baseline discrepancies, threat model, and rollback evidence.

If independent replay is impossible, record the limitation and route to HOLD or a separately authorized alternate assurance procedure. Producer-only tests must not be relabeled independent verification.

## 8. Failure and recovery

- Retry only classified transient failures when repeating the operation is safe.
- Use idempotency keys for retried dispatches and external effects.
- Use bounded exponential backoff with jitter at runtime; do not retry authorization denials as network errors.
- Quarantine suspicious outputs and preserve evidence.
- Revoke or expire grants when a task is cancelled, times out, or changes scope.
- Roll back candidate state to an immutable known-good revision when a guardrail fails.
- Convert reproducible failures into regression fixtures without erasing the original record.

## 9. Typed agent memory

Store SOURCE_FACT, HYPOTHESIS, TEST_RESULT, VERIFIED_CLAIM, DECISION, FAILURE_CASE, and REUSABLE_PATTERN as distinct record types. Each record needs provenance, version, timestamps, confidence basis, supersession links, retention policy, and access scope.

Never promote a hypothesis to fact solely because several agents repeat it. Correlated model outputs are not independent corroboration.

## 10. Self-improvement without self-authorization

Detect a measured gap; recover the immutable baseline; propose candidate changes in an isolated branch; declare expected benefit/risk/budget/rollback; run targeted and impact-appropriate regression tests; conduct adversarial tests and independent verification; compare evidence against baseline; request a separate admission decision; stage rollout with guardrails and rollback; record outcomes.

Agents may propose changes in an authorized sandbox but cannot change the policy that grants that authority or self-approve the result. Policy changes require a separate governed path and explicit approval.

## 11. Security invariants

- Least privilege and deny-by-default tool access.
- Bind principal identity to dispatch and result receipts.
- No ambient credentials in prompts, logs, or artifacts.
- Treat tool output as untrusted input; parse and validate it.
- Source prompt injection cannot change the task authority contract.
- Pin tool/dependency versions for reproducible consequential runs.
- Record policy/schema version with every admission.
- Separate read, write, merge, deploy, financial, and physical-actuation capabilities.
- Expired or revoked grants fail closed.
- Bound agent count and recursion depth to prevent runaway orchestration.

## 12. Acceptance tests for first runtime slice

- Expired authority grant is denied.
- Identity/capability mismatch is denied.
- Output is quarantined before schema validation.
- Producer cannot verify its own consequential task.
- Candidate fingerprint drift invalidates stale evidence.
- Timeouts and cancellation revoke scoped grants.
- Idempotent retry does not duplicate side effects.
- Unknown hard constraints lead to HOLD.
- Prompt injection cannot widen privileges.
- Every admission points to immutable evidence.
- Failed guardrails trigger a tested rollback path.
- Scheduler obeys queue, concurrency, recursion, and resource budgets.

## 13. Explicit implementation boundary

This document defines the next kernel contract. It does not assert that a distributed agent runtime, cryptographic identity service, authority service, evidence store, or autonomous scheduler has already been deployed. Those require code, integration tests, and observed runtime receipts before being reported as operational.
## 14. Executable reference slice

The repository now includes:
- `vcre/agent_orchestration.py`: task-envelope validation, scoped authority-grant checks, registered-principal/capability checks, explicit task-state transitions, deterministic result quarantine fingerprints, evidence provenance checks, stale candidate/source-revision rejection, independent-verifier separation, and explicit admission-decision handling.
- `tests/test_agent_orchestration.py`: tests for expiry, identity/capability mismatch, quarantine ordering, evidence drift, producer/verifier separation, HOLD behavior, successful gated closure, timezone requirements, and illegal state transitions.
- `schemas/agent-task-envelope.schema.json`: JSON Schema for the bounded task envelope.

This is an executable reference kernel, not a distributed agent service. The runtime still needs to bind real authenticated principals, retrieve grants from the authority service, persist immutable evidence, and dispatch work to configured agent providers. Passing unit tests must not be reported as proof that those external services are live.