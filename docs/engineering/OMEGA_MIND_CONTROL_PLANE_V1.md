# Ω Mind Control Plane and Agent Simulation Fabric v1

**Document ID:** VAIXLNS-OMEGA-MIND-PLANE-0001  
**Status:** SPECIFIED + REFERENCE SIMULATOR IMPLEMENTATION  
**Authority:** VAIXLNS / project.genome  
**Execution boundary:** VX  
**Planning boundary:** XV  
**Knowledge and provenance:** VV + VLNS  
**Registry:** VI / Ω.000  
**Assurance:** ARC-X + Ω-Arena  
**Version:** 1.0.0

> The console and simulator use synthetic fixtures. They do not call a model provider, mutate a repository, or control production agents. This document separates reference behavior from future live integrations.

## 1. Beyond API aggregation

The core is not a collection of public API wrappers. It is a provider-neutral, policy-governed control plane for task identity, capability grants, dependency-aware scheduling, side-effect authorization, state transitions, evidence requirements, event integrity, independent review and cross-system observability. Public APIs, local models, private runtimes, command-line tools, message buses and human reviewers are adapters behind explicit contracts; none becomes trusted merely because it responds.

The unit is a bounded cognitive worker, not an unconstrained agent. Every worker declares role, implementation/version, capabilities, inputs, repository scope, permitted tools, prohibited effects, budget, timeout, retry policy, output contract and evidence obligations.

## 2. System-of-systems map

| Plane | Responsibility | Owner boundary | Promotion condition |
|---|---|---|---|
| Constitution | Authority, invariants, approval policy | VAIXLNS / project.genome | Exact canonical revision and approved policy |
| Knowledge and provenance | Retrieval, source lineage and conflict preservation | VV / VLNS | Source references and provenance retained |
| Registry | Systems, capabilities, contract versions and adapters | VI / Ω.000 | Schema-valid record plus drift check |
| Planning | Task DAG, topology choice and impact reasoning | XV | Acceptance criteria and resource plan reviewed |
| Execution | Sandboxed tasks, budgets, cancellation and events | VX | Sandbox and policy checks pass |
| Assurance | Claim/counterclaim, evidence admission and replay | ARC-X | Independent, revision-bound evidence |
| Adversarial evaluation | Independent challenge and hard-gated scoring | Ω-Arena | Correctness, security and replay gates pass |
| Research | Literature and repository discovery | NEXENT | Sources retained; hypotheses separated from findings |
| Federation | Cross-repository and cross-runtime adapters | NEXNET | Contract and compatibility tests per connection |

The aggregate dashboard reports each system's epistemic and operational state. It does not manufacture state. Unknown, stale, conflicting or unsupported health remains UNKNOWN/BLOCKED, not green. A system is connected only after an adapter identity, version, permission probe, health check and evidence record all succeed.

## 3. Simulated minds as separated duties

- **Context Cartographer:** read-only retrieval, source maps and unresolved lineage.
- **System Architect:** boundaries, dependency graph, contracts, decisions and migration proposals.
- **Task Compiler:** intent normalization, testable acceptance criteria, dependency DAG and budget.
- **Implementation Planner:** minimal scoped patch plans; no authority to approve its own plan.
- **Implementation Worker:** scoped changes in a disposable workspace only.
- **Adversarial Challenger:** attempts to falsify claims and probes scope escape, prompt injection, hidden coupling and regression risk.
- **Evidence Referee:** independent review of revision-bound evidence; no permission to edit the candidate.
- **Registry Steward:** proposes provenance/index changes after accepted outcomes; cannot silently rewrite canonical history.

“Mind” describes a simulated cognitive role, not consciousness. Production profiles must name the real model/tool implementation and version; the demo roster does not claim those agents or models are deployed.

## 4. Adaptive topology controller

Choose the least expensive topology that meets the assurance contract:

1. Single worker for bounded low-risk tasks.
2. Serial specialists when outputs depend on one another or shared context is material.
3. Isolated parallel workers only for independent tasks with disjoint write sets and isolated workspaces.
4. Escalated review for high-impact tasks, authority ambiguity, conflicts, sensitive scopes or insufficient evidence.

Overlapping write sets require an explicit lock, patch queue or merge protocol. Parallelism is a decision to validate, not a default promise of speed. Record routing features, chosen topology, alternatives, predicted budget, risk, observed elapsed time and failure/retry outcome. Optimize accepted reproducible outcomes per unit cost, not code volume or agent count.

The included simulator emits a dependency-layer schedule marked PLAN_ONLY_NOT_CONCURRENT_RUNTIME. It does not start worker processes and therefore makes no actual concurrency or speed claim.

## 5. Ω-MIND/1 protocol

INTAKE → CANONICAL_CONTEXT → REALITY_GRAPH → TASK_DAG → TOPOLOGY_DECISION → AUTHORIZATION_GATE → ISOLATED_ATTEMPT → REGRESSION_CRUCIBLE → ADVERSARIAL_CHALLENGE → REPLAY_AND_EVIDENCE → INDEPENDENT_REFEREE → HUMAN_ADMISSION → POST-MERGE_OBSERVATION → MEMORY_AND_INDEX_PROPOSAL

Each transition has a typed event, task/attempt/trace identity, monotonically increasing sequence, logical tick, causal context, result, policy version and previous-event digest. Durable deployments should additionally use access-controlled append-only storage, trusted timestamps and signed provenance attestations where available. A local SHA-256 chain detects alteration only if a trusted chain head is retained; it does not authenticate who generated the events.

## 6. Task contract and effect boundary

The task envelope binds:

- Goal, acceptance criteria, exclusions, parent task and attempt IDs.
- Canonical source revision, repository, base commit and permitted paths.
- Role/profile ID, model/tool versions, allowed tool grants and denied actions.
- Dependency DAG, concurrency key, deadline, cancellation, retry cap and idempotency key.
- Token/tool/compute/spend/network budgets and execution environment digest.
- Required tests, adversarial cases, replay policy and evidence bundle contract.
- Output artifacts, changed-path manifest, hashes, verdict and terminal reason.

The schema checks structure; the policy evaluator checks authority. Every requested tool must be within both task grants and role capabilities. Path validation rejects absolute paths, traversal, ambiguous normalization, NUL and backslash separators. Canonical Genome and Ω.000 mutations are blocked from ordinary worker tasks and require a separate explicitly approved change protocol. High-impact actions require human approval; agents cannot elevate their privilege or alter the policy used to judge themselves.

## 7. Evidence is a contract, not a self-report

A production evidence bundle binds task/attempt IDs, repository, base and candidate revisions, actual diff SHA-256, environment digest, toolchain, exact commands, exit codes, log/artifact hashes, skipped/flaky checks, referee identity/policy/version, verdict and known limitations. Evidence references must be resolved and verified by the consumer. The reference simulator uses sim://fixture references solely to exercise gates; they are synthetic and never admissible as live evidence.

The existing Ω Change Capsule validator checks structural invariants. The added omega_git_diff_evidence tool calculates SHA-256 from an actual local Git diff and compares the digest and changed-path manifest with the capsule. This is a read-only binding check, not an admission decision; production admission still requires authenticated evidence references, environment/toolchain binding, independent test execution, review of protected-path changes, and human approval where policy requires it.

## 8. Event integrity and replay

The reference simulator canonicalizes JSON using UTF-8, sorted keys and compact separators, hashes each event and links it to the previous hash. Tests validate sequence continuity and detect tampering. This narrow mechanism does not provide distributed consensus, signature authority, durable storage, trusted time, provider attestations or proof that a check actually ran.

Live replay must pin toolchain/dependencies, candidate revision, environment configuration, task inputs and random seeds where applicable. If a boundary is nondeterministic, record it and bound it; do not relabel a non-reproducible outcome as verified.

## 9. Cross-system adapters, not API assumptions

Each adapter contract declares system ID, owner, interface version, identity/authentication mechanism, requested scopes, data classification, timeout/rate/concurrency limits, idempotency behavior, retry/backoff rules, error taxonomy, health semantics, provenance format and conformance tests. Secret material stays in a secret store; it must not enter prompts or logs.

Initial adapter classes:
- **Repository adapter:** branch/revision/diff/status/PR operations, least privilege and protected-branch compatibility.
- **Model adapter:** model/version, structured-output contract, budget and refusal/error behavior.
- **Tool adapter:** explicit capability and side-effect classification, timeout and output limit.
- **Event adapter:** append-only event envelope, replay cursor and deduplication.
- **Evidence adapter:** immutable artifact reference, content digest and access policy.
- **Registry adapter:** schema validation, lineage and conflict detection; writes remain proposals until approved.

An adapter passes conformance only after positive, negative, timeout, duplicate request, permission denial, stale version, malformed response and partial-failure tests pass. Availability is not correctness, and interoperability is not inferred from similar names.

## Interoperability standards and research boundary

The adapter architecture should reuse standards where they fit, while keeping VAIXLNS governance above transport and message exchange:

- **MCP (Model Context Protocol), specification dated 2026-07-28:** tool discovery/invocation and contextual integration. Tool input schemas, access controls, user-visible invocation and confirmation guidance are relevant at the tool-adapter boundary. An MCP-compatible server is not automatically trusted; validate its outputs, scope, side effects and identity. Official sources: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx and https://blog.modelcontextprotocol.io/posts/2026-07-28/
- **A2A Protocol v1.0.0:** interoperability among independent agent systems through capability discovery, task exchange, modalities and handoffs. It is a federation transport/interaction contract, not a replacement for canonical authority, permission mediation, evidence admission or an independent referee. Official source: https://a2a-protocol.org/v1.0.0/
- **SLSA provenance v1.2:** source-to-artifact provenance and supply-chain integrity signals. Map applicable attestations into the evidence bundle; do not treat a provenance record alone as proof of functional correctness or acceptance. Official source: https://slsa.dev/spec/v1.2/provenance

The resulting stack is layered: MCP for tool-facing interfaces where appropriate, A2A for inter-agent communication where appropriate, SLSA/in-toto-style provenance for artifact-origin evidence where applicable, and Ω-MIND/1 for task authority, scheduling, side-effect limits, system state, refusal semantics and admission. Transport compatibility cannot override any of these gates.

These standards evolve. Pin the exact protocol version and adapter test suite in each system registry record; compatibility must be re-verified on version change rather than inferred from a URL called latest.

## 10. Failure semantics

- Missing or conflicting authority: BLOCKED; preserve both source references.
- Missing evidence or undecidable referee: INCONCLUSIVE.
- Out-of-scope write, denied tool or budget overrun: stop/block and preserve the event.
- Critical security finding or hash mismatch: QUARANTINED/REJECTED.
- Retry: new attempt linked to the previous attempt; do not erase failures.
- Registry synchronization failure: report separately from engineering outcome.
- Emergency stop: stop new effects and cancel cancellable work without deleting history.

## 11. Dashboards and scorecard

The local console displays per-system epistemic state separately from adapter connection state, bounded worker roles, task graph, routing schedule, assurance gates, event chain and blocked reasons. Demo records are labeled SIMULATION and do not imply real health.

Operational metrics include acceptance-criterion pass rate, first-pass verification rate, replay reproducibility, escaped regressions, severity-weighted security findings, time-to-evidence, human override rate, duplicate-work rate, registry drift, cost per accepted change, retry amplification, cancellation latency and post-merge failure rate. Every KPI needs a documented numerator, denominator, time window and event source.

## 12. Implemented reference slice and limits

The reference slice provides:
- A deterministic standard-library simulation engine.
- Dependency DAG validation and layered scheduling plans.
- Task-level role/tool, path-scope, protected-path, dependency and budget gates.
- Explicit simulated verification states with fail-closed evidence handling.
- Hash-linked event records plus chain validation.
- A scenario fixture and negative/adversarial unit tests.
- A read-only Git-object-derived change-capsule verifier with temporary-repository tests.
- A standalone local HTML console using fixture data only.
- Versioned task and evidence JSON Schemas.

It does **not** yet provide live model invocation, concurrent worker runtime, OS/container isolation, a distributed event bus, signed evidence, durable control database, cross-repository writes, credentials, production deployment or live telemetry. Those require separately implemented adapters and security reviews. This slice is SPECIFIED/PARTIAL, never VERIFIED as a full agent platform.

## 13. Acceptance criteria for the next runtime stage

1. One task runs in a disposable isolated workspace with denied network by default.
2. Tool calls pass a broker enforcing scoped capabilities and recording actual effects.
3. A candidate diff digest is calculated from Git objects, not accepted from its own manifest.
4. Unit, integration, negative and adversarial tests execute with raw logs retained.
5. A separate referee validates evidence without write access to the candidate.
6. A complete attempt can be replayed against pinned revisions and environment.
7. Cancellation, retries, timeout, partial output and duplicate requests are fault-tested.
8. Human approval and protected-branch policy are enforced before consequential actions.
9. Post-merge verification and index synchronization are reported as distinct results.
10. A live systems dashboard turns green only from fresh, independently checked telemetry.

Until all mandatory criteria are met, do not report a full production agent workflow, autonomous system-wide control or worldwide superiority.
