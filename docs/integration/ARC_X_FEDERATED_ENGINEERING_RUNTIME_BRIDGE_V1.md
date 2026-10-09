# ARC-X Ω — Federated Engineering Compute and VX Server Bridge v1

**Status:** SPECIFIED — integration contract, not proof of a live deployment  
**Canonical owner:** VAIXLNS  
**Evidence and reconstruction:** ARC-X Ω  
**Runtime, routing, execution and replay:** VX  
**Independent verification:** VV / verification fabric  
**Research and candidate synthesis:** NEXENT, subject to verified identity and adapter contracts  
**Authority anchor:** Ω0_GENESIS_CORE  
**Registry:** Ω.000  
**Parent contracts:** docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md; deploy/federation/INDEX_RECOVERY_RUNTIME_PROTOCOL.md; docs/UNIVERSAL_VX_INTEROPERABILITY.md; docs/operations/FEDERATED_RUNTIME_BOOTSTRAP_AND_CAPACITY_PLAN_V1.md; docs/architecture/VAIXLNS_SYSTEM_MEMORY_INDEX_AND_LANGUAGE_FABRIC_V1.md

> This contract defines how ARC-X should connect evidence-backed engineering tasks to eligible VX execution workers. It does not claim that a production endpoint, GPU pool, remote physics solver, or multi-node federation is currently connected.

## 1. Objective

Join system architecture, mathematical reasoning, numerical computation, software engineering, and physics simulation through a single typed task contract without collapsing their different correctness criteria.

The bridge SHALL improve integration quality and measured throughput through:
- capability-aware routing across eligible workers;
- parallel execution of independent tasks and dependency-aware scheduling;
- reuse of immutable, content-addressed artifacts;
- bounded retries, queue backpressure, checkpoints, and safe failover;
- reproducible numerical and simulation environments;
- evidence-linked verification and independent replay;
- an auditable path from candidate → proof obligations → governed admission → VX execution → observed result → ARC-X reconstruction.

No speedup is presumed. Improvements must be measured against a recorded baseline using equivalent tasks, outputs, and verification thresholds.

## 2. Authority and responsibility boundaries

~~~text
NEXENT candidate / authorized source inputs
                  |
                  v
R2: pinned retrieval + provenance + security screening
                  |
                  v
ARC-X: typed EIR + claims + assumptions + proof obligations
                  |
                  v
VAIXLNS policy / identity / licensing / privacy / admission gate
                  |
                  v
VX scheduler + capability router + resource and budget controls
                  |
        +---------+----------+-----------+----------+
        |                    |           |          |
        v                    v           v          v
  Math workers       Numerical workers  Software   Physics / CAE
  exact/ symbolic    CPU/GPU/HPC        build/test solvers/simulators
        |                    |           |          |
        +--------------------+-----------+----------+
                             |
                             v
             execution receipts + raw artifacts
                             |
                             v
             VV independent verification / R4
                             |
                             v
       VAIXLNS governance decision (separate authority)
                             |
                             v
                  Ω.000 evidence-backed update
                             |
                             v
                ARC-X observed-reality replay
~~~

- **VAIXLNS** owns canonical identity, policy, admission, and registry updates.
- **ARC-X** compiles and reconciles evidence; it cannot grant execution or canonical-write authority.
- **VX** owns task routing, execution isolation, state/events, worker eligibility, replay, and runtime admission.
- **VV / independent verification fabric** validates the declared proof obligations; the producer must not be its sole verifier for consequential claims.
- **NEXENT** may propose candidates and research results; generated content remains untrusted until screened and evaluated.
- **Worker servers** advertise capabilities and evidence contracts, not their own authority. A healthy or reachable server is not automatically trusted.

## 3. Federated server planes

### 3.1 Control plane — VAIXLNS
Stores canonical policies, known system identities, registered worker certificates/keys, approved capabilities, resource budgets, and admission decisions. Replication improves availability only when all replicas follow the same versioned policy and authority rules. A replica may not invent or silently diverge from canonical policy.

### 3.2 Runtime plane — VX
Provides the logical operations: **register_worker**, **heartbeat**, **plan_task**, **submit_task**, **inspect_task**, **cancel_task**, **capture_execution_evidence**, **replay_task**, and **isolate_worker**. HTTP, gRPC, queue, or CLI are transport choices; all transports MUST preserve the same contract semantics.

### 3.3 Compute plane
Workers are registered by capability and hardware profile. Candidate pools:
- CPU: parsing, symbolic orchestration, compilers, test suites, graph algorithms, and CPU numerical workloads.
- GPU/accelerator: measured model inference, tensor workloads, embeddings, and compatible numerical kernels.
- High-memory: large graph/index processing and workloads with verified memory requirements.
- Specialized engineering: build systems, CAD/CAE, finite-element, computational-fluid-dynamics, circuit, control, and domain-specific solvers, but only when a declared adapter and its conformance tests exist.
- Independent verification: implementations or evidence paths sufficiently distinct from the producer to reduce common-mode failure.

Listing a pool is not proof that the hardware or any specialist solver is provisioned.

### 3.4 Evidence plane
Stores immutable input snapshots, content hashes, task envelopes, dependency locks, solver/model versions, seeds, stdout/stderr or structured logs subject to redaction, raw results, verifier reports, policy versions, and state-transition events. Secret values MUST be excluded; use secret references and redacted audit markers instead.

## 4. Typed engineering task envelope

A task MUST declare its domain and correctness contract before scheduling. Recommended schema is **schemas/arcx-vx-engineering-task.schema.json**.

Required logical fields:
- **schema_version**, **task_id**, **idempotency_key**, **parent_task_id**, **created_at**, **deadline**;
- **source_revision**, **input_artifact_hashes**, **eir_ref**, **claim_refs**, **lineage_refs**;
- **domain**, **operation**, **required_capabilities**, **input_schema**, **output_schema**;
- **assumptions**, **constraints**, **proof_obligations**, **verification_profile**;
- **resource_request** including CPU, RAM, accelerator class, disk, wall time, and concurrency;
- **security_class**, **data_residency**, **license_constraints**, **network_policy**;
- **reproducibility** including environment/image digest, dependency lock, random seed policy, and deterministic-mode requirement;
- **execution_mode** such as ANALYZE, SIMULATE, TEST, or separately authorized EXECUTE;
- **policy_version**, **authorization_ref**, and expiry.

Unknown required fields, unknown capabilities, unresolved identity, invalid policy versions, or missing mandatory provenance MUST fail closed.

The envelope is a request, not proof and not authorization. A worker MUST receive only the minimal data and capability scope required for the task.

## 5. Domain-specific correctness contracts

### 5.1 Mathematics
Each mathematical task declares its representation and acceptance criteria:
- exact symbolic result vs floating-point approximation;
- domain, assumptions, variable constraints, and singularity/branch conditions;
- units/dimensions where quantities are physical;
- proof strategy or verification mechanism;
- numeric tolerances only where exact proof is not required.

Exact symbolic transformations SHOULD preserve expression trees and normalization version. A numeric spot-check may find a counterexample but cannot by itself prove a general theorem. For high-consequence claims, require an independent proof checker, a trusted CAS/kernel, or a clearly bounded validation method.

### 5.2 Numerical and scientific computing
Record algorithm, implementation version, compiler/runtime, library versions, precision, device, reduction mode, seed, tolerances, conditioning assumptions, convergence criterion, and residual/error metrics. Floating-point computations may vary with processor, compiler, parallel reduction order, and library. Bitwise reproducibility must be requested and verified where required; otherwise define acceptable numerical equivalence explicitly.

### 5.3 Software engineering
Record repository and pinned commit, patch digest, dependency lock, build environment, test selection, coverage scope, static/security scan versions, and rollback strategy. Passing unit tests does not prove an architecture claim; compilation, tests, static analysis, security review, and runtime verification are separate evidence items. Generated patches remain candidates and must never self-merge into protected branches.

### 5.4 Physics and engineering simulation
Before running a simulation, require:
- model equations and model/version identifier;
- system boundaries, geometry/mesh digest where relevant, initial and boundary conditions;
- material/property tables and source/licence provenance;
- unit system and dimensional checks;
- solver, discretization, time step, tolerances, convergence status, and numerical stability conditions;
- declared conservation/invariant checks where applicable (for example mass, energy, charge, momentum);
- validation/calibration evidence and known model limitations;
- sensitivity/uncertainty plan for claims that depend materially on parameters.

A converged solver run is not automatically evidence that the physical model is valid. Compare against analytic cases, controlled experiments, benchmark datasets, or independent solvers as appropriate. Real hardware, robotics, industrial control, vehicles, and other physical actuators default to OBSERVE / SIMULATE; real-world actuation requires a separate capability grant and safety contract.

## 6. Safe scheduler and measured acceleration

Scheduling follows a two-stage policy.

### Stage A — hard eligibility gates
Reject a worker before ranking if any of the following fails:
- verified worker identity and allowed system mapping;
- capability and tool/solver compatibility;
- signed request/receipt validation and authorization scope;
- security, privacy, residency, and licensing constraints;
- resource fit, healthy lease, and non-isolated status;
- environment and proof requirements;
- required verifier independence;
- data locality and allowed network egress.

### Stage B — constrained ranking
Among eligible workers, estimate:
- queue wait and end-to-end latency by task class;
- resource fit and measured service time;
- data-transfer and cache-warmup cost;
- failure-domain concentration and recovery cost;
- budget/cost and deadline risk;
- verification workload and reproducibility requirements.

Do not use one universal “fastest” score. Preserve a policy explanation for the selected route and alternatives considered.

### Throughput mechanisms
- Build a DAG from task dependencies; parallelize only independent nodes.
- Cache immutable artifacts using a key that includes input hashes, code/solver version, environment, parameters, policy-relevant inputs, and seed. Do not cache across incompatible privacy or authorization scopes.
- Use batching only where task semantics and numerical acceptance rules allow it.
- Apply bounded retries with exponential backoff, queue limits, deadlines, circuit breakers, and cancellation.
- Retry only idempotent tasks or tasks with an explicit duplicate-side-effect defense.
- Checkpoint long simulations and distributed computations using versioned, integrity-checked checkpoints.
- Isolate unhealthy workers and reroute only eligible, safe-to-replay tasks.
- Avoid sending every intermediate token or large tensor through the control plane; workers should exchange large immutable artifacts through authorized artifact storage, with digest references in the ledger.
- Profile before adding GPUs or nodes. Parallelism may lose to serialization, communication, synchronization, memory bandwidth, licensing, or verification overhead.

## 7. Task lifecycle and server states

Task lifecycle:
**DRAFT → VALIDATED → AUTHORIZED → QUEUED → DISPATCHED → RUNNING → RESULT_CAPTURED → VERIFIED / INCONCLUSIVE / FAILED → GOVERNANCE_PENDING → ADMITTED / REJECTED**

Worker connection lifecycle:
**DISCOVERED → CONFIGURED → REACHABLE → IDENTITY_VERIFIED → CONTRACT_CONFORMANT → ADMITTED → ACTIVE**

Exceptional states include DEGRADED, ISOLATED, QUARANTINED, EXPIRED, and REVOKED.

Reachability never skips identity verification. A timeout, missing receipt, signature/digest mismatch, invalid lease, failed integrity check, or evidence-store failure MUST NOT yield VERIFIED, ADMITTED, or RUNNING for an unverified task. If a worker completes but its evidence cannot be durably acknowledged, record RESULT_CAPTURED_EVIDENCE_PENDING; do not silently report success.

Every transition records previous state, next state, reason code, timestamp, actor/worker identity, policy version, task/envelope digest, and linked evidence.

## 8. Logical API contract

The transport may vary; the bridge should expose equivalent operations:

- **POST /v1/engineering/tasks** — validate envelope and create a task; does not imply execution.
- **GET /v1/engineering/tasks/{task_id}** — state, route explanation, evidence references.
- **POST /v1/engineering/tasks/{task_id}/cancel** — request cancellation subject to capability and task state.
- **POST /v1/engineering/tasks/{task_id}/verify** — request the independent verification plan.
- **GET /v1/engineering/workers** — return only registered workers and their declared status/capabilities, with appropriate access controls.
- **GET /health/live** — process liveness only.
- **GET /health/ready** — readiness for its declared service contract, excluding claims of semantic correctness.

These are proposed paths, not claims that endpoints currently exist. Health routes must not reveal secrets, internal topology, or sensitive worker data.

The reference client is scripts/arcx_vx_bridge.py. Its validate command uses no network; submit requires an operator-configured endpoint and separate request-signing and receipt-verification keys of at least 32 bytes, plus a bearer token. It enforces HTTPS except explicitly enabled loopback tests, signs the canonical task envelope with HMAC-SHA256, and verifies a receipt bound to the exact task ID and digest. A valid receipt is only an acknowledgement of RECEIVED/QUEUED/PENDING_VERIFICATION/BLOCKED/REJECTED; it never means VERIFIED or ADMITTED. The server must implement the matching request/receipt protocol and independently validate the JSON Schema, policy, authorization, identity, and signature. The response schema is schemas/arcx-vx-engineering-receipt.schema.json. Its response_signature is HMAC-SHA256 over canonical JSON of the receipt with response_signature omitted, using the separate receipt-verification key. The request signature is HMAC-SHA256 over canonical JSON of the request envelope before adding the signature, using the request-signing key. Request authentication, TLS, scoped authorization, rate limits, request-size limits, deadlines, replay protection, audit events, and secret-manager integration are mandatory before exposing endpoints beyond loopback/private test infrastructure.

## 9. R2 / ARC-X / R4 / VX handshake

1. **R2 retrieval:** pin revision and configuration, hash source artifacts, store retrieval receipt, classify external content as untrusted, and preserve each source in the governed memory/index lineage defined by docs/architecture/VAIXLNS_SYSTEM_MEMORY_INDEX_AND_LANGUAGE_FABRIC_V1.md.
2. **ARC-X compile:** normalize source evidence into EIR; extract claims, assumptions, conflicts, units, dependencies, and explicit proof obligations.
3. **Policy prepare:** VAIXLNS resolves system identity, licenses, privacy, allowed capabilities, resource/cost bounds, and authorization reference.
4. **VX plan:** scheduler returns an explainable route plan; no worker runs until required admission passes.
5. **Execute in isolation:** worker verifies task digest and scope, runs in the declared sandbox, and emits structured output plus environment receipt.
6. **Evidence commit:** persist the input/output digests, execution trace, environment, metrics, failure state, and previous state before reporting a completed result.
7. **R4 / VV verification:** check schema, contract invariants, mathematical/numerical obligations, domain-specific tests, and reproducibility. Use independent paths for high-impact claims.
8. **Governance:** authority gate decides whether an output may be accepted, published, indexed, or executed further. The producer and ARC-X cannot approve themselves.
9. **ARC-X reconstruction:** compare expected architecture with observed execution; register drift, missing obligations, latency/resource measurements, and unresolved conflict.
10. **Ω.000 update:** write only through the canonical admission path, with explicit decision and evidence references.

## 10. Evidence and receipt minimum

An execution receipt MUST include:
- **receipt_id**, **task_id**, **worker_id**, **worker_identity_version**;
- **request_digest**, **input_artifact_digests**, **output_artifact_digests**;
- **runtime_image_or_environment_digest**, **solver_or_tool_versions**;
- **started_at**, **finished_at**, **exit_state**, **failure_reason**;
- **resource_usage**, **latency_ms**, **queue_wait_ms**, **retry_count**;
- **seed**, **precision**, **tolerance**, and **convergence** fields when applicable;
- **verification_profile**, **verification_result_refs**, **policy_version**;
- **previous_event_digest** or equivalent tamper-evident event linkage;
- explicit state among PASS, FAIL, INCONCLUSIVE, PENDING, or NOT_APPLICABLE for each obligation.

A missing measurement is MISSING or NOT_RECORDED, never inferred as zero. A worker-signed receipt proves attribution to that worker identity, not that the result is true; semantic correctness still requires verification.

## 11. Failure isolation and recovery

Required negative paths:
- network unavailable or timeout;
- worker identity or certificate mismatch;
- signed envelope or receipt digest mismatch;
- worker lost lease or became isolated mid-task;
- stale result from an earlier task version;
- duplicate request with the same idempotency key;
- missing artifact, corrupted checkpoint, or evidence-store outage;
- policy or authorization revoked while queued;
- numerical non-convergence, solver crash, or failed invariant;
- a result that passes schema but fails the verification contract.

For each case, define deterministic state transition, retry eligibility, maximum retries, cancellation behavior, retained evidence, alert condition, and rollback/no-promotion rule. Preserve failed task evidence for diagnosis without promoting its outputs.

## 12. Performance and accuracy acceptance gates

Record a baseline on the same pinned task suite before claiming an improvement. Report each task class separately:
- median and p95 end-to-end latency;
- queue wait, execution, data transfer, and verification time;
- completed and accepted-and-verified tasks per second;
- cost per accepted-and-verified task;
- CPU/RAM/GPU utilization and data movement where measurable;
- cache hit rate and cache invalidation correctness;
- solver convergence, residual/error, invariant failures, and reproducibility rate;
- provenance completeness and verification failure rate;
- throughput scaling at 1, 2, 4, and 8 eligible workers;
- timeout, retry, duplicate-effect, evidence-loss, and recovery rates.

Compare the same workload, output quality, model/solver revision, verification bar, and resource budget. Repeat runs and report variability. Speed cannot compensate for lower correctness, missing provenance, or a weaker verification threshold.

### Minimum acceptance tests
1. No contradiction detection result can itself grant admission.
2. No unresolved identity or worker-policy mismatch can be routed.
3. Different physical dimensions cannot be compared as the same metric without a valid conversion and semantic match.
4. Different math/simulation environments produce distinct execution provenance.
5. A duplicate request does not create duplicate side effects.
6. Worker isolation blocks new privileged dispatch and preserves pending evidence.
7. A failed or unavailable R4 verifier leaves the task pending or blocked.
8. A stale policy invalidates or triggers reauthorization before dispatch.
9. Corrupted outputs/checkpoints fail integrity verification.
10. A mathematically plausible but unproved claim remains a candidate, not a theorem.
11. A converged physics simulation without model validation remains limited-evidence, not physical truth.
12. Replaying the same pinned task either reproduces equivalent results under declared criteria or records an explicit reproducibility failure.
13. A changed canonical policy causes re-evaluation without rewriting the historical decision.
14. The runtime can recover the task ledger and rebuild task state from durable evidence.
15. No worker, ARC-X component, generated artifact, or verifier can self-promote to canonical authority.

## 13. Staged implementation

- **B0 — Inventory:** map existing schemas, VX Stage router, admission gate, evidence schemas, and existing adapter implementations; do not duplicate working interfaces.
- **B1 — Contract:** validate the task/receipt schemas and lifecycle; add negative tests.
- **B2 — Local vertical slice:** route one harmless mathematical or software verification task through a local registered worker with immutable inputs and an evidence receipt.
- **B3 — Domain adapters:** add math, numerical, software, and physics adapters one at a time, each with domain fixtures and explicit dependencies.
- **B4 — Independent verification:** connect the R4/VV verification contract and ensure fail-closed behavior.
- **B5 — Multi-worker federation:** enable bounded parallelism, resource-aware scheduling, idempotency, caching, and fault-injection tests.
- **B6 — Remote endpoint admission:** configure a known operator-supplied endpoint; verify identity, TLS, contract, receipt semantics, security, persistence, and recovery. Do not scan for or invent private endpoints.
- **B7 — Benchmarked rollout:** run controlled benchmarks, capture artifacts, document gaps, and request explicit governance approval. Do not auto-deploy or auto-merge protected changes.

## 14. Current evidence boundary

The existing VAIXLNS documents define an index-recovery/runtime-admission protocol, typed VX interoperability, a reference VX Stage runner, and a federated capacity plan. The capacity plan explicitly distinguishes CI/reference runs from persistent production servers. Therefore:
- this bridge begins as SPECIFIED;
- local tests can establish local contract conformance only;
- a mock or fake endpoint does not establish remote connectivity;
- a successful health check does not establish semantic correctness;
- live connection, persistent workers, GPU/solver availability, multi-node throughput, and canonical admission remain unproven until their specific evidence is recorded.

## 15. Non-negotiable rule

> ARC-X determines what the evidence supports; VX determines what is eligible to execute; VV verifies the declared obligations; VAIXLNS governance determines what may become canonical. No layer may grant itself the authority of another.

This is an additive integration contract. It does not supersede existing specifications or historical records. Implementation status may advance only through reproducible tests and evidence attached to the exact revision.
