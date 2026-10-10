# VX / XV Cognitive Continuity Engine v1

**State:** SPECIFIED; the reference task-planning and local memory slice is IMPLEMENTED only after code and tests are inspected.  
**Owner:** VAIXLNS  
**Authority:** project.genome v1.0.0 and Ω.000 remain authoritative.  
**Safety rule:** a generated plan is not an executed action; a model answer is not evidence of truth.

## 1. User-facing promise

The system should accept an ordinary request such as "I want a dashboard that collects project status, detects broken tests, and explains what needs fixing" and turn it into an inspectable work contract: inferred intent, context to retrieve, work units, responsible roles, outputs, acceptance tests, approval gates, and a durable record.

The system should reduce the need for users to know repository paths, architecture vocabulary, command syntax, or the internal decomposition of a task. It should ask only for information that is genuinely required to proceed safely; otherwise it should state its assumptions and produce the best safe next artifact.

It must not claim that it understands every domain, can access unavailable services, remembers data that was not persisted, or completed work that has not been observed.

## 2. Non-negotiable epistemic contract

A natural-language response must distinguish:

- **VERIFIED FACT:** directly supported by inspectable evidence and a stated verification method.
- **EVIDENCE-SUPPORTED:** supported by traceable sources but not independently established.
- **INFERENCE:** reasoned from evidence; alternatives and assumptions remain visible.
- **HYPOTHESIS:** a candidate explanation that needs testing.
- **SPECIFICATION:** a designed behavior, not yet demonstrated in execution.
- **UNVERIFIED / UNKNOWN:** required evidence is absent or unavailable.
- **CONFLICT:** credible records disagree; the conflict is preserved, never silently merged.

Evidence records should include source identity, pinned revision or retrieval time, content hash, and relevant location. A URL or a confident model statement alone does not establish truth. Time-sensitive claims must be refreshed from current sources. High-impact claims require an explicit verification method and independent review before they may be labeled VERIFIED.

Explanations should use this shape when useful:
1. What is known.
2. The evidence and its date/revision.
3. What is inferred and why.
4. What remains uncertain or conflicts.
5. What would prove or falsify the conclusion.
6. The next safe action.

## 3. VX: parent orchestration fabric

VX is the task and execution coordinator, not a fictional single omniscient mind. It maintains task contracts and coordinates specialized roles through provider-independent adapters.

Initial logical roles:
- **Intent Analyst:** convert a plain-language request into a goal, constraints, and deliverables.
- **Research Mind:** retrieve and compare evidence, mark source freshness, and preserve contradictions.
- **Systems Architect:** map requirements to the existing VAIXLNS architecture and avoid duplicate subsystems.
- **Builder / Executor:** implement only through explicitly authorized tools and bounded workspaces.
- **Adversarial Reviewer:** generate counterexamples, test failure paths, and challenge unjustified claims.
- **Verification Mind:** run acceptance tests and replay checks; report observed results.
- **Explainer:** translate the artifact and evidence into a clear user-facing account.
- **Memory Steward:** save task contracts, artifacts, source receipts, decisions, test results, and recovery pointers.
- **Repair Engineer:** diagnose failed tests, propose minimal patches, and preserve rollback paths.

These are logical roles, not proof that multiple external AI providers are connected. Real model providers and tools require adapters, credentials where appropriate, evaluations, and health evidence. Role names must never be counted as active providers.

### Task lifecycle

`REQUESTED → NORMALIZED → CONTEXT_RETRIEVED → PLANNED → AUTHORIZATION_CHECKED → EXECUTING → TESTING → VERIFIED / PARTIAL / BLOCKED → EXPLAINED → RECORDED`

The reference implementation in this change creates deterministic plans and a local append-only event ledger. It does not execute arbitrary commands or automatically connect model providers.

## 4. XV: repair, memory, and continuity fabric

XV is the continuity and recovery counterpart. It should:
- keep an append-only history of observable tasks, plans, evidence references, artifact hashes, test outcomes, decisions, and user-approved preferences;
- restore task context from prior records and link related artifacts;
- track failed verification steps and create repair proposals;
- prefer minimal, reversible changes and preserve before/after references;
- rerun relevant tests after repair and record the result;
- quarantine uncertain or conflicting state instead of overwriting it;
- provide export, backup, restore, and integrity-check mechanisms.

"Remember everything" is a design goal, not a claim of literal perfect recall. Persistence is limited to captured information, storage availability, retention settings, and backup integrity. The reference SQLite store is local and unencrypted; it must not contain passwords, access tokens, private keys, or financial credentials. Hidden/private model reasoning is not the memory contract; record observable decisions, evidence, plans, and outcomes.

### Hash-chain event record

Each record includes sequence, event ID, timestamp, type, canonical JSON payload, previous event hash, and current event hash. The verifier detects modification, deletion, or reordering in the stored chain. A hash chain is tamper-evident, not a substitute for signed remote backups, access control, encryption, or protection against an attacker rewriting the entire database and chain.

## 5. XV repair contract

A failure triggers:
`OBSERVE → REPRODUCE → LOCALIZE → FORM HYPOTHESIS → PROPOSE MINIMAL PATCH → TEST → REVIEW → ADMIT / REJECT → RECORD`

No repair is automatically admitted merely because it fixes one test. The repair envelope includes:
- failing test or incident ID;
- exact source revision and affected paths;
- reproduction instructions;
- root-cause hypothesis and evidence;
- proposed diff and blast radius;
- regression, security, and compatibility tests;
- rollback reference;
- approval requirement;
- final observed result.

Changing canonical authority, deleting/replacing user data, publishing, deploying, spending money, trading, sending messages, or altering access controls requires explicit approval by an authorized user/system. Network access and shell execution are capabilities, never implicit consequences of natural-language requests.

## 6. "I ask; the system works" interface

The request adapter should:
1. Preserve the original request.
2. Extract the desired outcome, constraints, deliverables, and implicit ambiguities.
3. Search project memory and the repository before inventing new components.
4. Build a task graph with owners, prerequisites, outputs, and acceptance criteria.
5. Execute only the work covered by granted capabilities.
6. Save checkpoints after material state transitions.
7. Validate the actual artifact and test output.
8. Explain what was done, what failed, and what is still pending, with direct artifact links.
9. Offer a recovery path and resume from the last verified checkpoint.

If ambiguity does not block a safe first step, proceed with a stated assumption. If a missing choice affects safety, money, data loss, external publication, or irreversible change, stop at the approval gate.

## 7. Integration boundaries

- **VAIXLNS / Ω.000:** canonical governance, identity, registry, history, admission, and lineage.
- **VLNS:** governed model/knowledge activation and provider mediation; provider identity and availability must be verified.
- **VX:** multi-role planning, orchestration, sandboxed execution, experiments, replay, and verification.
- **XV:** repair coordination, durable task history, evidence continuity, recovery pointers, and memory integrity checks.
- **ARC-X Ω:** source retrieval, repository reconstruction, claims/evidence normalization, and contradiction analysis.
- **VV:** independent verification and proof-oriented review.

No component may upgrade itself to canonical authority. Existing architecture documents remain design sources; execution status is determined only by reproducible evidence.

## 8. High-value extensions

1. **Intent Compiler:** natural language → typed task contract → dependency graph → acceptance tests.
2. **Project Twin:** current repository map with paths, owners, dependencies, runtime status, evidence age, and unresolved gaps.
3. **Unknown-Unknowns Engine:** ask what evidence, dependency, user constraint, or failure mode could invalidate the plan.
4. **Evidence-Carrying Answers:** key factual statements link to the exact source revision or execution evidence.
5. **Repair Arena:** generate multiple minimal repair candidates; isolate, test, compare blast radius, then select through governed review.
6. **Continuity Capsule:** portable, checksummed context package for resuming work after a session, model, or device change.
7. **Capability Router:** choose tools/providers by task fit, access, latency, price, reliability, and evaluation results—not brand prestige.
8. **Self-Measurement:** track first-pass test success, regressions, unsupported-claim rate, task resumption success, time-to-repair, and human-approval compliance.
9. **Reality Synchronizer:** compare intended architecture, repository files, CI runs, and live observations; label each source and freshness.
10. **Fail-Closed Recovery:** when memory is corrupted or sources conflict, stop promotion, restore from a verified backup, and keep the incident record.

## 9. Initial acceptance criteria

- A natural-language request generates a structured plan with dependency order and acceptance tests.
- Research/build/repair intents route to appropriate logical roles.
- High-impact requests are flagged for explicit approval.
- Evidence claims without adequate source hashes or verification methods cannot be represented as VERIFIED.
- Identical plan inputs generate the same step structure apart from generated IDs/timestamps.
- Memory append, search, and hash-chain verification work locally.
- Changes to old stored events are detected by integrity verification.
- No provider, repository mutation, live action, or external service is claimed active without observed evidence.
- Existing `project.genome`, `registry/omega/omega-000-master-index.json`, and historical artifacts are not modified by this implementation.

## 10. Status boundary

The repository-backed reference slice is a starting kernel—not the final autonomous organization. Real multi-provider reasoning, broad repository operations, remote search, code execution, automatic repair application, encrypted/replicated storage, and production-grade recovery require separately implemented adapters and conformance evidence.
