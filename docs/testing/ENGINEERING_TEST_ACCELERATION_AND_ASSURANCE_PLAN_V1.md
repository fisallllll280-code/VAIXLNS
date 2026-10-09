# VAIXLNS Engineering Test Acceleration and Assurance Plan v1

**Status:** PROPOSED PLAN — not yet implemented as a CI redesign  
**Owner:** VAIXLNS engineering / assurance  
**Authority:** project.genome::v1.0.0; Ω0_GENESIS_CORE; Ω.000  
**Applies to:** VAIXLNS, VAIXLNS-unified, VX reference/runtime surfaces, NEXENT, VLNS activation adapters, memory/index tooling, ARC-X, and domain-specific engineering adapters  
**Core rule:** reduce feedback time without reducing proof strength.

## 1. Executive objective

Build a test system that returns early, useful failures to contributors while preserving one non-bypassable assurance path for changes that affect canonical identity, policy, admission, evidence, schemas, or runtime execution.

The target is not “fewer tests.” The target is:
- shortest reliable feedback loop for each change;
- maximum relevant tests per unit of compute;
- reproducible evidence linked to the exact revision and policy;
- deliberate parallelism where tasks are independent;
- stronger detection of semantic, security, numerical and integration defects;
- safe fallback to broader testing whenever change impact is ambiguous.

Do not publish a percentage speedup until a comparable baseline and repeated measurements exist.

## 2. Current baseline observed in the repository

The main-branch workflows inspected include:

- `.github/workflows/vaixlns-conformance.yml`: control-plane JSON validation, compile checks, admission/federation gates, proof verification, control-plane reconstruction, provenance emission, deterministic innovation-index generation/validation, and a broad `unittest discover -s tests` run.
- `.github/workflows/federation-integrity.yml`: additional schema validation, federation validation, integrity gate, and protected-path deletion guard.
- `.github/workflows/discovery-routing.yml`: path-scoped router compile and focused unit tests.
- `.github/workflows/vx-stage-runtime.yml`: path-scoped Stage compile/tests, golden scenario, admission and federation gates.
- `.github/workflows/innovation-index-sync.yml`: scheduled/source-triggered deterministic generation, validation, and pull-request proposal flow.
- `tools/build_innovation_operation_index.py` and `tools/validate_innovation_operation_index.py`: deterministic generated-index tooling with a check mode.

These surfaces show both reusable specialized checks and repeated control gates across workflows. Exact wall-clock durations, queue times, cache costs, flaky-test rates, and slowest-test profiles have not yet been measured in this plan. Obtain these from Actions run/job/step timings before optimizing based on assumed bottlenecks.

## 3. Test architecture: five assurance tiers

### T0 — Static and contract preflight (fast)
Run syntax/import compilation, JSON/YAML parsing, schema self-consistency checks, required-file checks, secret-pattern checks, and basic policy linting. No network and no mutable side effects.

### T1 — Focused unit tests (fast feedback)
Test the smallest affected module and its direct contracts. Use deterministic fixtures and local fakes. Every test should identify the invariant it protects and the failure mode it detects. A focused result is an early signal, not a replacement for downstream gates.

### T2 — Cross-contract integration tests
Exercise component boundaries: discovery → classification → policy route; ARC-X task envelope → VX admission; VLNS activation envelope → receipt → evidence event; memory source → index delta; model/compiler output → typed task contract. Include invalid, stale, duplicated, unauthorized, incomplete and conflicting inputs.

### T3 — System golden, recovery and replay
Run deterministic golden scenarios for VX Stage, admission, federation integrity, proof verification, generated-index determinism, event/ledger reconstruction and recovery. Compare explicit output invariants and evidence digests, not merely process exit codes.

### T4 — Scheduled deep assurance
Run broader cross-repository contract checks, property-based or generated-input testing, mutation testing, fuzzing for parsers, dependency/security scans, fault injection, performance benchmarks and domain-specific numerical/physics tests. Expensive checks may be scheduled nightly or before release, but critical security, identity, authorization, proof and canonical-admission checks remain required before merge when affected.

## 4. CI topology for fast feedback

Split independent jobs, not independent safety obligations:

1. **Preflight:** changed-file map, syntax and schema JSON/YAML parse; produce a revision-bound impact manifest.
2. **Control-plane assurance:** genome, Ω.000, provenance, proof, admission and federation integrity.
3. **Routing and federation:** discovery router, VX federation gate, capability and authority routing tests.
4. **Runtime/replay:** VX Stage golden scenario, failure isolation, recovery and replay tests.
5. **Index determinism:** build innovation-operation index, validate it, then run the generator in `--check` mode.
6. **Adapter contracts:** ARC-X/VX task and receipt, VLNS activation and evidence event, memory coverage/lineage, and any touched domain adapter.
7. **Full suite:** repository-wide tests on merge-critical changes and on a schedule; every specialized suite remains represented.

Run these jobs concurrently when they do not depend on the same generated state. The final required-check policy must require the relevant jobs and the final assurance aggregator to pass. A green focused job must never substitute for a missing mandatory gate.

### Avoid unnecessary repeated work

- Extract shared read-only validation into one versioned composite action or script called by multiple workflows; preserve separate job results for traceability.
- Do not run the same expensive generator twice in a single job unless the second run is explicitly the determinism check.
- Where an identical gate is required by separate workflows, decide whether to run it once in a required shared job or retain deliberate duplication for isolation. Record the decision and test it before deleting the duplicate.
- Avoid installing pytest, coverage, mutation, schema-validation or fuzzing packages in every fast job without measuring the cost; pin and cache dependencies only when the relevant suite actually needs them.
- Keep local deterministic tests network-free. Remote integration tests use explicit operator-provided endpoints and a separate opt-in workflow.

## 5. Safe change-impact selection

Create a deterministic mapping from path classes to mandatory test suites. Example:

| Change class | Minimum required checks |
|---|---|
| Python source / tests | compile + directly affected tests + dependent contract suite |
| `schemas/**` | parse/schema validation + all producer/consumer contract tests |
| `project.genome`, `registry/omega/**`, admission/policy/proof code | full control-plane, provenance, proof, admission and federation-integrity gates |
| index source catalogs / index builder | source validation + deterministic generator + index validation + `--check` + lineage/coverage tests |
| VX routing, state, leases, replay, runtime adapters | routing tests + golden Stage + isolation/recovery/replay + evidence validation |
| VLNS activation / model/provider contract | envelope/schema tests + signature/receipt mismatch tests + evidence-event tests |
| ARC-X / EIR / engineering task envelope | schema and type contract tests + false-admission tests + provenance and task-receipt tests |
| numerical / physics / scientific adapter | unit/dimensional tests + residual/invariant tests + reproducibility and benchmark tests |
| workflow, reusable action, dependency lock or test tooling | workflow validation + affected suite + full assurance because the test harness itself changed |
| docs-only changes | link/structure checks; if policy, schema, contract, runbook, generated-index source, or status claim changes, apply the relevant gates above |

Rules:
- Unknown paths and unclassified impact default to the full assurance suite.
- Renames are evaluated as both deletions and additions; protected-source deletion checks stay enabled.
- The change map cannot decide that a governance-sensitive file is “docs-only.”
- Emit the change classification and selected checks as an artifact so a reviewer can audit why a suite ran or did not run.
- Run periodic full suites to detect missing dependency edges in the map.

## 6. Test selection and parallelism algorithm

Build a test dependency graph:
- Nodes: source files, schemas, policy rules, generated indexes, test modules and runtime contracts.
- Directed edges: imports, schema producers/consumers, index source/generator/output, lifecycle transitions and evidence dependencies.
- For a changed node, compute its impact cone and select all downstream tests.
- Group tests by measured historical duration and resource class; balance jobs by estimated runtime rather than test count.
- Parallelize only independent groups. Protect tests sharing mutable state, external services, ports or durable databases with isolation or explicit serialization.
- Use deterministic sharding based on stable test IDs. Record shard configuration and seed.
- If dependency extraction fails, the graph is incomplete, or a relevant source is unclassified, fail over to the complete suite.

The first version can be a checked-in declarative mapping with conservative rules. Do not begin with a complex learned selector before the mapping can be compared against repeated full-suite runs.

## 7. Stronger engineering test formulations

Every consequential requirement should be expressed as:

`Requirement → Invariant → Preconditions → Input/State → Expected outcome → Counterexample → Evidence → Owner/Policy version`

Required test families:

### 7.1 Contract and state-machine tests
Verify allowed and forbidden transitions, lifecycle guards, expiry, version compatibility, idempotency, cancellation, replay and recovery. Cover each transition's success and rejection conditions.

### 7.2 Negative and adversarial tests
Attempt to bypass admission with missing provenance, unrelated evidence, malformed types, stale policies, altered digests, invalid signatures, spoofed worker identity, hidden prompt injection, duplicate requests, expired leases and self-authorization. Assert exact blocked/hold/quarantine outcomes.

### 7.3 Property-based and boundary tests
Generate varied valid and invalid records, Unicode identifiers, Arabic/Indic numerals, extreme sizes, empty/missing fields, graph cycles, duplicated lineage and unusual numeric values. Pin seeds and preserve minimal counterexamples as regression fixtures.

### 7.4 Differential and metamorphic tests
Compare independent implementations or equivalent transformations. Examples: replay must preserve the declared equivalence; changing only a non-semantic field should not change semantic identity; a normalization pass followed by canonical serialization must be stable; equivalent units under a valid conversion should yield compatible measurements.

### 7.5 Numerical and physics assurance
Separate exact proofs from floating-point tests. Record precision, algorithm, solver/library versions, random seed, convergence, residual/error, boundary/initial conditions and model assumptions. Check dimensional consistency and relevant conservation/invariant properties. A converged solver is not itself evidence that the physical model matches reality; use validated benchmarks or experimental references when available.

### 7.6 Mutation testing
For high-risk modules, deliberately mutate branch conditions, policy checks, digest validation and status transitions. A test suite that remains green after a safety guard is removed is not sufficient. Start with admission, signatures, provenance, identity, and canonical-write boundaries before expanding to all code.

### 7.7 Fault-injection and recovery
Simulate worker timeout, corrupt or missing artifacts, unavailable evidence store, interrupted index rebuild, partial remote activation, stale policy at dispatch, retry after unknown result, and failed verifier. Require durable pending states and no silent promotion.

### 7.8 Cross-repository contract tests
Pin each participating repository revision and validate its declared adapter contract. Distinguish same identity, implements, derived-from, compatible-with and merely-related. Unresolved VLNS↔NAXLNS and NEXNET↔NEXENT mappings remain blocked for operations that require those identities to be established.

## 8. Evidence package per CI run

Each required workflow should emit a machine-readable test receipt containing:
- repository, commit SHA, workflow/run/job IDs, interpreter/tool versions;
- test selection policy version, changed-path classification and selected suite list;
- source/schema/policy revisions and generated-index input/output hashes;
- counts: collected, passed, failed, skipped, xfailed where applicable;
- per-suite and total duration, queue delay when available, retry count;
- coverage summary where instrumented and mutation score where run;
- exact failure IDs and safe artifact references;
- execution environment and determinism/seed metadata;
- final result and explicit reason for any suite not run.

Do not store tokens, keys, private input payloads or secrets in receipts. A successful receipt establishes that a specific test procedure passed at a specific revision; it does not prove the entire system is correct.

## 9. Performance baseline and optimization gates

Before optimizing:
1. collect a sample of at least 20 comparable CI runs per primary workflow where history allows;
2. record p50/p95 wall time, queue time, test time, generator time, artifact upload time, flake rate and rerun rate;
3. identify the slowest suites and repeated work;
4. set a baseline using the current required assurance level;
5. make one optimization at a time and compare equivalent commits/workloads.

Suggested initial targets (targets, not claims):
- T0/T1 feedback: p95 under 3 minutes for ordinary code changes;
- focused affected-contract path: p95 under 8 minutes;
- required PR assurance: p95 under 15 minutes after runner queue time is reported separately;
- zero reduction in mandatory critical gate coverage;
- zero silent skips of admission, provenance, security or canonical-index checks;
- measured decrease in redundant work with stable or better defect-detection results;
- no unexplained increase in flaky failures or retries.

If these targets are incompatible with runner capacity or current workload, revise them from measured data rather than weakening assurance.

## 10. Phased execution plan

### Phase A — Observe (no behavior changes)
- Capture current workflow timing and test durations.
- Map source → contract/schema → tests → workflow dependencies.
- Identify duplicate gates, slow tests, network calls, shared state, and untracked skips.
- Produce a baseline report with uncertainty and missing telemetry.

**Exit criteria:** timing report and a reviewed test-impact map; no tests removed.

### Phase B — Fast feedback with conservative safety
- Standardize Python version per supported component and pin tooling/dependencies where required.
- Add a quick static/preflight job and parallelize independent specialized suites.
- Keep a required final control-plane + runtime assurance gate.
- Use conservative change selection with full-suite fallback.
- Add CI concurrency control to cancel obsolete PR runs only; do not cancel release/admission jobs that carry critical evidence.

**Exit criteria:** same mandatory gates as baseline; selection trace artifact; full-suite comparison passes.

### Phase C — Stronger formulation
- Turn design rules into explicit invariants and typed contracts.
- Add adversarial negative tests for security, provenance and self-authorization.
- Add state-machine, boundary, property-based and differential tests for the highest-risk boundaries.
- Keep counterexamples as fixtures and preserve regression lineage.

**Exit criteria:** every high-risk invariant maps to at least one positive and one negative test, plus a stable evidence reference.

### Phase D — Recovery and scientific confidence
- Add fault injection for event ledger, artifact store, worker leases and index reconstruction.
- Add numerical, dimensional and solver acceptance contracts per domain.
- Add reproducibility/replay checks and identify common-mode verifier risks.

**Exit criteria:** injected failures lead to deterministic, recoverable, non-promoting states; domain metrics are recorded.

### Phase E — Mutation and measured rollout
- Introduce mutation testing to admission, provenance, identity, signatures and policy rules.
- Run nightly full assurance and scheduled broader multi-repository compatibility checks.
- Compare latency, flakiness, coverage of critical obligations, and mutation score.
- Admit the optimized CI design only through the existing governance path.

**Exit criteria:** performance improves against baseline without lowering critical assurance.

## 11. Decision rules

- Speed is a constrained optimization objective; correctness, security, provenance and authority are hard constraints.
- A skipped test is not a passed test; record NOT_RUN with a reason.
- A health check is not a correctness proof.
- A build is not semantic verification.
- A simulation is not physical validation.
- A model confidence score is not proof.
- The candidate generator may propose test plans but cannot classify its own output as verified.
- A test selector cannot exclude the tests that validate the selector when the selector or its dependency graph changes.
- No automatic canonical promotion or destructive repository merge is introduced by this plan.

## 12. First implementation slice

Implement in this order:
1. add a test-timing and impact-manifest artifact without skipping tests;
2. split the current conformance workflow into shared preflight plus independent control, routing/runtime and index jobs;
3. verify the new required-check set against the current full suite;
4. add source/schema-to-test mapping for ARC-X, VX Stage, discovery routing, VLNS activation and innovation indexing;
5. add focused negative tests for the highest-risk authority/provenance boundaries;
6. only then enable selective PR execution, with scheduled full-suite backstop.

## 13. Status boundary

This plan is PROPOSED until the workflow redesign, timing baseline, tests, and required-check policy have been implemented and observed in Actions. No speed improvement, broader test coverage, mutation score, or live cross-repository integration is claimed by this document.

**Governing rule:** accelerate the discovery of defects, not the path by which unverified changes become real.
