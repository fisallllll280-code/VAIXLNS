# Systems, Tools & Interfaces — Operating Mechanism Index v1

**Index status:** `CANONICAL-CANDIDATE / REVIEW REQUIRED`  
**Prepared:** 2026-10-28  
**Purpose:** One navigable index explaining what each system does, how work flows through it, which interfaces connect it, and what evidence is needed before claims of live operation.

> This index explains documented architecture and proposed operating mechanisms. A specification, registry entry, README, or passing static test does not by itself prove a live service, deployed agent, active connection, or production enforcement. Unknowns remain explicit.

## 1. Federation map

```text
NEXENT ── discover / research / design / simulate / propose ──┐
                                                              ▼
VLNS ── governed model/semantic activation ───────────────► VAIXLNS
                                                              │
                       canonical identity, policy, registry, admission
                                                              │
                                                              ▼
VX ── authorize action → execute → record event → replay/test ─┐
                                                               ▼
VV / ARC-X Ω / Ω-RAC ── independently inspect evidence and acceptance
                                                               │
                                                               ▼
                         admit / hold / reject / rollback
```

The diagram is the intended/documented control flow, not proof that every edge is connected at runtime. The repository federation contract specifically leaves identity equivalences such as VLNS↔NAXLNS and NEXNET↔NEXENT unverified until evidence is supplied.

## 2. System operating mechanisms

### 2.1 VAIXLNS — canonical governance and project memory

**Purpose:** Own canonical identities, architecture decisions, registries, recovery lineage, promotion rules, and the durable project index.

**Mechanism**
1. Receive a discovery, change proposal, evidence receipt, or recovery record.
2. Resolve the source identity and preserve its revision, provenance, and historical name.
3. Compare the proposal against canonical contracts, existing records, duplicates, dependencies, and known conflicts.
4. Assign a truthful lifecycle state such as `RECOVERED`, `PROPOSED`, `IMPLEMENTED`, or `VERIFIED`; do not collapse these states.
5. Admit only changes meeting the relevant evidence and authorization gates.
6. Preserve decision history and link every promoted claim to its source and validation evidence.

**Interfaces:** Master Index, Ω.000/Canonical Nexus, architecture and innovation indexes, repository federation index, typed federation contracts, decision register, promotion gates.

**Evidence needed:** pinned repository revision, provenance/hash, validation output, review decision, and recovery/rollback record where applicable.

**Known boundary:** historical Master Index material spans roughly 0001–2750 across 40+ families, but the repository documentation says not every legacy row has been extracted item-by-item. Do not claim complete legacy recovery.

### 2.2 NEXENT — discovery, research, and proposal generation

**Purpose:** Find external assets, inspect technical possibilities, compare designs, and generate testable proposals without silently making them canonical.

**Mechanism**
1. Discover repositories, papers, tools, models, APIs, and relevant project artifacts.
2. Record exact source, revision/date, license, maintenance and dependency signals.
3. Extract capabilities, constraints, threat surface, overlap, and missing evidence.
4. Compare candidates against existing VAIXLNS/VX/NEXENT capabilities and explicit evaluation criteria.
5. Produce a proposal with expected value, integration boundary, acceptance tests, and failure modes.
6. Hand the proposal to VAIXLNS for governance; do not promote it itself.

**Interfaces:** source/archive indexes, external systems candidate registry, repository search, web/API connectors, innovation catalogs, sandbox/evaluation harnesses.

**Evidence needed:** source URL and pinned revision, repeatable assessment, benchmark or test results, and a traceable proposal.

**Known boundary:** discovery is not proof of installation, compatibility, safety, or production readiness.

### 2.3 VX — governed execution and runtime

**Purpose:** Execute approved work through controlled action envelopes rather than unrestricted agent-to-tool calls.

**Mechanism**
1. Accept a typed task and resolve its declared capability profile.
2. Convert each consequential tool request into an action envelope containing identity, intent, scope, inputs, permissions, and trace identifiers.
3. Evaluate policy, capability, identity, resource limits, and the required federation gates.
4. Deny or hold actions that lack authority, exceed scope, or lack required evidence.
5. Execute approved actions in the designated runtime/adapter.
6. Emit event records, outputs, error details, and replay/verification artifacts.
7. Revalidate outputs before the result is eligible for downstream acceptance.

**Interfaces:** VX Runtime, VX Federation Gate, Sovereign Tool Control Fabric (STCF), action-envelope schema, policy-decision schema, agent-runtime profiles, adapters, event/state/ledger/replay.

**Evidence needed:** exact runtime commit, policy decision, execution receipt, test logs, artifact hashes, and independent acceptance evidence.

**Known boundary:** documented agent profiles are logical templates unless deployment evidence says otherwise. The STCF specification explicitly does not establish runtime enforcement by itself.

### 2.4 VLNS — governed model and semantic activation

**Purpose:** Provide a controlled boundary for model/semantic participation without giving a model authority over canonical policy.

**Mechanism**
1. Receive a governed activation request.
2. Validate the signed, provider-neutral activation envelope and declared identity/capability.
3. Apply the configured activation policy and return a receipt bound to the activation identifier and envelope hash.
4. VX validates the receipt and records an evidence event.
5. Independent conformance, replay, and admission checks determine whether the activation may be used.

**Interfaces:** VLNS→VX activation bridge, signed activation-envelope schema, activation-contract registry, model/provider adapters.

**Evidence needed:** identity proof, signature/receipt verification, live endpoint conformance, replay evidence, and authorized canonical admission.

**Known boundary:** repository docs say live VLNS connectivity and VLNS↔NAXLNS identity equivalence remain unverified. Do not treat names as proof of identity.

### 2.5 VV — verification and acceptance

**Purpose:** Challenge claims independently and decide whether the submitted evidence meets acceptance criteria.

**Mechanism**
1. Convert a claim into explicit, falsifiable acceptance conditions.
2. Identify the independent source or test needed for each condition.
3. Re-run or inspect tests against a pinned revision and known environment.
4. Check failures, missing observations, replay consistency, and conflicting evidence.
5. Issue pass, fail, or hold with reasons and links to receipts.
6. Prevent unsupported claims from being promoted.

**Interfaces:** test suites, proof/evidence records, ARC-X Ω, Ω-RAC, OIF, CI receipts, regression and replay harnesses.

**Evidence needed:** reproducible commands, raw results, environment/commit identity, and independent review.

**Known boundary:** the name VV alone does not mean a separately deployed verifier exists; verify the implementation and its independence.

### 2.6 ARC-X Ω — evidence and claim evaluation

**Purpose:** Structure the relationship between claims, observations, proof obligations, and decisions.

**Mechanism**
1. Accept a claim and its required proof obligations.
2. Resolve evidence sources and their provenance.
3. Evaluate whether evidence is relevant, fresh, independent, and bound to the claim/revision.
4. Mark missing or contradictory evidence as unresolved rather than silently inferring success.
5. Produce a traceable assurance/decision record for downstream verification and governance.

**Interfaces:** evidence ledger, repository/test receipts, Omega-RAC where implemented, acceptance gates, canonical decision records.

**Evidence needed:** schema-valid receipt, source/revision binding, reproducible checks, and independent review.

**Known boundary:** architecture documents and a tool specification are not themselves proof that the complete compiler or evaluator is deployed.

### 2.7 Ω-RAC — assurance evaluation kernel

**Purpose:** Evaluate declared assurance obligations deterministically and fail closed when required observations or dependencies are absent.

**Documented mechanism to validate against source:** canonicalize inputs; fingerprint engine/policy/environment; evaluate assurance rules; detect recursive/circular assurance and missing observations; calculate dependency closure/revalidation frontier; emit a structured AssuranceReport; quarantine or hold insufficiently supported results.

**Interfaces:** assurance schemas, policy/engine fingerprints, dependency graph, evidence receipts, CI and benchmark suites.

**Evidence needed:** exact implementation revision, unit/integration test outputs, deterministic replay, adversarial cases, and independent verification.

**Known boundary:** earlier project notes mention an `omega_rac/` implementation and benchmark identifiers, but this index does not claim those tests were freshly run in this change.

### 2.8 OIF — operational assurance and incident history

**Purpose:** Connect system health and operational events to evidence, decisions, and recovery actions.

**Intended mechanism:** collect operational events; correlate them with system/contract/version identity; detect a breached service or safety condition; open a bounded incident record; run authorized diagnostics; verify recovery; retain a post-incident receipt and regression test.

**Interfaces:** telemetry, Event/State/Ledger/Replay, incident records, runtime health checks, rollback and recovery certificates.

**Evidence needed:** live telemetry source, alert rules, incident examples, recovery drills, and verified regression outcomes.

**Known boundary:** OIF must not be marked live solely because an architecture or assurance document exists.

### 2.9 Canonical Nexus / Ω.000 — identity and relationship graph

**Purpose:** Resolve canonical entities, source lineage, ownership, contracts, dependencies, and cross-system edges.

**Intended mechanism:** assign stable IDs; attach source and version references; represent typed relationships; detect ambiguous identities and conflicting claims; calculate dependency impact; require explicit resolution before rename, reassignment, or destructive merge.

**Interfaces:** master index, repository federation manifest, typed contract edges, provenance records, dependency/revalidation graphs.

**Evidence needed:** validated graph/registry, stable IDs, source hashes, conflict reports, and tests for ambiguous or missing edges.

### 2.10 Event / State / Ledger / Replay — operational memory

**Purpose:** Preserve what was requested, what happened, what state changed, and whether the same inputs reproduce the same result.

**Intended mechanism**
- **Event:** append a timestamped, correlated record of an action or observation.
- **State:** represent the current derived state and its source events.
- **Ledger:** preserve ordered, attributable records and relevant integrity hashes.
- **Replay:** reconstruct or re-execute a bounded flow against pinned inputs and compare outputs.

**Interfaces:** VX action envelopes, receipts, execution IDs, state snapshots, hashes, test/replay harnesses, audit records.

**Evidence needed:** event schema, integrity checks, replay fixtures, deterministic comparisons, and recovery tests.

**Known boundary:** the conceptual pattern does not prove an immutable ledger or deterministic production replay exists.

### 2.11 NEXUS / Workflow Registry — discoverable operational workflows

**Purpose:** Index workflow definitions, triggers, inputs/outputs, owners, versions, dependencies, and run outcomes.

**Intended mechanism:** register a workflow with a versioned schema; validate its triggers and dependencies; dispatch only authorized runs; persist run status and outputs; correlate failures; support retry/idempotency and controlled replay.

**Interfaces:** workflow JSON/API, scheduler, database/search index, web control surface, GitHub Actions, n8n or other candidate engines.

**Evidence needed:** actual workflow files, API contract, storage schema, run receipts, auth tests, retry/idempotency tests, and deployment evidence.

**Known boundary:** n8n, SQLite FTS5, Docker, and web UI appear in project materials as candidate/related surfaces; their current connectivity must be inspected separately.

### 2.12 RIRF — repository inspection and change fabric

**Purpose:** Make repository discovery and modifications traceable and reversible.

**Intended mechanism:** enumerate accessible repositories; inventory files and refs; capture commit identity and hashes; inspect before editing; stage changes on a separate branch; run targeted validation; produce a diff and review request; preserve rollback path.

**Interfaces:** GitHub API, repository and branch search, file fetch/create/update, CI, pull requests, archive/source indexes.

**Evidence needed:** actual API results, commit SHAs, diff, validation logs, and review/merge status.

**Known boundary:** a successful file write or open pull request proves a repository change was staged, not that tests passed or the change was merged.

### 2.13 VX Agent Fabric — specialized agents under common controls

**Purpose:** Define role-specialized agents without granting them independent tool authority.

**Intended mechanism:** map a task to a role profile; provide bounded context and declared capabilities; route tool requests through VX action envelopes and policy; collect independent results; verify outputs; merge only accepted results.

**Interfaces:** agent profile registry, runtime role bindings, tool-action envelope, policy evaluator, task router, evidence/verification receipts.

**Evidence needed:** active runtime bindings, deny-path tests, privilege-boundary tests, multi-agent conflict handling, and traceable execution receipts.

**Known boundary:** role catalogs are templates; direct tool invocation is disabled by contract in the documented design, but actual runtime enforcement needs runtime evidence.

### 2.14 Innovation / Architecture Forge

**Purpose:** Generate architecture candidates and evaluate evolution without changing canonical production state automatically.

**Intended mechanism:** describe a capability gap; search the architecture space; compose or mutate candidate designs; run static and sandbox checks; compare candidates against a fixed scorecard; generate a proposal and rollback plan; submit to governance.

**Interfaces:** innovation master index, operation index, capability genome, architecture search/lab, simulation, benchmarks, sandbox, pull requests.

**Evidence needed:** pinned candidate definition, reproducible benchmark, adversarial/failure tests, impact analysis, and explicit acceptance decision.

**Known boundary:** a generated design or catalog item is not an implementation.

### 2.15 External Systems & Tooling Intake

**Purpose:** Evaluate third-party tools without confusing catalog inclusion with adoption.

**Intended mechanism:** discover → identify exact upstream → inspect license/security/dependencies → quarantine → sandbox → test → independently verify → propose adapter → authorize admission → monitor upstream changes.

**Interfaces:** separate external systems candidate registry; GitHub/source metadata; SBOM/security scanners; sandbox; adapter contracts; evidence ledger.

**Initial state:** candidates are `UNASSESSED` until a specific review receipt changes their state.

## 3. Tools and integration families

The entries below are candidates to assess against existing capabilities, not an assertion that they are installed or connected.

| Family | Examples | How the family works | Integration boundary |
|---|---|---|---|
| Agent frameworks | OpenAI Agents SDK, LangGraph, Microsoft Agent Framework, AutoGen, CrewAI, Semantic Kernel | Model a task as agents, state transitions, tools, handoffs, and policies | Must route tool calls through VX; compare against existing agent fabric before adopting |
| Durable workflows | Temporal, n8n, Prefect, Airflow, Dagster, Argo Workflows | Persist job state, schedule/dispatch steps, retry failures, and record outcomes | Workflow registry + idempotency + authorization + run receipts |
| Web discovery | Firecrawl | Crawl or extract web content into structured data for downstream analysis | NEXENT discovery; capture URL, retrieval time, source attribution, and license constraints |
| Observability | OpenTelemetry, Prometheus, Grafana, Jaeger, Sentry, Loki | Instrument traces, metrics, logs, errors, and service health | OIF/event correlation; telemetry does not itself prove correctness |
| Policy and supply-chain | OPA, Sigstore/Cosign, SLSA, in-toto, Trivy | Evaluate policy, attest artifact origin/builds, sign artifacts, scan dependencies | VX action gate and evidence/provenance records |
| Search and data | Neo4j, Qdrant, OpenSearch, PostgreSQL, DuckDB, Iceberg | Store relationships, vectors, indexed documents, transactional data, analytics, or table snapshots | Canonical identity/provenance contracts; no source replacement without migration tests |
| Build and test | GitHub Actions, Dagger, BuildKit, Testcontainers, Nix, Renovate | Automate checks, create repeatable build environments, test dependencies, manage updates | Pinned commits, CI receipts, isolated integration tests, rollback |
| Model runtimes | Ollama, llama.cpp, vLLM, Transformers | Load, serve, or execute models across local and hosted compute | VLNS activation envelope; provider identity, model/version, limits, and receipts |
| Interoperability | MCP, OpenAPI, webhooks, gRPC, message brokers | Describe tool/API contracts and carry typed requests/events between systems | Adapter schemas, auth scopes, timeout/retry policy, trace IDs, replay behavior |
| Secrets and identity | Vault, workload identity, short-lived credentials | Issue and rotate scoped credentials and bind actions to workload identity | Least privilege; no secrets in source, prompts, or candidate intake records |
| Infrastructure | Docker, Podman, Kubernetes, Linux, Termux | Package and run services/processes in isolated or managed environments | Deployment manifests, resource limits, network policy, health checks, recovery tests |
| Test and simulation | Property-based tests, fuzzing, fault injection, digital twins | Generate edge cases, perturb dependencies, simulate failures, test recovery invariants | VV acceptance gates, replayable fixtures, recorded seeds and environments |
| Data lineage | Event sourcing, schema registries, CDC, lineage tools | Track changes, schema versions, data movement, and downstream impact | Event/state/ledger contracts and migration/compatibility tests |
| Business systems | CRM, billing, customer support, price monitoring | Capture leads, manage customers, calculate charges, monitor opportunities | VX business workflows; explicit consent, scopes, audit, and financial reconciliation |

## 4. Interface catalog — required contract for every connection

Every interface should be indexed with these fields:

- **Interface ID and name**
- **Producer → consumer** and the owning system on each side
- **Purpose and data classification**
- **Transport/protocol:** function/API, HTTP/OpenAPI, MCP, webhook, gRPC, queue, file, or database
- **Input/output schema** and version compatibility
- **Identity, authentication, authorization scope**
- **Timeout, retry, idempotency, rate/resource limits**
- **Correlation/trace ID and event/audit record**
- **Failure modes, circuit-breaker behavior, and recovery**
- **Security boundary and secrets handling**
- **Acceptance tests, replay fixtures, evidence URI/hash**
- **Lifecycle status:** `SPECIFIED`, `IMPLEMENTED`, `VERIFIED`, `LIVE`, `DEGRADED`, `UNKNOWN`
- **Owner, last verified revision/time, rollback/decommission path**

A declared interface must not be labelled `LIVE` until an authorized runtime probe or execution receipt proves connectivity for the named environment and revision.

## 5. Cross-system lifecycle

```text
DISCOVER
  → identify source and exact revision
  → register candidate + preserve provenance
  → quarantine and inspect
  → define contract, threat model, and acceptance tests
  → sandbox and test
  → independently verify evidence
  → submit proposal / pull request
  → authorized canonical admission
  → controlled VX execution
  → telemetry + event/ledger + replay
  → continuous revalidation or rollback
```

## 6. Evidence and status rules

- `SPECIFIED`: contract/design exists.
- `IMPLEMENTED`: code exists at a named revision.
- `VERIFIED`: named tests passed with inspectable receipts.
- `LIVE`: runtime connectivity/operation was proven in a named environment.
- `UNKNOWN`: evidence is missing, stale, conflicting, or not independently checked.
- `HOLD`: a required gate is not satisfied.
- `REJECTED`: a reviewed candidate failed explicit criteria.

Do not infer implementation from prose, status labels, a catalog row, a repository name, or an unrelated green CI run. Preserve existing source files and history; prefer additive records and reviewed pull requests.

## 7. Existing source documents

- [Master Index navigation](README.md)
- [Innovation Master Index](INNOVATION_MASTER_INDEX.md)
- [Innovation Operation Index](../innovation/INNOVATION_OPERATION_INDEX.md) — generated projection; edit its source catalogs, not the generated file.
- [Repository Federation Index](REPOSITORY_FEDERATION_INDEX.md)
- [Repository System Map](../canonical/REPOSITORY_SYSTEM_MAP_V1.md)
- [VX Universal Agent Runtime](../architecture/VX_UNIVERSAL_AGENT_RUNTIME_AND_ENGINEERING_FABRIC_V1.md)
- [Sovereign Tool Control Fabric](../tools/VAIXLNS_SOVEREIGN_TOOL_CONTROL_FABRIC_V1.md)
- [VLNS→VX Activation Bridge](../integration/VLNS_VX_ACTIVATION_BRIDGE_V1.md)
- [External Systems & Tooling Candidate Registry](../architecture/EXTERNAL_SYSTEMS_AND_TOOLING_CANDIDATE_REGISTRY_V1.md)


## 3. Ω Meta-Kernel

**Constitutional change control:** [Ω Meta-Kernel — Constitutional Change Control Specification v1](../architecture/OMEGA_META_KERNEL_CONSTITUTIONAL_CHANGE_CONTROL_V1.md)

This specification defines the proposed contracts for changing governance rules themselves: amendment classes C0–C5, non-amendable safety floor, independent review, federation message contracts, trust/knowledge sovereignty, append-only decision evidence, recovery, conformance levels M0–M6, and acceptance tests. It is an architecture specification; runtime enforcement remains unverified until implementation artifacts and tests demonstrate it.


## 4. Machine-readable contract draft

[Proposed JSON Schema: Meta-Kernel core contracts v1](../../schemas/meta-kernel/meta-kernel-contracts-v1.schema.json)

The draft defines four record families: federation messages, constitutional decision records, evidence records, and capability records. Its schema identifier currently uses a placeholder domain and must be replaced before treating it as a published stable contract. JSON syntax validation: passed; this does not yet prove semantic correctness or runtime enforcement.
