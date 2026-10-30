# VX Sovereign Gateway — Threat Model, Assurance Plan & Admission Matrix V1

**Status:** PROPOSED / SPECIFIED — no runtime enforcement claim  
**Parent contract:** `docs/architecture/VX_UNIFIED_CONNECTOR_GATEWAY_V1.md` (PR #201)  
**Existing controls reused:** STCF V1, VX Federation Gate V1, Universal External Integration Gate V1, AEPF Ω, action-envelope schema, policy-decision schema, default tool-control policy, and `tools/vx_tool_control_reference.py`.  
**Authority:** VAIXLNS governance; VX execution; VLNS cross-system coordination; NEXENT discovery/design; ARC-X/AEPF evidence and assurance.  
**Protected assets:** `project.genome` and `Ω.000` are immutable for this work.

## 1. Decision and non-goals

Adopt a **federated sovereign control plane with distributed enforcement points**. The central plane publishes versioned policy and identity/capability contracts; each runtime, connector adapter, repository integration, data boundary and execution environment enforces the applicable policy locally. The central plane is not a universal secret holder or an unrestricted superuser.

This document is an additive threat-model and admission artifact. It does not create a second gateway, registry, ledger, policy engine, identity authority, or canonical index. It does not activate connectors, establish production readiness, or authorize external access.

Non-goals:
- No replacement for STCF, VX Federation Gate, AEPF, ARC-X, Event/State/Ledger/Replay, or the existing VX connector gateway contract.
- No assumption that every third-party model or application can be fully observed or controlled.
- No automatic policy promotion, canonical adoption, merge, deployment, payment, physical action, or irreversible mutation.
- No new credentials, network destinations, external spend, or production connections.

## 2. System boundary and trust assumptions

### 2.1 Protected assets
1. Canonical authority and governance policy.
2. `project.genome` and `Ω.000`.
3. Source repositories, protected branches, build artifacts and dependency locks.
4. Agent/model identities, capability grants, provider credentials and secret references.
5. Data, prompts, memory, indexes, backups and customer/regulated information.
6. Tool adapters, MCP servers, APIs, CI runners, runtime hosts and deployment targets.
7. Approval records, event history, evidence capsules, audit logs and recovery points.
8. Resource budgets, quotas, billing accounts and external side effects.

### 2.2 Trust zones
- **Z0 — Sovereign roots:** constitution, protected anchors, policy-signing authority and human approval identities.
- **Z1 — Governance/control:** policy distribution, asset/capability registries, admission decisions and approval workflow.
- **Z2 — VX execution:** orchestrator, action evaluator, dispatcher, runtime, ledger and adapter supervisors.
- **Z3 — Isolated adapters:** one adapter/process/container per trust boundary where feasible; narrow credentials and egress.
- **Z4 — External/untrusted:** model providers, MCP servers, SaaS, repositories outside the governed tenant, user-supplied artifacts and fetched content.
- **Z5 — Evidence/assurance:** append-only receipts, independent verification, replay and recovery evidence.

Trust is never inherited across zones. A successful call, reachable endpoint, model reputation, signed package, green CI status or previous approval is not a substitute for current scoped authorization.

### 2.3 Adversaries
- External attacker with no account.
- Compromised user, agent, model, connector, dependency or provider account.
- Malicious or compromised insider with legitimate access.
- Prompt-injection content author controlling repository files, web pages, tickets, documents or model context.
- Supply-chain attacker controlling package, image, action, model artifact or update channel.
- Accidental operator, policy author or automation error.
- Colluding or correlated agents that share faulty sources or assumptions.
- Failure/partition attacker exploiting stale state, retries, clocks, queues or partial writes.

## 3. Security objectives and invariants

1. **Least authority:** effective permissions are the intersection of actor ceiling, tool capability, task scope, environment ceiling, active policy, valid proof and exact approval.
2. **No self-escalation:** agents, models, tools and generated artifacts cannot grant themselves authority, change active policy, approve themselves or promote themselves.
3. **Fail closed:** unknown identity/tool/capability, missing scope, stale proof, invalid signature, conflicting policy, expired approval, unverifiable impact or unavailable enforcement returns HOLD, QUARANTINE or REJECT.
4. **No implicit trust:** internal, federated, previously successful or high-scoring callers receive no bypass.
5. **Exact-intent approval:** approval binds to action digest, target, revision, policy, dependencies, budget, environment and validity interval; material change invalidates it.
6. **Separation of duties:** proposer, executor, verifier and approver are distinct principals for high-impact actions. The same evidence producer cannot be the sole independent verifier.
7. **No secret concentration:** raw provider credentials remain in approved secret storage and are scoped per adapter; the control plane stores references and metadata only.
8. **Bounded execution:** wall time, retries, concurrency, tokens, network calls, output bytes, write volume and cost have hard ceilings.
9. **Durable accountability:** allow, hold, deny, quarantine, timeout, abort, rollback and recovery are recorded without secrets.
10. **Blast-radius containment:** failure or compromise of one adapter, model, agent, tenant or runtime must not grant lateral access to others.
11. **Freshness:** policy, identity, connector, dependency, approval and evidence have explicit versions/expiry/revocation semantics.
12. **Recoverability:** privileged operations require a tested recovery/compensation plan where technically possible; recovery never erases the incident.
13. **Epistemic honesty:** UNKNOWN, NOT_OBSERVED, INACCESSIBLE, CONFLICT, NOT_CONFIGURED and NOT_RUN remain distinct from PASS or MISSING.
14. **Protected-root integrity:** no change to `project.genome` or `Ω.000` under this work.

## 4. Threat register

| ID | Threat / failure mode | Impact | Required control | Required evidence |
|---|---|---|---|---|
| T01 | Gateway/control-plane compromise | Cross-system authority abuse | Distributed enforcement; no universal root token; offline policy cache with expiry and revocation semantics | Control-plane compromise exercise; local deny-path receipts |
| T02 | Stolen/forged actor identity | Unauthorized action | Strong authentication, short-lived identity assertions, revocation, audience binding | Invalid/revoked/expired identity tests |
| T03 | Agent privilege escalation | Unauthorized writes or external actions | Capability ceilings; intersection semantics; no self-grant | Cross-tier negative tests |
| T04 | Prompt/tool injection | Data exfiltration or tool misuse | Treat external content as data; structured tool calls; output validation; egress control | Injection corpus and blocked-action receipts |
| T05 | Connector impersonation or drift | Calls routed to malicious endpoint | Pinned connector identity, endpoint and adapter digest; re-admission on drift | Endpoint/adapter substitution tests |
| T06 | Secret theft or leakage | Account/provider compromise | Secret manager references, just-in-time retrieval, redaction, scoped credentials | Canary-secret scans of logs/results/artifacts |
| T07 | Cross-tenant or cross-agent data leakage | Confidentiality breach | Tenant/agent memory partitioning; explicit data-class and recipient policy | Isolation and cross-tenant negative tests |
| T08 | Supply-chain compromise | Malicious code/model execution | SBOM, provenance/attestation, pinned dependencies, image/model digest verification | Tampered dependency/artifact tests |
| T09 | Policy manipulation | Governance bypass | Signed, versioned policy; dual control; policy changes are governed actions | Unsigned/stale/self-authored policy tests |
| T10 | Approval replay or TOCTOU | Unauthorized changed action | Exact action digest, expiry, nonce/idempotency, re-check immediately before dispatch | Mutate target/payload after approval tests |
| T11 | Duplicate execution/retry storm | Duplicate side effects or cost | Atomic idempotency ledger, bounded retries, cancellation and circuit breaker | Concurrent duplicate and timeout tests |
| T12 | Evidence forgery/laundering | False VERIFIED claims | Independent evidence store, signed receipts, source pinning, counterevidence | Tampered/stale/fabricated receipt tests |
| T13 | Correlated agent error/collusion | False consensus | Independent source/method, conflict preservation, adversarial reviewer | Shared-source and contradictory-evidence tests |
| T14 | Unknown/shadow asset | Uncontrolled access path | Discovery inventory, egress observation, owner attestations, coverage limitations | Shadow endpoint and unregistered tool detection |
| T15 | Control-plane outage/partition | Unsafe fail-open or total outage | Local enforcement; bounded cached policy; sensitive actions stop on stale policy | Partition, stale-cache and recovery tests |
| T16 | Clock manipulation | Expiry/replay bypass | Trusted time source, monotonic elapsed-time checks, bounded skew | Clock rollback/skew tests |
| T17 | Ledger deletion/rollback | Loss of forensic history | Append-only or tamper-evident remote audit copy; sequence continuity | Truncation/reordering/deletion detection |
| T18 | Resource exhaustion / recursive agents | Cost and availability failure | Per-task and global budgets; recursion/concurrency caps; stop/checkpoint | Exhaustion and runaway-loop tests |
| T19 | Unsafe rollback/compensation | Further damage | Predefined compensating actions; recovery rehearsal; human gate for destructive restore | Partial-failure recovery drill |
| T20 | Regulatory/data-residency violation | Legal, contractual or privacy harm | Data classification, purpose/retention rules, processor/region register, legal applicability review | Data-flow inventory and compliance evidence |

Risk ratings must be assigned per asset and deployment context; this register does not claim that every threat has the same likelihood or impact.

## 5. Existing-asset reconciliation — do not duplicate

| Existing asset | Reuse responsibility | Gap before runtime admission |
|---|---|---|
| STCF V1 | Action envelope, authority tiers, policy/approval/budget invariants | Prove all call paths enforce it, not merely document it |
| VX Federation Gate V1 | Instance identity, capability routing, isolation | Runtime membership, heartbeat/lease, revocation and route receipts |
| Universal External Integration Gate V1 | Discover → quarantine → test → verify → admit | Evidence-backed connector inventory and actual adapter enforcement |
| VX Universal Agent Runtime | Agent profiles, task DAG, tool-call boundary | Active profile binding and no direct-tool bypass tests |
| AEPF Ω | Claims, proof obligations, counterevidence, falsifiers | Independent, commit-bound evidence capsule implementation |
| Action-envelope / policy-decision schemas | Typed request and decision contracts | Runtime schema validation, canonicalization and signature verification |
| Default tool-control policy | Fail-closed baseline, hard limits, approval rules | Policy currently declares PROPOSED_NOT_ADMITTED / CONTRACT_ONLY_NOT_CONNECTED; admission is a separate gate |
| `tools/vx_tool_control_reference.py` | Reference decision evaluator | File explicitly states it does not authenticate signatures, validate schemas, write durable ledger, provide atomic idempotency or gate real adapters |
| VX-runtime | Execution core, event ledger, policy-before-capability and replay contracts | Reconcile the real adapter/identity/ledger path; do not infer gateway integration from core existence |
| Ω.000 / Nexus | Canonical identities, relationships and lineage | Protected; consume existing read interfaces only, no parallel registry |

**Critical distinction:** the reference evaluator is not a production security boundary. Before any runtime claim, the missing controls explicitly identified in its module contract must be implemented and independently tested: trusted registry loading, schema validation, authentication/signature verification, atomic idempotency, durable event/ledger writes and an adapter gate. Also test concurrency, revocation races, policy freshness, cancellation and partial side effects.

## 6. Federated enforcement model

The gateway is the policy decision and coordination contract; enforcement must exist at every consequential boundary:

- Agent runtime: cannot call raw tools or provider credentials directly.
- Connector adapter: validates a signed, short-lived execution permit and exact operation.
- Repository integration: independently enforces repository/branch/path allowlists and protected-branch rules.
- Data adapter: enforces tenant, classification, purpose, region and export restrictions.
- Runtime host: enforces process/container isolation, filesystem, network and resource quotas.
- CI/CD: requires immutable commit binding, trusted workflow identity and separate release authority.
- Evidence store: verifies producer identity, content digest, sequence and retention policy.

If the control plane is unavailable:
- Read-only, low-risk operations may continue only if the local enforcement point has a still-valid signed policy snapshot and a bounded freshness lease.
- Any write, external side effect, credential change, release, canonical change, financial action or irreversible operation must HOLD/REJECT when fresh authorization cannot be established.
- No component may mint a replacement approval or extend a stale policy lease during an outage.

## 7. Admission stages and exit criteria

| Stage | Scope | Exit evidence | Default status |
|---|---|---|---|
| M0 — Inventory & contract reconciliation | Map all existing handlers, adapters, registries, policies and direct-call paths | Commit-pinned asset map, call graph, gap register, protected-path check | HOLD until inventory bounded |
| M1 — Observe-only | Read-only telemetry and decision simulation; no external mutation | Coverage statement, identity mapping, redaction tests, no-side-effect proof | No authority increase |
| M2 — Enforced deny/hold | Deny unknown, stale, unauthorized and out-of-scope calls | Negative tests at every adapter boundary; bypass tests | Fail closed |
| M3 — Isolated sandbox | Harmless synthetic action through one adapter | Isolation, budget, audit, cancellation and replay receipts | Sandbox only |
| M4 — Branch-only workflow | Named non-protected branch and path allowlist | Exact diff, CI on exact head, rollback/recovery, independent review | No merge |
| M5 — Release preparation | Build/sign/attest candidate without publishing | SBOM, provenance, vulnerability report, reproducible artifact, rollback plan | Prepare only |
| M6 — Explicit production admission | One connector/use case at a time | Fresh proof, owner approval, independent security review, operational runbook | Deny by default |
| M7 — Continuous revalidation | Drift, revocation, policy/dependency/model changes and incidents | Scheduled and event-triggered revalidation receipts | Revoke/quarantine on failure |

A stage does not inherit the status of the prior stage if its assumptions, commit, policy, environment, provider, dependency or target changes.

## 8. Fifty acceptance tests

All tests are requirements, not executed results. Each test must record exact commit, environment, test command, fixture digest, output, timestamp and verifier identity.

### Identity and authority
1. Unknown actor identity is rejected.
2. Revoked actor identity is rejected immediately.
3. Expired actor assertion is rejected.
4. Actor role/ceiling mismatch against trusted registry is rejected.
5. Lower authority actor cannot request a higher tier.
6. Tool capability ceiling lower than requested action causes rejection.
7. Environment ceiling lower than requested action causes rejection.
8. Agent cannot grant itself a new capability or modify its profile.
9. Agent cannot approve its own high-risk action.
10. Cross-agent delegation does not increase the child actor's ceiling.

### Policy and approval
11. Unadmitted policy returns HOLD.
12. Unsigned or invalidly signed policy is rejected.
13. Stale policy version/digest is rejected.
14. Conflicting policy versions return HOLD.
15. Policy change requires independent review and authorized approval.
16. Approval for a different action digest is rejected.
17. Expired approval is rejected.
18. Approval is invalidated by target, payload, dependency, budget or policy change.
19. High-risk action without independent human approval is held.
20. Approval replay with a reused nonce/action key cannot authorize a second execution.

### Connector, input and data boundaries
21. Unknown connector is quarantined.
22. Connector adapter digest/version mismatch is quarantined.
23. Endpoint substitution or redirect to an unapproved destination is blocked.
24. Invalid input schema is rejected before dispatch.
25. Invalid provider/tool output schema is rejected and recorded.
26. Prompt injection in fetched content cannot change policy or grant tool authority.
27. Secret canary does not appear in prompts, logs, audit events, outputs or artifacts.
28. Restricted data cannot cross an unapproved tenant, region or provider boundary.
29. Unregistered tool/endpoint discovered in egress telemetry is flagged as shadow asset.
30. Direct model-provider or MCP call that bypasses VX is blocked or reported as an uncovered enforcement gap.

### Runtime, budget and resilience
31. Retry after timeout does not duplicate a non-idempotent side effect.
32. Concurrent duplicate idempotency keys result in at most one execution.
33. Budget exhaustion stops execution within the declared enforcement bound.
34. Recursive agent calls stop at depth, concurrency and wall-time limits.
35. Cancellation prevents queued work and records any in-flight residual effect.
36. Circuit breaker quarantines an unhealthy connector and does not silently fail over to an unapproved one.
37. Control-plane outage with stale policy blocks sensitive actions.
38. Local enforcement continues to reject unauthorized actions during control-plane outage.
39. Clock rollback/skew cannot extend approval or policy validity.
40. Partial write/crash produces a recoverable, explicitly classified state.

### Evidence, supply chain and recovery
41. Tampered evidence digest is detected.
42. Stale CI receipt for a different commit cannot satisfy the current proof obligation.
43. Missing test result remains NOT_RUN/UNKNOWN, never PASS.
44. Producer cannot be sole verifier for an obligation requiring independence.
45. Contradictory evidence remains CONFLICT and is not silently collapsed.
46. Dependency/model/adapter artifact digest change triggers revalidation.
47. SBOM/provenance mismatch blocks admission.
48. Ledger deletion, truncation or event reordering is detectable.
49. Recovery drill restores only a verified checkpoint and preserves incident evidence.
50. `project.genome` and `Ω.000` mutation attempts are denied and recorded.

## 9. Required evidence capsule

Each test/admission claim must have:
- claim ID and falsifiable statement;
- repository, immutable commit SHA, changed paths and environment;
- policy/schema/adapter/dependency digests;
- test ID, exact command, fixture digest and expected outcome;
- execution receipt and exit status;
- raw result reference with secret redaction;
- timestamp and trusted actor/verifier identity;
- counterevidence, limitations and known blind spots;
- recovery/rollback reference where applicable;
- separate technical state, authority state and admission state.

A policy decision is not proof of execution. A successful execution receipt is not proof of correctness. A passing test is not production admission. A green CI run is not evidence of live external connectivity.

## 10. Immediate engineering work queue

1. Reconcile PR #201 with current `main` before extending its branch; the inspected PR branch was 1 commit ahead and 3 commits behind at the time of inspection.
2. Inventory every actual VX-runtime tool/connector invocation path and identify direct-call bypasses.
3. Inspect the current action evaluator, schema validators, identity source, policy loader, event ledger and adapter dispatcher.
4. Write focused tests for the reference evaluator's documented limits; do not label it enforcement.
5. Implement a narrow vertical slice inside the existing VX runtime: authenticated local test principal → validated envelope → admitted test policy → deterministic decision → one inert/read-only adapter → durable event/evidence receipt.
6. Add negative tests before any mutation adapter.
7. Add atomic idempotency and revocation/TOCTOU protections before branch writes.
8. Have an independent reviewer challenge the implementation and test design.
9. Keep live connectors, production activation, spend, merge and deployment blocked until separately authorized.

## 11. Project-specific safety boundaries

- `project.genome` and `Ω.000` are protected and must not be modified by this work.
- Preserve all historical drafts, evidence, failures and superseded records; extend only.
- No privileged-token bypass.
- No external connector activation, network integration, paid call or spend.
- No merge to `main`, release, deployment or public publication without separate explicit approval.
- Use an isolated branch and exact commit evidence.
- Distinguish PROPOSED, SPECIFIED, IMPLEMENTED, RUNNING, VERIFIED, AUTHORIZED and ADMITTED.
- Treat NOT_OBSERVED and INACCESSIBLE as bounded visibility states, not proof of absence.

## 12. Current status

| Artifact / capability | State |
|---|---|
| Existing STCF, federation and integration contracts | SPECIFIED |
| Action envelope and decision schemas | PRESENT; runtime enforcement not established here |
| Default tool-control policy | PROPOSED_NOT_ADMITTED / CONTRACT_ONLY_NOT_CONNECTED |
| Reference evaluator | IMPLEMENTED AS REFERENCE ONLY; explicitly not an enforcement boundary |
| VX-runtime governed execution core | Existing repository claims IMPLEMENTED/TESTED within its documented evidence scope |
| Unified connector gateway | PROPOSED in PR #201; not activated |
| This threat model and admission matrix | PROPOSED / SPECIFIED by this change |
| 50 acceptance tests | SPECIFIED; NOT_RUN |
| Live connector coverage | NOT_VERIFIED |
| Production admission | HOLD |

**Closure rule:** no stage may be marked IMPLEMENTED, RUNNING, VERIFIED, AUTHORIZED or ADMITTED without the corresponding source, runtime, test, approval and evidence records.
