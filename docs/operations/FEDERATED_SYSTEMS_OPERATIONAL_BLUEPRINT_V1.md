# VAIXLNS Federated Systems — Engineering & Operational Blueprint v1

**Snapshot date:** 2026-10-15  
**Snapshot commit:** `52d1795e8550cd069ddb03cca45e573028115062`  
**Document state:** Engineering plan / evidence reconciliation; **not a production-readiness certificate**  
**Canonical authority:** `project.genome::v1.0.0` · `Ω0_GENESIS_CORE` · `Ω.000`

## 1. Purpose and non-negotiable boundaries

This document turns the existing architecture and repository evidence into one operating model: what each system owns, how data moves between systems, which interfaces are expected, how to start and test the reference surfaces, and what must still be closed before the federation can be called connected or production-ready.

It is additive. It does not replace `project.genome`, rewrite `Ω.000`, rename repositories, merge histories, or promote any proposal to canonical status. The repository and workflow snapshots below are pinned to their observed refs and timestamps; re-check source heads and CI before an admission decision.

Rules:

1. **One canonical authority:** VAIXLNS owns canonical identity, policy, registry, recovery, admission, and production authorization.
2. **Evidence before status:** a README, a green schema-validation workflow, or code in a repository is not by itself proof of a running service.
3. **Identity is explicit:** system names and repository names are different entities. Unknown identity mappings remain `HOLD`.
4. **Default deny across boundaries:** an unknown identity, contract, capability, signature, policy revision, or evidence reference blocks the edge.
5. **No silent data loss:** retain original files, source commit SHAs, event/evidence records, superseded candidates, and recovery paths.
6. **Execution is downstream of authorization:** NEXENT/NAXLNS can discover and propose; ARC-X can reconstruct and compile evidence-backed candidates; VX executes only a scoped, authorized request.
7. **Local reference operation is not production:** public network exposure, external model calls, remote activation, deployment, and irreversible publication require separate controls and fresh evidence.

## 2. Observed system inventory

### 2.1 Canonical and primary execution surfaces

| System / surface | Observed role and entry points | Evidence observed | Current treatment | Remaining gate |
|---|---|---|---|---|
| **VAIXLNS** — [repository](https://github.com/fisallllll280-code/VAIXLNS) | Canonical control plane; `project.genome`, `registry/omega/omega-000-master-index.json`, federation manifests, proof/admission checks, recovery, stage conformance | `project.genome` blob `7b8822cff6321d2b750aec030e29b928ed685940`; Repository Pulse passed on 2026-10-15; latest Federation Snapshot failed on 2026-10-15 | Canonical authority; implementation remains partial | Repair snapshot authentication and publication path; resolve identity blockers; connect and independently verify federation edges |
| **ARC-X Ω** — [canonical specification](https://github.com/fisallllll280-code/VAIXLNS/blob/main/docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md) | Source pinning, repository reconstruction, atomization, EIR, claim/evidence/proof-obligation separation, contradiction/gap/drift analysis, candidate compilation | The canonical ARC-X spec declares `SPECIFIED`, not production implementation | Specification / partial supporting tooling | Demonstrate one reproducible end-to-end compile from pinned repository evidence to an independently reviewable admission package |
| **VLNS candidate / NAXLNS** — [repository](https://github.com/fisallllll280-code/NAXLNS) | Current identity candidate for the VLNS model/knowledge activation boundary; root has README, repository contract, federation docs, conformance workflow | Latest observed NAXLNS conformance run passed on 2026-10-06, but the current main tree is documentation/contract-oriented; no model activation service or application entry point was established by this inventory | **Identity UNVERIFIED; runtime MISSING in inspected tree** | Resolve `VLNS ↔ NAXLNS`; inventory the intended service, API owner, deployable entry point, authentication and actual runtime evidence |
| **NEXNET candidate / NEXENT** — [repository](https://github.com/fisallllll280-code/NEXENT) | Discovery, research, synthesis, capability and architecture candidates; Python package `nexent`, Rust subtree, tests, CLI and optional local web surface | CI suites passed on main SHA `f62cf5920174551f9a8f88deb420f9515bedc284` on 2026-10-10; the CLI includes `status`, `demo`, `run`, `web` | Implemented discovery/reference baseline; **identity NEXNET ↔ NEXENT remains UNVERIFIED** | Establish the identity mapping independently; distinguish deterministic demo paths from live source discovery; pin provider/source adapters and prove their failure behavior |
| **VX** — [VX-runtime](https://github.com/fisallllll280-code/VX-runtime), [VX50_COMPLETE_BUILD](https://github.com/fisallllll280-code/VX50_COMPLETE_BUILD) | Execution boundary; policy-gated capability calls, event hash chain, replay and evidence | VX-runtime main has `vxruntime/core.py`, tests, and a conformance workflow; its main conformance run passed on 2026-10-10. VX remains a multi-repository system surface | Reference runtime implemented/tested; production deployment unverified | Reconcile stale specification-first entries with current source evidence; close/open-review machine-readable contract PR #2; prove integration with canonical policy and durable evidence |
| **VAIXLNS-unified** — [repository](https://github.com/fisallllll280-code/VAIXLNS-unified) | Integrated implementation surface; `main.py` smoke runner, `api/server.py`, boot/recovery/health/telemetry, workspace, activation bridge | Several main workflows passed on 2026-10-11/12; latest observed scheduled VX readiness and activation-matrix runs passed on 2026-10-12 | **PARTIAL integrated surface**, not a connected production federation | Re-run complete test suite on current pinned main; validate durable-store restart, authentication default, remote VLNS adapter and canonical ledger integration; keep public exposure disabled until hardened |
| **VX Agents Fabric** — [repository](https://github.com/fisallllll280-code/vx-agents-fabric) | Versioned specialist-agent routing, multi-mind reviews, workflow orchestration, provider factory, tool-control dispatcher, artifacts and failure memory | Test workflow passed on main SHA `f0b3374a4245a8d128afc4bf05303c27b59c23fb` on 2026-10-10 | Coordination scaffold with tested local behavior | Provider endpoints/credentials, repository read adapters, sandbox execution, durable shared ledger, policy binding and admission are not yet established as a production chain |
| **vaixlns-nexent-vx** — [repository](https://github.com/fisallllll280-code/vaixlns-nexent-vx) | Auxiliary capability/action-control integration candidate | External-boundary CI passed on main; PR #1 adds an action-control assurance gate and remains draft | Experimental integration surface | Review/merge only after validating that its contract duplicates neither VX-runtime nor the unified activation bridge; add cross-repository conformance evidence |

### 2.2 Supporting, historical, and experimental surfaces

| Surface | Observed condition | Engineering decision |
|---|---|---|
| **vaixlns-core** — [repository](https://github.com/fisallllll280-code/vaixlns-core) | README describes a full runtime, but the inspected main tree is small and does not contain the full architecture directory layout described by that README. The external-integration-boundary workflow passed; that does not verify the README's broader runtime claims. | Treat as a core-contract/reference candidate. Audit claim-to-file mapping before copying code or consolidating it. |
| **vaixlns-csd-kernel** — [repository](https://github.com/fisallllll280-code/vaixlns-csd-kernel) | Specialized LNS/CSD kernel surface with a test file and CI workflow; no proof of federation-level runtime integration observed | Keep isolated as a specialized kernel; require parser/invariant tests and a declared adapter before binding it into VX |
| **verbose-engine** — [repository](https://github.com/fisallllll280-code/verbose-engine) | Main SHA `ffe607b29d36cff6f05494f7ec3fd11f2395ec4b`; PR #7 adds a read-only structural audit on a branch, but the workflow failed during checkout before tests ran | Audit-only / not admitted. Do not claim the kernel was repaired or that audit tests passed. Diagnose checkout/access first, then validate source-preserving extraction |
| **VAIXLNS-Intent-to-Reality** — [repository](https://github.com/fisallllll280-code/VAIXLNS-Intent-to-Reality) | Current tree is documentation/workspace material; no executable runtime was established | Keep as the intent-to-execution contract lane until an implementation, tests and evidence package exist |
| **Historical and duplicate repositories** | The repository inventory contains multiple variants and even nonstandard artifact-like repository names | Do not bulk-merge, delete or infer ownership. Classify and reconcile each item by immutable source SHA, role, provenance and evidence |

**Identity warning:** there is no repository named exactly `VLNS` or `NEXNET` in the inspected account. The candidates are `NAXLNS` and `NEXENT`; their identity links are explicitly unresolved in the canonical four-system manifest. This is a hard admission gate, not a naming cleanup task.

## 3. Operating mechanism of each primary system

### VAIXLNS — control plane and evidence authority

**Input:** repository inventories, system/contract manifests, source revisions, policies, proof/evidence records and human authorization decisions.  
**Work:** validate canonical pointers and registry structure; compare declared identities and edges; apply admission policy; preserve lineage; expose read-only readiness reports; govern promotions.  
**Output:** an admission decision, a constrained authority grant (when separately authorized), a registry/recovery record and an immutable reference to evidence.  
**Must never do:** infer truth from a missing contradiction, use a candidate as authority, or silently write canonical state from an agent/model proposal.

Read-only local preflight:

~~~bash
python scripts/federation_preflight.py
python scripts/validate_four_system_federation.py
python scripts/validate_federation_contract_edges.py
python -m unittest tests.test_four_system_federation tests.test_federation_contract_edges tests.test_federation_preflight -v
~~~

Interpretation: a structurally valid preflight is **not** a connectivity check. The current federation contract says `connectivity_verified=false` and `runtime_observed=false`; the four defined cross-system edges are disabled.

### ARC-X Ω — source/evidence reconstruction and compilation

**Input:** immutable repository refs, file/blob hashes, contracts, tests, CI receipts and any runtime observations.  
**Work:** source-pin → reconstruct → atomize → type claims and facts → link evidence/provenance → detect contradiction/gaps/drift → emit proof obligations and counterexamples → produce a candidate design and verification plan.  
**Output:** an EIR/candidate bundle with source hashes, claim IDs, evidence references, assumptions, unresolved questions, tests and a recommendation such as `HOLD`, `REJECT` or `READY_FOR_REVIEW`.  
**Authority boundary:** ARC-X may not grant itself authority, promote its own output to canonical, or reinterpret missing evidence as success.

**Operational closure required:** one tested command/API must accept a pinned source manifest and emit deterministic JSON; the same source snapshot should reproduce the same structural output; source changes must change the digest; claims without admissible evidence must remain unverified; contradiction and negative cases must be covered by tests. Current canonical status remains `SPECIFIED` until this vertical slice and its evidence are reviewed.

### VLNS / NAXLNS candidate — model and semantic activation

**Intended role:** identify model/provider/capability profiles and return a signed activation receipt; it does not own canonical meaning or execution permission.

The schema/bridge reference in VAIXLNS-unified is `schemas/vlns-activation-envelope.schema.json` and `vlns/activation.py`. The intended envelope binds `activation_id`, provider/model/version, role, capability/tool/permission profiles, constraints, provenance, context digest, signature metadata and status. The context itself should not be copied into the envelope when a canonical digest is sufficient.

Required activation path:

1. VAIXLNS supplies the authorized activation policy and permitted scope.
2. VX/unified validates model identity, envelope schema, signature and allowlisted capabilities.
3. The remote activation service must return the exact activation ID and envelope digest.
4. VX records the validated receipt and evidence event.
5. Replay and independent conformance run before the edge can be admitted.

**Current blocker:** the canonical specification states that live external connectivity and identity mapping are unverified. NAXLNS currently exposes repository-level docs/contracts only in the inspected tree, not a service proven to implement the remote activation endpoint. Keep this edge disabled; mock-client tests do not prove live connectivity.

### NEXNET / NEXENT candidate — discovery and synthesis

**Input:** explicit goal/intent, pinned sources or user-provided data, context, bounded research permissions and target output schema.  
**Work:** parse intent → bind declared capability → run discovery/analysis → generate candidate → simulate/attack candidate → emit proof obligations and evidence lineage.  
**Output:** non-canonical candidate, report and provenance; never a canonical write or an execution grant.

Reference commands from the current NEXENT docs:

~~~bash
python -m pip install -e . pytest
python -m pytest -q
python -m nexent.cli status
python -m nexent.cli demo
python -m nexent.cli web --host 127.0.0.1 --port 8787
~~~

The `demo` path is a deterministic example, not evidence of live web/repository research. Keep the web service on loopback. Do not expose it publicly until authentication, authorization, TLS, rate/resource limits and network policy are tested. The CLI `web` entry point alone does not establish an external-source connector. Resolve the `NEXNET ↔ NEXENT` identity claim separately from this code evidence.

### VX — governed execution, observation and replay

**Input:** signed/scoped execution request from the authority boundary, stable request ID, immutable input digest, capability allowlist, policy revision and unexpired authorization/lease.  
**Work:** validate identity and policy → resolve capability → enforce resource/permission limits → execute → emit state/event receipts → verify ledger → replay original inputs → return result and evidence.  
**Output:** execution result and evidence receipt containing runtime/execution IDs, source and policy revisions, input/output hashes, status, event/trace digest, replay result and observation time.  
**Must reject:** missing authority, unknown capability/contract, expired or revoked lease, unverified proof, mismatched digest or invalid policy revision.

The current VX-runtime conformance workflow compiles `vxruntime`, runs pytest, executes `math.add`, checks replay and ledger integrity, and tests the external-integration boundary. Run from a pinned VX-runtime checkout:

~~~bash
python -m pip install pytest
python -m compileall -q vxruntime tests
python -m pytest -q
~~~

The latest observed main conformance workflow passed on 2026-10-10. This supports a tested reference core, not production-scale reliability or a currently deployed service. Do not mark VX `RUNNING` without a fresh health observation from an admitted instance.

### VAIXLNS-unified — integrated reference runtime and API surface

**Work:** run the current smoke path; persist local events/snapshots; provide health/status endpoints; coordinate workspace/activation and recovery components; retain event integrity metadata.  
**Smoke command:**

~~~bash
python main.py
~~~

**Local API (loopback only during validation):**

~~~bash
export VAIXLNS_DB_PATH=var/vaixlns/events.db
export VAIXLNS_API_TOKEN='<load-from-a-secret-manager>'
uvicorn api.server:app --host 127.0.0.1 --port 8080
~~~

Documented endpoints include `GET /health`, `GET /status`, `GET /events`, `POST /events`, `POST /snapshots`, and `POST /federation/probe`. Check the current server implementation before relying on any additional workspace routes.

**Security blocker:** `api/server.py` currently treats a request as authorized when `VAIXLNS_API_TOKEN` is unset. That behavior can be acceptable only for a tightly loopback-bound development harness; it is not an acceptable default for a remotely exposed or production service. Before non-loopback binding, change the deployment configuration/authorization guard to fail closed, add auth tests for absent/wrong/correct tokens, and verify that probe/mutation routes cannot be reached unauthenticated. Use a durable protected volume for SQLite and test process restart, corruption detection and recovery.

### VX Agents Fabric — multi-agent workflow coordination

**Input:** a workflow ID and goal plus version-pinned agent roles, task budgets/deadlines, output schemas, evidence obligations and explicitly available context.  
**Work:** route research/engineering/financial/security/proof tasks to configured adapters; record agent-version and input lineage; collect independent reviewer results; return `HOLD` when a required role/provider is missing; create artifacts and failure records.  
**Output:** workflow report and candidate artifact, never canonical adoption or production authority.

Test command:

~~~bash
PYTHONPATH=src python -m unittest discover -s tests -v
~~~

Example bounded CLI:

~~~bash
PYTHONPATH=src python -m vx_agents_fabric.cli --goal "Design and validate an engineering capability" --workflow-id WF-ENG-001 --output reports/WF-ENG-001.json
~~~

The OpenAI-compatible adapter is opt-in. Configure model IDs/endpoints/credentials only through protected runtime environment or a secret manager. A chat adapter does not itself provide web search, GitHub credentials or a secure code sandbox. Local hash-linked receipts and file-backed ledgers must be integrated with the canonical VAIXLNS evidence ledger and independently replayed before production admission.

## 4. Required cross-system interfaces

All calls across system boundaries must use declared, versioned adapters. Direct cross-repository imports and free-form agent-to-agent calls are not federation protocols.

### 4.1 Common envelope

Each cross-system message should contain at minimum:

- `schema_version`, `contract_id`, `message_id`, `correlation_id`, `idempotency_key`;
- `source_system_id`, `target_system_id`, source repository and immutable `source_revision`;
- `issued_at`, `expires_at` where applicable, and policy/contract revision;
- canonicalized `payload_sha256`, provenance references and evidence references;
- capability scope, data classification and authority grant reference when the action requires authority;
- signature algorithm, key reference and signature for security-sensitive activation/execution messages.

Never include raw API tokens, signing secrets, provider credentials or customer data in the envelope or CI artifacts. Store key references; perform secret resolution inside the trusted runtime. Every receiver validates the schema, digest, signature, expiry, sender identity, target identity and policy binding before action.

### 4.2 Contract edges to implement

| Edge ID | Direction | Interface / purpose | Required fields/evidence | Current state |
|---|---|---|---|---|
| `FED.VLNS.VAIXLNS.KNOWLEDGE.001` | VLNS → VAIXLNS | Knowledge observation only | source revision, content digest, provenance, observed time | `BLOCKED_IDENTITY`, disabled |
| `FED.NEXNET.VAIXLNS.DISCOVERY.001` | NEXNET → VAIXLNS | Candidate proposal only | source revision, candidate digest, provenance, proof obligations | `BLOCKED_IDENTITY`, disabled |
| `FED.VAIXLNS.VX.EXECUTION.001` | VAIXLNS → VX | Scoped execution request | decision ID, authority grant, capability scope, input digest, policy revision | `SPECIFIED_NOT_CONNECTED`, disabled |
| `FED.VX.VAIXLNS.EVIDENCE.001` | VX → VAIXLNS | Execution evidence receipt | execution ID, source revision, input/output digests, test receipt, observed time | `SPECIFIED_NOT_CONNECTED`, disabled |

The authoritative current source for these statuses is `registry/federation/federation_contract_edges.v1.json`. Do not manually mark an edge enabled. Admission requires endpoint identity, protocol conformance, negative tests, durable receipt ingestion, replay and independent review.

### 4.3 Interface ownership

- **Repository source adapters:** read-only acquisition; return commit SHA, blob digests, and explicit inaccessible/truncated states.
- **ARC-X output adapter:** emits an evidence-backed candidate package. It cannot set canonical state or grant capability.
- **VLNS activation adapter:** validates signed model activation and remote receipt; activation alone does not grant execution.
- **VX execution adapter:** accepts only an authorized, bounded request; emits receipt and state evidence.
- **Agent dispatch adapter:** pins role/version and limits per-task tools, input size, call count, deadline and output schema.
- **Evidence ingestion adapter:** validates event identity/digests, idempotently stores receipt, and rejects duplicate-ID/different-content conflicts.
- **Health/telemetry adapter:** reports instance ID, source revision, readiness, lease/heartbeat, dependency health, queue, latency, error counters and last successful replay. A process being alive is not readiness.
- **UI/API layer:** displays source-backed statuses and evidence URLs; must not create a new authority path around VAIXLNS.

## 5. End-to-end operational sequence

The complete desired vertical slice is:

~~~text
Repository snapshot / intent
  → source pins + digests
  → NEXENT / VLNS candidate (read-only discovery)
  → ARC-X reconstruction + typed evidence + proof obligations
  → VAIXLNS identity / policy / admission review
  → bounded VX request with explicit authority
  → isolated execution + health/limits
  → evidence receipt + durable event ledger
  → independent replay + conformance
  → VAIXLNS admission decision
  → monitored Stage rollout + rollback evidence
~~~

Each transition produces an inspectable artifact with a stable ID, source revision, hash, outcome, and evidence references. A missing adapter or unresolved identity yields `HOLD`; timeout yields a recorded failure; invalid signature/digest yields `REJECT` or quarantine according to policy. No transition silently skips missing research, failed tests, or absent parent-mind review.

### Lifecycle gates

1. **G0 — Inventory freeze:** snapshot exact refs, default branches, contracts, entrypoints, dependencies, tests, CI and license/security posture.
2. **G1 — Identity and contract:** record canonical system ID separately from repo name; resolve aliases only with evidence; validate request/receipt schemas.
3. **G2 — Local functionality:** execute each repository's unit and negative tests on pinned SHAs.
4. **G3 — Isolated integration:** connect only local/read-only test adapters; test unknown identity, invalid signature, policy mismatch, timeout, duplicate request, provider unavailable and receipt-store failure.
5. **G4 — Replay and recovery:** kill a worker during a task, restart from the last verified checkpoint, replay the original input and compare digests; preserve failed artifacts.
6. **G5 — Governance admission:** attach source, test, security, replay and deployment evidence; independent reviewer checks the exact commit and environment; explicit authority grants only the bounded scope.
7. **G6 — Stage operation:** startup/health/lease, signed request, routing, controlled isolation, recovery, re-route, telemetry and rollback. Save evidence externally.
8. **G7 — Production decision:** separate approval after authentication, secrets, persistence, observability, backup/restore, capacity, security and load objectives are demonstrated.

## 6. Highest-priority blockers and actions

### P0 — Correct the evidence/snapshot workflow

Latest run: [VAIXLNS Federation Snapshot #38698964074](https://github.com/fisallllll280-code/VAIXLNS/actions/runs/38698964074). The capture report records multiple `CAPTURE_FAILED` results because `git clone` could not obtain GitHub credentials (`could not read Username for 'https://github.com'`). The job then attempted to push an archive commit directly to `main`; GitHub rejected that push because the target ref is protected and Code Scanning results were still awaited.

**Fix path:**
1. For each source repo, prove read access using the intended GitHub App/token and pass credentials to the actual clone/API operation; never print the token.
2. Record each inaccessible repo as `ACCESS_UNAVAILABLE` (with redacted diagnostic and exact URL), not as an apparently complete snapshot.
3. Write a manifest only after per-source status has been recorded; mark the overall capture incomplete if required sources are missing.
4. Publish the bundle as a workflow artifact first, then create/update a dedicated bot branch and pull request for durable archival. Do not bypass protected `main`.
5. Add tests for public/private/missing repo access, token absence, partial capture, no-op capture, artifact generation and branch-protected publish failure.

### P0 — Resolve identity before connecting the four-system graph

- Obtain authoritative evidence for `VLNS ↔ NAXLNS`.
- Obtain authoritative evidence for `NEXNET ↔ NEXENT`.
- Keep both edges disabled until accepted by canonical review.
- Do not create a new repo named VLNS/NEXNET as a shortcut; first decide whether the historical identity is a repo alias, a separate system or a successor, and record the relation without losing history.

### P1 — Make the runtime surface safe by default

- Change exposed API authorization to fail closed when deployment auth is missing; test all mutation/probe routes.
- Pin the API to loopback for development; use TLS, gateway auth, rate limits, network policy and protected secrets before remote binding.
- Set durable DB/ledger paths, test restart/recovery and corruption handling, and define backup/restore procedure.
- Connect runtime evidence to the canonical ledger through an idempotent adapter; process-local receipts are insufficient.
- Test the actual externally deployed activation service separately; mocked activation success is not connectivity proof.

### P1 — Close and sequence existing branches/PRs

- [VAIXLNS PR #117](https://github.com/fisallllll280-code/VAIXLNS/pull/117) is the current supervised-runtime bootstrap slice. Its description reports seven passing tests, a stopped final state, hash-chain verification and one bounded recovery, plus successful triggered gate runs on its feature head. It remains draft/unmerged; review its diff and rerun on the current head before merge. The subprocess fixture is not an OS-enforced sandbox and must not be promoted as production deployment.
- [VAIXLNS PR #112](https://github.com/fisallllll280-code/VAIXLNS/pull/112) and [#113](https://github.com/fisallllll280-code/VAIXLNS/pull/113) form a stacked ARC-X interoperability/security chain; merge prerequisites must be handled in order.
- [VAIXLNS-unified PR #55](https://github.com/fisallllll280-code/VAIXLNS-unified/pull/55), [#53](https://github.com/fisallllll280-code/VAIXLNS-unified/pull/53), and [#52](https://github.com/fisallllll280-code/VAIXLNS-unified/pull/52) address source connectors, knowledge/console and bounded model adapter work. Do not equate open PRs with merged integration.
- [VX-runtime PR #2](https://github.com/fisallllll280-code/VX-runtime/pull/2) remains the runtime-contract review surface.
- [NEXENT PR #14](https://github.com/fisallllll280-code/NEXENT/pull/14) covers the RIRF repair boundary; validate compatibility with the canonical source/evidence gates before adoption.
- [vx-agents-fabric PR #8](https://github.com/fisallllll280-code/vx-agents-fabric/pull/8) and [vaixlns-nexent-vx PR #1](https://github.com/fisallllll280-code/vaixlns-nexent-vx/pull/1) remain draft/experimental integration work.

No bulk merge is appropriate. Each PR must be reviewed for base branch, dependencies, tests, source preservation, contract overlap and exact evidence.

### P1 — Reconcile claim-to-code mismatches

Audit `vaixlns-core` README promises against actual files. Audit CSD/DSL source before importing it into any runtime. For `verbose-engine`, PR #7's audit workflow failed at GitHub checkout; its tests were skipped. Fix checkout/access and obtain a green independent run before making structural conclusions from its script.

### P2 — Demonstrate the complete vertical slice

Implement one end-to-end candidate path with local or mock adapters first, but make test boundaries explicit:

- candidate from pinned source;
- ARC-X-style evidence record with provenance and proof obligations;
- explicit VAIXLNS hold/admit result;
- one authorized VX execution with strict capability allowlist;
- durable evidence receipt and idempotent retry;
- replay equals original output for deterministic fixtures;
- restart/recovery scenario;
- all external calls remain disabled by default.

Only after the local slice passes should live model/VLNS connectivity be activated in a separate, permissioned environment.

## 7. Definition of operational readiness

The federation is **not READY** until all required criteria below are evidenced at pinned commits:

- [ ] Canonical genome/index checks pass without modifying the canonical pointers.
- [ ] VLNS and NEXNET identity mappings have approved evidence, or the corresponding edges remain explicitly blocked.
- [ ] Every enabled edge has a versioned schema, adapter, contract tests, negative tests and an owner.
- [ ] Every repository has a declared entry point, reproducible install/test instructions and current CI evidence.
- [ ] The whole local vertical slice passes across adapters at pinned source SHAs.
- [ ] The request path rejects unknown identity/capability, absent authority, expired lease, altered digest, invalid signature and incompatible policy.
- [ ] Every successful, failed, timed-out or recovered operation has a durable, idempotent receipt; no missing evidence is silently skipped.
- [ ] Replay/recovery is verified independently from the producing worker.
- [ ] API/model/web surfaces fail closed and remain loopback-only until security gates pass.
- [ ] Snapshot capture records private/inaccessible sources honestly and uses artifact/PR publication compatible with branch protection.
- [ ] The Stage checklist, rollback revision, backup/restore and incident procedure are complete.
- [ ] Production authority is granted separately and scoped to a specific revision, environment, capabilities and expiry.

## 8. Canonical sources to keep synchronized

This blueprint is a cross-reference, not a replacement, for the existing source documents:

- `project.genome` and `registry/omega/omega-000-master-index.json`;
- `registry/federation/four_system_unification.v1.json` and `registry/federation/federation_contract_edges.v1.json`;
- `docs/indexes/FOUR_SYSTEM_RECONCILIATION_V1.md`;
- `docs/indexes/REPOSITORY_RUNTIME_STATUS_V1.md`;
- `docs/operations/FEDERATED_RUNTIME_BOOTSTRAP_AND_CAPACITY_PLAN_V1.md`;
- `docs/operations/FEDERATED_ENGINEERING_DEPLOYMENT_V1.md`;
- `docs/operations/VX_STAGE_RUNTIME_RUNBOOK_V1.md` and `docs/operations/VX_STAGE_RELEASE_CHECKLIST.md`;
- `docs/integration/VLNS_VX_ACTIVATION_BRIDGE_V1.md`;
- `docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md`.

**Completion rule:** this document itself completes only the cross-system planning/reconciliation artifact. It does not complete the missing live integrations, resolve the two identity mappings, repair snapshot automation, merge open PRs, or certify production.
