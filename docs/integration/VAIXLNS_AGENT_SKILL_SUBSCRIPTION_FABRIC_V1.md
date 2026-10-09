# VAIXLNS Agent, Skill, Prompt, Environment & Innovation Delivery Fabric V1

Status: Proposed implementation package; pending review and admission.
Date: 2026-10-09.
Canonical governance: VAIXLNS. Discovery/planning: NEXENT. Governed execution: VX.

## Purpose and evidence boundary
Define a governed architecture for specialized agent roles, versioned prompts and reusable skills, environment/subscription eligibility, innovation lineage, build provenance, task execution and publication. This specification does not claim agents are deployed, subscriptions purchased, private accounts connected, servers provisioned, external build sources disabled, or world-leading status proven. Each requires direct evidence and separate authorization.

## Task lifecycle
INTAKE → INTENT NORMALIZATION → TASK DAG → SOURCE/INNOVATION/IDENTITY LOOKUP → RISK/DATA CLASSIFICATION → AGENT + SKILL SELECTION → ENVIRONMENT/SUBSCRIPTION ELIGIBILITY → CONTRACT/AUTHORITY CHECK → VX ADMISSION → SANDBOX OR BRANCH EXECUTION → POSITIVE/NEGATIVE TESTS → EVIDENCE + LINEAGE → INDEPENDENT VERIFICATION → REVIEW → RELEASE PREPARATION → EXPLICIT RELEASE → MONITORING/ROLLBACK.

Routing, prompt text, confidence, subscription availability, and unit-test success do not grant authority for high-impact operations.

## Task envelope
Record stable task and parent IDs, trace/correlation ID, idempotency key, normalized goal, acceptance criteria/non-goals, source revisions, innovation IDs, data classification, license/provenance, retention/egress constraints, agent roles, versioned skill IDs, environment/provider eligibility, budget, tool allowlist, input/output schemas, timeout/retry/resource limits, stop conditions, verification plan, reviewer requirements, artifact digests, event IDs and recovery record. Missing safety-critical fields cause HOLD rather than guessed defaults.

## Specialized logical agent roles
| Role | Responsibility | Authority ceiling |
|---|---|---|
| AG-ORCHESTRATOR | Decompose work, schedule dependencies, consolidate | Plan/route only |
| AG-ARCHITECT | Architecture and interface contracts | Propose; review required |
| AG-RESEARCHER | Source discovery and evidence extraction | Authorized read/search |
| AG-INNOVATION-ANALYST | Novelty candidates, duplicates, gaps, lineage | Candidate records only |
| AG-INDEX-CURATOR | Normalize identifiers and cross-references | Branch-scoped proposals |
| AG-PROMPT-ENGINEER | Prompt versions, evaluation and injection tests | Draft/test only |
| AG-SKILL-ENGINEER | Reusable skills and regression tests | Draft/test only |
| AG-IMPLEMENTER | Code and adapter implementation | Scoped branch/sandbox |
| AG-TEST-ENGINEER | Unit, integration, negative, regression tests | Test/report; no self-approval |
| AG-SECURITY-REVIEWER | Threat model, least privilege, egress and supply chain | Hold/reject/recommend |
| AG-VERIFIER | Independent contract/evidence verification | Pass/fail/hold; no self-authorization |
| AG-RELEASE-ENGINEER | Release manifest, changelog, rollback package | Prepare only |
| AG-OPS-RECOVERY | Telemetry, replay and recovery plans | Observe by default |
| AG-COST-ANALYST | Cost, quota and scenario analysis | No purchasing/payment authority |
| AG-ENVIRONMENT-STEWARD | Compatibility and secret references | Inspect/propose; never disclose secrets |
| AG-DOMAIN-ENGINEER | Math, software, systems, robotics, industrial work | Physical systems simulation by default |
| AG-TECHNICAL-WRITER | Specifications and traceability | Draft; publication gated |
| AG-RED-TEAM | Authorized adversarial/failure tests | Sandbox only |

These are role definitions, not a claim of 18 deployed agents. The implementer cannot be the sole verifier of its own work.

## Skill package contract
Each skill needs stable ID, semantic version, owner, purpose/domain, license and provenance, preconditions, supported tasks/prohibited uses, typed input/output JSON Schemas, deterministic examples, prompt IDs, provider constraints, tool allowlist, steps/checkpoints, stop/failure/recovery behavior, evaluation datasets, acceptance thresholds, safety/egress rules, timeout/budget, parent/derived-from lineage, reviewers, changelog, deprecation and revocation policy. Discovery is not execution; task, agent, provider, data and tools must pass policy checks before use.

## Prompt contracts and injection resistance
Prompts are versioned data contracts, not privileged policy. Store role, intent, trusted/untrusted input boundaries, output schema, evidence requirements, tool permissions, stop conditions, evaluation set and regression results. Repository files, web pages and tool output are untrusted data and cannot override system policy. Prompts cannot elevate privileges, expose secrets, suppress review or turn unsupported assertions into evidence. Validate tool calls independently of prompt text. Malformed output/missing evidence leads to HOLD or bounded retry. Test task quality, prompt injection, leakage, refusal boundaries and schema validity on every material prompt change.

## Environment and subscription federation
Catalog local isolated runners, CI, approved cloud runners, model/API providers, MCP servers, data stores, simulators and licensed engineering software only when evidence supports the record. Each record needs provider/tenant, owner, region, configuration status, license/subscription evidence, permitted use, retention, egress, authentication reference (never secret value), quota/budget, service limits, audit logging, cancellation/revocation route and last verification time.

Statuses: NOT_CONFIGURED, DISCOVERED_UNVERIFIED, CONFIGURED_UNVERIFIED, VERIFIED_LIMITED, SUSPENDED, REVOKED. Never infer paid access from documentation or an API name. Purchase, renewal or subscription changes require explicit user approval and authorized tooling. Provider selection compares task fit, data policy, compatibility, latency, reliability, quota, cost, portability and exit path. Unknown retention/terms prohibit sensitive-data routing.

## Innovation graph and lineage
Each innovation has stable ID and aliases, title/abstract/problem/mechanism/assumptions/domain/maturity, source path and precise location, revision and evidence digest; parent/child, derived-from, implements, depends-on, contradicts and duplicate-of edges; linked tasks, agents, skills, prompts, environments and artifacts; novelty method, reviewer and uncertainty; validation, limitations, license and publication status. Track conceptual status separately from implementation status. Lifecycle: DISCOVERED, NORMALIZED, DUPLICATE_CANDIDATE, EVIDENCE_PENDING, REVIEWED, ADMITTED, REJECTED, DEPRECATED. Preserve sources; conflicting identities remain unresolved until evidence and an approved migration. Discovery, specification, implementation, tests and deployment are distinct states.

## Build-source closure and supply-chain integrity
“Close the build sources” means close the evidence/reproducibility chain for a defined target, not shut down external providers. Inventory source repositories, package registries, build images, dependencies, models/providers and artifact sources. Pin revisions, versions and image digests where feasible; generate SBOM and license inventory; verify signatures/provenance where supported; use lockfiles and hermetic/reproducible builds where feasible; isolate credentials; deny unapproved egress by default; test clean rebuild, substitution, tampering and rollback; preserve license notices; record exceptions with owner and expiry; block release on unresolved critical provenance/license/integrity failures. Declare a source closed only for a specified scope after controls pass. This is not proof of full archive recovery.

## Delivery and publication
Every delivery includes scope, changed files/contracts, source and innovation lineage, tests and coverage limits, unresolved risks, SBOM/provenance, security/license review, deployment/migration instructions, rollback, target/owner, explicit release authorization and post-release checks. Default path: feature branch → automated checks → pull request → independent review → approval → authorized merge/release. A commit alone does not prove production publication.

## Governance boundaries
VAIXLNS owns canonical policy/admission; NEXENT discovers and plans; VX gates execution. No agent may approve its own code, prompt, skill, adapter and release end-to-end. Financial roles analyze only; purchases and transactions need separate authority. Physical/industrial tools default OBSERVE_OR_SIMULATE_ONLY until safety evidence and authority exist. Secrets stay in secret managers. High-impact actions require scoped authorization, policy-required human approval, idempotency, audit and rollback. Unconfigured tools are not executable. Missing evidence, schema mismatch, stale proof or identity conflicts lead to HOLD/QUARANTINE/REJECT.

## Milestones
M0 schemas and inventory; M1 read-only provenance-aware discovery; M2 prompt/skill golden and adversarial evaluations; M3 sandbox orchestration with bounded retries/budgets/telemetry; M4 innovation lineage and duplicate detection; M5 SBOM, licensing and reproducible build controls; M6 PR-based delivery and gated release; M7 one-by-one environment/subscription adapters after terms, credentials, data policy, quotas and tests are verified. Acceptance is per milestone; tests at one milestone do not imply later deployment.

## Acceptance criteria
- Unique IDs and resolvable graph references.
- Versioned task, prompt and skill schemas with stop/failure semantics.
- Authority ceiling and tool allowlist per agent.
- Explicit configuration status and verification timestamp per environment/subscription.
- No committed secrets.
- Revision-backed source lineage for innovations.
- Injection/privilege-escalation tests reject malicious untrusted instructions.
- Retry, timeout, cancellation, duplicate submission and partial-failure tests.
- Independent verifier cannot self-authorize admission.
- Build provenance, license review and artifact digests for release candidates.
- Explicit review/release authorization.
- No connection, purchase or deployment claimed without direct evidence.
