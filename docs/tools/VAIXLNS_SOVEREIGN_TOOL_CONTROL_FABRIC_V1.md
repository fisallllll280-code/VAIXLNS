# VAIXLNS Sovereign Tool Control Fabric (STCF) V1

**Status:** PROPOSED — canonical review and runtime admission required  
**Canonical owner:** VAIXLNS  
**Discovery and synthesis:** NEXENT  
**Execution enforcement:** VX  
**Identity, relationships and lineage:** Canonical Nexus / Ω.000  
**Evidence and assurance:** ARC-X Ω / Ω-RAC where implemented  
**Operational history:** Event / State / Ledger / Replay / OIF contracts  
**Rule:** This document and its schemas do not establish runtime enforcement by themselves.

## 1. Decision

Create one versioned control contract for every consequential tool invocation, whether the tool is a model, API, shell, repository client, browser, database, build runner, server, connector, robot, cloud action or internal capability.

STCF does not replace the Universal External Integration Gate, the Agent/Skill Delivery Fabric, the VX Federation Gate, ARC-X, or the Finality Gate. It joins their decisions at the point of action so that no adapter, agent, prompt, or workflow creates a side door around canonical policy.

The control objective is not to maximize what tools can do. It is to let the authorized owner set the maximum permitted action, scope, budget and risk, then make each invocation demonstrate that it remains inside those limits.

## 2. Non-negotiable invariants

1. **Authority is not inferred.** Identity, access, model quality, tool availability, capability, confidence, proof, and authority are distinct.
2. **No self-escalation.** An agent, tool, prompt, skill, provider, or generated artifact cannot raise its own ceiling, modify governing policy, approve itself, or grant another actor authority.
3. **Fail closed.** Unknown tool/identity/capability, missing scope, stale proof, conflicting policies, invalid signatures, expired approval or ambiguous impact yields HOLD, QUARANTINE or REJECT; never guessed permission.
4. **No implicit production.** Repository writes, merging, releases, deployment, public publication, payments/trades, destructive changes and physical actuation require their own explicitly scoped authorization. High-impact classes are denied by default.
5. **Budgets are hard limits.** Time, retries, tokens, network calls, write volume and cost limits are checked before and during execution. Exhaustion stops the run and records the stop; it does not silently request or grant a larger budget.
6. **Separate execution from verification.** The producer cannot be the only verifier of a claim that requires independent assurance. Passing tests does not grant authority.
7. **Approval binds to exact intent.** Approval is bound to a digest of the action, target scope, policy, implementation, dependencies, budget and validity interval. Any material change requires re-evaluation and, when required, new approval.
8. **Append-only history.** Allow, hold, deny, timeout, cancellation, rollback and recovery decisions preserve actor, target, policy version, reason and evidence references. Recovery never erases the incident.
9. **No automatic canonical promotion.** A discovered tool, capability or innovation can become a candidate; canonical adoption remains a separate governance decision.
10. **Stop beats progress.** Emergency stop, revoked identity, budget exhaustion, proof invalidation or violated invariant suspends the affected action path and prevents automatic resumption of privileged work.

## 3. Authority ceilings

These are proposed tiers for policy evaluation, not permissions automatically granted to any actor.

| Tier | Ceiling | Typical permitted effect | Default posture |
|---|---|---|---|
| A0 | OBSERVE | Read approved telemetry and artifacts | Allow only under identity, data and scope policy |
| A1 | RESEARCH | Search approved sources; retrieve scoped data | Allow only through configured adapters and egress rules |
| A2 | PROPOSE | Produce plans, patches and candidate artifacts in scratch space | Allow; no external side effect |
| A3 | SANDBOX_MUTATE | Change an isolated, disposable sandbox | Require isolation, resource budget and tests |
| A4 | BRANCH_MUTATE | Write to a named non-protected branch or workspace | Require target allowlist, diff capture and audit |
| A5 | RELEASE_PREPARE | Prepare release manifest, candidate package and rollback plan | Prepare only; cannot publish or deploy |
| A6 | RELEASE_DEPLOY | Deploy or cause approved external state change | Deny by default; require fresh proof and explicit release authority |
| A7 | IRREVERSIBLE_OR_PHYSICAL | Delete irrecoverable data, move funds, execute trades, make high-impact public/physical changes | Deny by default; separate policy, scope, just-in-time human approval and recovery/safety controls where feasible |

The effective authority is the **intersection**, never the union, of:
- actor/agent ceiling;
- registered tool capability;
- approved task scope;
- canonical policy;
- target environment ceiling;
- fresh evidence/proof requirements;
- valid explicit approvals;
- resource and time budgets.

Formally:

`EffectiveAuthority = RequestedScope ∩ ActorCeiling ∩ ToolCapability ∩ Policy ∩ EnvironmentCeiling ∩ ValidApproval`

If any required boundary is missing or inconsistent, the decision is not ALLOW.

## 4. Control surface — the operator's knobs

A future VAIXLNS Control Center should expose these controls through authenticated, audited policy changes:

- **Global operating mode:** READ_ONLY, ADVISORY, SANDBOX, BRANCH_WORK, RELEASE_PREPARATION, or explicitly authorized PRODUCTION.
- **Per-tool state:** ENABLED, DISABLED, QUARANTINED, EXPIRED, or NOT_CONFIGURED.
- **Authority ceiling:** set maximum tier by actor, agent role, tool, environment and domain.
- **Scope allowlist:** repositories, branches, paths, APIs, databases, cloud projects, devices and permitted data classes.
- **Budget envelope:** wall time, token use, retries, concurrency, network calls, write volume, compute and cost.
- **Approval thresholds:** require human review by action class, risk, blast radius, novelty, confidence/evidence gap or external side effect.
- **Execution controls:** dry-run/simulation requirement, sandbox profile, egress policy, idempotency, timeout, abort and rollback references.
- **Promotion controls:** separate candidate, verified, admitted, canonical, released and operationally-final states.
- **Emergency controls:** stop new actions, cancel supported in-flight work, revoke a tool/identity/policy binding, quarantine a capability and require re-admission.
- **Audit controls:** inspect action envelope, policy decision, resource consumption, diff, events, proof freshness, approval and replay.

Changing a policy is itself a governed action: it requires a versioned change proposal, impact analysis, independent checks and authorized approval. Agents can recommend a policy change but cannot commit it.

## 5. Mandatory action envelope and decision

Every tool invocation must carry a validated action envelope using `schemas/vx-tool-action-envelope.v1.schema.json`. The policy evaluator returns a separate decision record using `schemas/vx-tool-policy-decision.v1.schema.json`.

Minimum binding chain:

`Intent → Actor Identity → Tool Identity/Version → Capability → Target Scope → Policy Version → Authority → Budget → Preconditions → Approval (if required) → Execution → Events/State → Evidence → Independent Verification → Commit/Finality`

The request envelope must include stable task/action IDs, idempotency key, expiration, input digest/reference, exact target scope, requested operation, actor ceiling, tool/adapter identity and digest, policy identity/version/digest, bounded budget, risk class, required checks, proof references and approval requirements.

The decision record must include ALLOW/HOLD/QUARANTINE/REJECT, deterministic reason codes, the effective ceiling, gate outcomes, the policy digest, expiry and any granted budget. A decision is not a proof of successful execution; the execution receipt and verification report are separate artifacts.

## 6. Single decision pipeline

```text
REQUEST
  ↓
SCHEMA + SIGNATURE + EXPIRY CHECK
  ↓
ACTOR / TOOL / VERSION IDENTITY
  ↓
CAPABILITY + CONTRACT CHECK
  ↓
TARGET / DATA / NETWORK SCOPE
  ↓
POLICY + AUTHORITY INTERSECTION
  ↓
PROOF FRESHNESS + DEPENDENCY / IMPACT CHECK
  ↓
RISK + RESOURCE BUDGET + IDEMPOTENCY
  ↓
DRY-RUN / SANDBOX / REQUIRED HUMAN APPROVAL
  ↓
DECISION: ALLOW | HOLD | QUARANTINE | REJECT
  ↓
BOUNDED EXECUTION
  ↓
EVENT + STATE + LEDGER + EVIDENCE
  ↓
INDEPENDENT VERIFICATION + REPLAY (where applicable)
  ↓
AUTHORIZED COMMIT / ADMISSION / FINALITY
  ↓
MONITOR → REVALIDATE → REVOKE OR RECOVER
```

No caller may skip a gate because it is internal, trusted, fast, previously successful or initiated by a high-scoring agent.

## 7. Perpetual innovation without authority drift

“Perpetual” means a continuous, restartable learning and engineering loop — not unlimited recursion or autonomous permission to rewrite the canonical system.

```text
OBSERVE REALITY / FAILURES / RESEARCH
  ↓
FIND GAP OR CONTRADICTION
  ↓
CREATE SOURCE-LINKED INNOVATION CANDIDATE
  ↓
COMPARE AGAINST CANONICAL + HISTORICAL LINEAGE
  ↓
CLASSIFY: DUPLICATE / COMPLEMENT / CONFLICT / NOVEL / UNKNOWN
  ↓
SYNTHESIZE CANDIDATE DESIGNS
  ↓
SIMULATE + ESTIMATE IMPACT / COST / RISK
  ↓
SANDBOX PROTOTYPE + POSITIVE / NEGATIVE / ADVERSARIAL TESTS
  ↓
CAPTURE REPRODUCIBLE EVIDENCE
  ↓
INDEPENDENT VERIFICATION
  ↓
GOVERNANCE REVIEW / PR-BASED ADOPTION
  ↓
CONTROLLED ROLLOUT + MONITORING
  ↓
OUTCOME, REGRESSION OR FAILURE → LINEAGE / KNOWLEDGE / NEXT CANDIDATE
  └───────────────────────────────────────────────↺
```

Every innovation keeps its source, author/agent, assumptions, related candidates, rejected alternatives, artifact digests, test matrix, resource consumption, verification state, reviewer/approval and adoption outcome. A novel name alone is not novelty; the system must compare semantic function, contracts and lineage.

The loop must have finite per-run limits: maximum candidate count, recursion depth, parallel workers, wall time, compute/cost and retries. When a limit is reached, save a resumable checkpoint and stop. The next run may continue only under the current policy. Each iteration proposes evolution; it does not inherit authority from the previous iteration.

## 8. Failure and recovery semantics

- **HOLD:** a required fact, mapping, reviewer, approval or proof is missing; preserve the request and identify the exact obligation to resolve.
- **QUARANTINE:** tool identity, behavior, dependency or output may be unsafe or has drifted; deny consequential access and preserve evidence.
- **REJECT:** the request conflicts with an explicit policy, scope, or non-delegable boundary.
- **ABORT:** stop an admitted run when a runtime guard is breached; emit the event and make residual effects observable.
- **ROLLBACK/COMPENSATE:** execute only through a pre-authorized recovery contract. Rollback is not assumed possible for every action.
- **RE-ADMIT:** require fresh identity, contracts, tests, evidence, impact analysis and authority after material change.

A missing adapter, test runner or external provider produces NOT_CONFIGURED/HOLD. It must never be represented as a successful tool call.

## 9. Acceptance gates before runtime admission

The implementation is not ready until evidence demonstrates at least:

1. Valid envelopes parse; malformed, extra-field, expired and digest-mismatched envelopes fail closed.
2. Unknown tools, unknown capabilities and unknown targets do not execute.
3. A lower-tier actor cannot request or obtain a higher effective tier.
4. An agent cannot modify policy, approve its own change or promote its own output.
5. Approval expires and is invalidated when the approved target, payload digest, policy or material dependency changes.
6. Scope escape, disallowed egress and secret-exfiltration test cases are blocked and audited.
7. Budget exhaustion stops execution within a documented enforcement bound and produces a durable event.
8. Retries respect idempotency and cannot duplicate consequential effects.
9. Protected branch, release, deployment, payment/trading and physical-control operations remain denied without their separate authorization gates.
10. Event history links request, decision, execution receipt, resulting state, evidence and recovery; replay checks the applicable deterministic claims.
11. The verifier is independent for claims designated as requiring independence.
12. The operator can disable/quarantine a tool and stop new work; privileged resumption requires revalidation.
13. Candidate innovation cannot automatically become canonical, released or operationally-final.
14. Policy changes, approvals, denial reasons, resource use and finality decisions are traceable and reviewable.

Tests must include positive cases, negative cases, adversarial inputs, time-of-check/time-of-use changes, stale proof, revoked identity, partial failure and restart/replay.

## 10. Implementation ownership and rollout

| Boundary | Responsibility |
|---|---|
| VAIXLNS canonical hub | Approve policy vocabulary, schemas, authority model, lifecycle and adoption decision |
| Nexus / Ω.000 | Bind identities, contracts, capabilities, dependencies and lineage |
| NEXENT | Discover gaps and produce candidate architecture/innovation proposals; no execution authority |
| VX | Enforce the action gate, scoped adapters, budgets, sandboxing, execution receipt and stop behavior |
| ARC-X Ω / Ω-RAC | Check supported claims and assurance obligations; proof does not grant authority |
| Event / State / Ledger / Replay | Persist the decision and execution history; reconstruct and verify applicable state transitions |
| OIF / Finality Gate | Observe operational integrity, trigger revalidation, and prevent unproved readiness/finality claims |
| Control Center UI | Display and submit authorized policy changes; UI state itself is not the security boundary |

Suggested stages:
- **M0 — Contract:** schemas, policy profile and test vectors reviewed.
- **M1 — Observe-only:** inventory configured tools and record decisions without granting mutation.
- **M2 — Enforced deny/hold:** enforce identity, scope, authority and expiry checks for all tool calls.
- **M3 — Sandbox:** allow bounded mutations in isolated environments with evidence.
- **M4 — Branch workflow:** branch-only changes, automated tests, review and PR creation; no automatic merge.
- **M5 — Release preparation:** reproducible artifacts, security/supply-chain checks and rollback preparation.
- **M6 — Explicit production admission:** only after all applicable gates, fresh proof, independent review and separate authorization pass.
- **M7 — Continuous revalidation:** drift, incidents, policy changes, dependency changes and expired proofs trigger reassessment.

Each stage has its own evidence. Passing one stage does not imply admission to a later stage.

## 11. Status truth

At specification time:
- The repository already contains related contracts for external integration admission, agent/skill delivery, VX federation, innovation indexing and finality.
- This document proposes a unified action-time control contract and its machine-readable envelopes.
- No claim is made here that STCF runtime enforcement, a live control dashboard, every adapter, or perpetual autonomous operation has been implemented or verified.
- Canonical adoption, execution-repository implementation, integration tests and runtime admission remain separate gates.

## 12. Related canonical contracts

- `docs/integration/UNIVERSAL_EXTERNAL_INTEGRATION_GATE_V1.md`
- `docs/integration/VAIXLNS_AGENT_SKILL_SUBSCRIPTION_FABRIC_V1.md`
- `docs/integration/VX_AGENTS_FABRIC_CONTRACT_V1.md`
- `docs/architecture/VX_FEDERATION_GATE_V1.md`
- `docs/canonical/FINALITY_GATE_V1.md`
- `docs/cognitive/VX_OMEGA_COGNITIVE_FABRIC_V1.md`
- `docs/indexes/INNOVATION_MASTER_INDEX.md`
