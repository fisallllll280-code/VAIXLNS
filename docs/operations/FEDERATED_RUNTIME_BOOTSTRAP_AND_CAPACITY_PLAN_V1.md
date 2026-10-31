# VAIXLNS / NEXENT / VX — Federated Runtime Bootstrap and Capacity Plan v1

**Status:** EXECUTION RUNBOOK + SCALE-OUT DESIGN; production deployment not established  
**Canonical authority:** VAIXLNS  
**Research / candidate design:** NEXENT (repository identity mapping to NEXNET remains evidence-gated)  
**Execution / verification boundary:** VX  
**Default security posture:** local-only, read-only discovery, no external spending, no production mutation

## 1. What has actually been executed

The following successful GitHub Actions runs were observed on 2026-10-09:

- VAIXLNS Conformance: https://github.com/fisallllll280-code/VAIXLNS/actions/runs/37914676615
- Discovery Routing Conformance: https://github.com/fisallllll280-code/VAIXLNS/actions/runs/37914676578
- VX Stage Runtime: https://github.com/fisallllll280-code/VAIXLNS/actions/runs/37914676569
- VX Stage evidence artifact: https://github.com/fisallllll280-code/VAIXLNS/actions/runs/37914676569/artifacts/11609775686
- NEXENT Core verification: https://github.com/fisallllll280-code/NEXENT/actions/runs/37897351303

These are reproducible CI/reference-run results, not evidence of a persistent production service or of multiple live compute nodes.

### Current capability boundary

NEXENT's checked-in CLI currently provides the `status`, `demo`, `run`, and `web` entry points. Its `demo` path registers a deterministic echo capability. The research loop module enforces stage transitions (OBSERVE → FRONTIER → HYPOTHESIS → CANDIDATE → SIMULATION → ATTACK → PROOF → GOVERNANCE → ADOPTION); the stage machine alone is not a connected web/repository crawler or a proof of autonomous real-world research.

VAIXLNS has a tested deterministic discovery router, evidence-gated admission tooling, and a VX Stage reference runner. The Stage run tests signed request verification, capability/authority routing, failure isolation, blocking after isolation, and recovery/re-routing. It does not establish production federation, durable distributed consensus, or benchmark-level superiority over high-end accelerators.

## 2. Run the existing NEXENT reference system

Requirements: Python 3.11 or newer and Git. The current NEXENT package declares no mandatory third-party runtime dependencies; its CI installs pytest for testing.

~~~bash
git clone https://github.com/fisallllll280-code/NEXENT.git
cd NEXENT

python3 -m venv .venv
source .venv/bin/activate                 # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e . pytest

python -m pytest -q
python -m nexent.cli status
python -m nexent.cli demo
~~~

To run the NEXENT intent web interface locally:

~~~bash
python -m nexent.cli web --host 127.0.0.1 --port 8787
~~~

Keep it bound to loopback while validating. Do not expose it publicly until authentication, authorization, TLS, resource limits, and network policy are added and tested. Stop the foreground service with Ctrl+C.

Interpretation:
- `status` reports the reference kernel status.
- `demo` exercises the current deterministic demo capability; it is not a live research run.
- `web` launches a local interface, not a cloud deployment and not proof of external-source ingestion.

## 3. Run VAIXLNS discovery routing and VX Stage

In a separate terminal/repository checkout:

~~~bash
git clone https://github.com/fisallllll280-code/VAIXLNS.git
cd VAIXLNS

python3 -m unittest discover -s tests -v
python -m json.tool schemas/discovery-routing-record.schema.json > /dev/null
python -m unittest discover -s tests -p "test_discovery_router.py" -v
python scripts/admission_gate.py
python scripts/federation_integrity_gate.py
python scripts/vx_stage_runtime.py stage-run --output stage-evidence.json
~~~

Expected reference behavior:
- unknown/mismatched parent policy or unverified family identity is held for review;
- unresolved evidence, security, or licensing blocks normal admission;
- a discovery may create financial and engineering routes under the approved policy;
- routing never grants execution authority;
- the Stage golden scenario emits machine-readable evidence and demonstrates route denial during isolation followed by recovery.

Preserve the emitted `stage-evidence.json` with the commit SHA and environment metadata. A successful Stage run is not a deployment certificate.

## 4. Canonical integration sequence

The intended governed path is:

~~~text
NEXENT discovery / candidate
  → source and claim provenance
  → VAIXLNS canonical identity + family resolution
  → parent-directive policy check
  → VX-FINANCIAL and/or VX-ENGINEERING route proposal
  → security / license / evidence checks
  → independent verification and replay
  → explicit admission decision
  → authorized VX execution
  → event / state / ledger / evidence record
~~~

Do not invent a family ID, parent directive, provider endpoint, or VX instance when registry evidence is absent. Keep unresolved mappings on hold. A candidate produced by NEXENT is not automatically an accepted discovery record: the adapter between its output contract and `schemas/discovery-routing-record.schema.json` remains an explicit integration task.

## 5. Target architecture: scale by federation, not by pretending one server is infinite

### Control plane — VAIXLNS
Owns canonical policies, system/family identity, admission, routing constraints, audit requirements, registry lineage, and the logical source of truth. Replicas may improve availability, but they must not invent independent policy authority.

### Research plane — NEXENT
Runs source discovery adapters, repository/document ingestion, deduplication, claim/evidence extraction, architecture search, candidate synthesis, and counterevidence collection. Each adapter records source URI, revision/time, retrieval outcome, and content digest where available. Network search is disabled by default until explicit source adapters and budgets are configured.

### Execution plane — VX
Uses capability-registered workers for code, research, security, math, systems, and financial analysis. Each worker advertises instance identity, current state/health, capacity, capabilities, model/tool bindings, memory scope, and authority envelope. Only admitted tasks can cause privileged side effects.

### Evidence plane
Persists append-only event/evidence artifacts with provenance, hashes, policy version, replay inputs, verification results, and decision lineage. Deduplicate payload storage, but never erase the history of route decisions or failed candidates.

### Resource pools
- CPU pool: crawling, indexing, parsing, routing, metadata, compilation, and many tests.
- RAM / storage pool: indexes, caches, source snapshots, intermediate artifacts, and replay material.
- GPU / accelerator pool: model inference, embeddings, reranking, simulation, and other measured accelerator-bound tasks.
- External model/API adapters: opt-in only, per-provider budget-capped, with data-classification and privacy controls.
- Independent verification pool: checks important outputs using a distinct implementation or evidence path rather than simply asking the same model to agree with itself.

## 6. Scheduler policy

Route each task by a constrained score, not one universal “fastest server” ranking. Candidate features:

1. required capability and validated tool/model compatibility;
2. authority/privacy boundary and data residency;
3. worker health, queue depth, memory fit, and available accelerator;
4. estimated latency and deadline;
5. cost or local resource budget;
6. evidence obligations and required verifier independence;
7. data locality and transfer overhead;
8. failure domain and recovery path.

Apply hard security, license, authority, and memory-fit gates before ranking. A high score must never bypass a failed gate. Support weighted fair queues, backpressure, bounded retries, idempotency keys, result caching, batching where semantics permit, and work stealing between eligible workers. Keep large-model sharding separate from independent-task distribution: adding nodes only helps when the workload and interconnect permit effective parallelism.

## 7. Define “stronger” as an auditable workload claim

Do not state that the federation is faster than every server or supercomputer without controlled benchmark evidence. Establish a workload baseline first, and compare equivalent outputs at an equivalent quality/verification threshold.

Required metrics:
- accepted-and-verified tasks per second;
- end-to-end median and p95 latency by task class;
- cost per accepted-and-verified task;
- energy per accepted result when measurable;
- correctness / evidence completeness / contradiction rate;
- throughput scaling from 1 → 2 → 4 → 8 workers;
- scheduler overhead and network transfer overhead;
- recovery time, dropped-task rate, duplicate-side-effect rate, and availability;
- model-specific tokens/sec only when the model, quantization, context, batch, hardware, and quality settings match.

Run at least four workload classes independently: (A) public-source discovery and indexing, (B) coding/test cycles, (C) long-context reasoning, and (D) memory-bandwidth-heavy model inference. Keep raw measurements, commit SHA, dataset version, prompt/task set, hardware, power limits, model revision, quantization, concurrency, cache state, and all failures. Repeat runs and publish confidence intervals. Do not pool unlike task results into one score.

## 8. Hardware reality and scale strategy

High-end current platforms set a substantial raw-compute baseline. Vendor-published NVIDIA Vera Rubin information describes rack-scale AI/HPC capability, while AMD lists MI350-series accelerators with large HBM capacity and high bandwidth. Those are hardware claims for particular configurations/workloads, not directly comparable to the latency or throughput of a research-agent workflow.

The practical path to competitive system-level performance is:
- exploit parallelism across independent tasks before attempting distributed model sharding;
- keep the control plane lightweight and avoid routing every token through it;
- place data and workers near each other; cache immutable source snapshots and verified intermediate results;
- use the smallest model/tool that satisfies the measured quality contract, with escalation for hard cases;
- batch compatible work and cap queue growth;
- separate speculative candidates from admitted execution;
- run independent verification only where risk/value justifies its cost;
- isolate unhealthy nodes and automatically reroute only idempotent work;
- scale to multiple machines only after profiling shows CPU, memory, GPU, or queue saturation.

Federation can outperform a single server on aggregate throughput, availability, cost for a target workload, or failure recovery. It cannot make physical compute, RAM, network bandwidth, electricity, or model licensing constraints disappear. Beating a high-end rack at raw model inference would require comparable measured hardware capacity or a workload-specific algorithmic advantage, not just a more elaborate router.

## 9. Deployment stages

### Stage A — deterministic reference
Run NEXENT status/demo, VAIXLNS unit and admission checks, discovery-routing tests, and VX Stage scenario. Keep all external side effects disabled.

### Stage B — real research ingestion
Implement one source adapter at a time. Start with public GitHub repository metadata and explicitly approved public documentation. Store evidence/provenance. Test malformed, stale, contradictory, rate-limited, and malicious inputs.

### Stage C — governed handoff
Build and validate the NEXENT-candidate → discovery-record adapter. Resolve family and parent directive against the actual registry. Require a policy decision record and idempotent route/event IDs.

### Stage D — two-worker experiment
Deploy one CPU research worker and one independent verification worker, initially in a sandbox. Add a separate engineering worker only after it proves registration, health, permission checks, observability, and recovery. Do not attach production write credentials.

### Stage E — capacity study
Measure baseline and 2/4/8-worker scaling using fixed task suites; publish bottlenecks and cost/latency/correctness trade-offs. Scale only when marginal verified throughput improves.

### Stage F — controlled operations
Add secret manager integration, TLS/authentication, signed worker identity, durable event storage, backup/restore drills, network policy, budget caps, alerting, rollback, and admission approval. Production deployment requires an actual target host/cluster, configured secrets, sustained health/heartbeat evidence, and reproducible external observations.

## 10. Current acceptance statement

**Verified in CI:** the recorded NEXENT CLI/status/demo and test workflow passed on the inspected NEXENT branch; VAIXLNS conformance, discovery-router conformance, and the VX Stage golden scenario passed for the recorded VAIXLNS commit, with a Stage evidence artifact.

**Not yet established:** connected live web/repository research from NEXENT into the VAIXLNS discovery schema; a deployed multi-worker VX federation; a durable integrated event/state/ledger across repositories; production security hardening; persistent hosting; and measured superiority over contemporary AI servers.

This separation is mandatory: specification, executable reference, CI pass, deployed service, and benchmarked superiority are five different evidence states.
