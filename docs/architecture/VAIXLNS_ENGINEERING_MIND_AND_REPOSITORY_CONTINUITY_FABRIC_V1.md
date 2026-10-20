# VAIXLNS Engineering Mind and Repository Continuity Fabric v1

**Status:** SPECIFIED + bounded reference implementation  
**Authority:** project.genome::v1.0.0 / Ω0_GENESIS_CORE  
**Canonical index:** Ω.000  
**Evidence reconstruction:** ARC-X Ω  
**Execution and replay:** VX  
**Discovery and candidate synthesis:** XV / research workers  
**Independent verification:** VV / verification fabric  
**Mathematical and physical simulation:** VCRE

This fabric extends the existing memory, perpetual-engine, ARC-X/VX bridge, and VCRE contracts. It does not replace them, merge repository identities, or claim every described worker is already deployed.

## 1. Operating objective

Turn a repository federation into a continuity-preserving engineering system that can:

1. inventory accessible repositories and capture exact revisions;
2. recover historical ideas and source artifacts without silent loss;
3. connect systems by evidenced capabilities, contracts, dependencies, and shared invariants;
4. generate executable mathematical, software, and physical models from explicit inputs;
5. simulate baseline and counterfactual scenarios;
6. compare predictions with independent observations;
7. find architectural gaps, failing contracts, regressions, and expensive test paths;
8. propose a bounded improvement, run it in isolation, measure it, and preserve the evidence trail.

No single intelligence score establishes correctness. The fabric evaluates correctness, uncertainty, test coverage, runtime, security, reproducibility, and engineering utility separately.

## 2. Six cooperating minds with separated authority

| Mind / fabric | Primary responsibility | Cannot do by itself |
|---|---|---|
| Ω.000 Memory Mind | Source identity, retrieval, lineage, history, conflicts, gaps, and lossless references | Turn summaries into original sources or accept its own canonical update |
| XV Discovery Mind | Search, derive candidate architectures, generate hypotheses and alternatives | Claim that generated designs are verified or safe |
| VCRE Model Mind | Typed model contracts, numerical solving, counterfactuals, invariants, and error diagnostics | Declare simulation equal to physical reality |
| VX Execution Mind | Plan dependency DAGs, schedule eligible capabilities, isolate workers, replay tasks, capture receipts | Grant canonical authority or bypass worker policy |
| VV Verification Mind | Independent tests, property checks, differential checks, reproduction, and falsification | Rely solely on the producer's self-reported pass |
| ARC-X Assurance Mind | Claims, counter-evidence, proof obligations, source quality, contradictions, and temporal reconstruction | Infer approval from the absence of a detected contradiction |

A coordinator may route and parallelize work, but these roles retain separate contracts. Material decisions require producer/verifier separation and an explicit VAIXLNS governance gate.

## 3. Repository continuity: preserve first, optimize second

### 3.1 Identity and source capture

Every repository record should bind:
- stable repository ID and observed owner/name;
- aliases and historical names, preserved rather than destructively renamed;
- visibility/access result, default branch, observed ref, commit SHA and tree SHA;
- source snapshot/archive digest when capture is permitted;
- license and provenance metadata;
- capture time, tool/version, failure state, and evidence receipt;
- parent/fork relationships, related-system IDs, capability contracts and known conflicts.

A repository that cannot be accessed is recorded as INACCESSIBLE or NOT_CAPTURED; it is never marked preserved merely because it appears in a list. Private content must not be exposed through logs, public artifacts, or unauthorized cross-repository mirrors. Secrets are never copied into knowledge indexes.

### 3.2 Lossless memory tiers

- **Tier A — source vault:** original documents, code snapshots, artifact references, equations, schemas, logs, test output, and historical drafts.
- **Tier B — identity/event ledger:** typed records, source hashes, alias decisions, append-only lifecycle events, verification receipts, and reviewed governance decisions.
- **Tier C — rebuildable projections:** search indexes, embeddings, dependency graphs, summaries, caches, and predictive features.

A projection may accelerate retrieval but cannot replace Tier A. Hashes establish byte identity, not correctness, provenance truth, authorization, or trust. A hash mismatch causes quarantine and an explicit reconciliation event.

### 3.3 Conflict-aware cross-linking

Connect repositories by observed evidence:
- explicit contract/schema compatibility;
- verified API or protocol compatibility;
- matched source lineage and commit references;
- executed adapter conformance tests;
- independent runtime evidence.

Name similarity, README claims, or matching version numbers only create LINK_CANDIDATE. Conflicted mappings remain UNRESOLVED until evidence closes the identity question.

## 4. Full engineering execution loop

~~~text
INTENT / FAILURE / DISCOVERY
            |
            v
Ω.000 SCOPE RETRIEVAL + HISTORICAL SOURCE COVERAGE
            |
            v
IDENTITY / LINEAGE / LICENSE / SECURITY PREFLIGHT
            |
            v
ARC-X EIR + CLAIMS + ASSUMPTIONS + PROOF OBLIGATIONS
            |
            v
VX CAPABILITY GRAPH + DEPENDENCY DAG + RESOURCE BUDGET
            |
            v
MODEL / CODE / ADAPTER CANDIDATE IN ISOLATED WORKSPACE
            |
            v
TYPED CONTRACT CHECKS + STATIC ANALYSIS + FAST TEST ROUTING
            |
            v
VCRE SIMULATION / REPLAY / COUNTERFACTUALS / ERROR METRICS
            |
            v
VV INDEPENDENT VERIFICATION + ADVERSARIAL / REGRESSION TESTS
            |
            v
ARC-X EVIDENCE RECONSTRUCTION + DRIFT / UNCERTAINTY ASSESSMENT
            |
            v
GOVERNANCE DECISION
   | PASS                | FAIL / UNCERTAIN
   v                     v
PROPOSED INDEX DELTA     QUARANTINE + FAILURE GENOME + RECOVERY PLAN
   |                     |
   +------ REVIEW -------+
            |
            v
MEASURED POST-CHANGE BASELINE -> NEXT BOUNDED CYCLE
~~~

Every stage emits machine-readable provenance, explicit inputs/outputs, and a terminal state. An acknowledgement receipt cannot substitute for execution logs or independent verification.

## 5. Predictive model discipline

Every model must declare:
- identity/version and code or implementation digest where obtainable;
- state variables, parameter names and unit/dimension contract;
- equations or transition implementation;
- initial and boundary conditions;
- assumptions, validity domain and exclusions;
- invariants, solver, step policy, tolerances and resource cap;
- uncertainty model and observations used for calibration;
- reference scenarios, independent comparison method and known limitations.

A scenario output is initially SIMULATED. Numerical residuals and local truncation estimates describe numerical behavior, not necessarily physical forecast accuracy. Promote the forecast to a validated level only after independent or out-of-sample observations, declared tolerances, provenance checks, and documented domain coverage.

### 5.1 Required model comparisons

Where applicable, the verification plan includes:
- analytic solutions and dimensional checks;
- step-size refinement and convergence diagnostics;
- conservation/invariant checks;
- sensitivity and parameter sweeps;
- baseline versus counterfactual comparison;
- differential or metamorphic tests against a separate implementation;
- calibration and held-out validation on pinned observations;
- numerical agreement across supported solver/hardware paths.

When a model is outside its validity domain, the solver is unstable, observations are missing, tolerances are absent, or uncertainty cannot be quantified, return INCONCLUSIVE, OUT_OF_DOMAIN, MODEL_INSUFFICIENT, or QUARANTINED rather than fabricating confidence.

## 6. Engineering intelligence and safe self-improvement

The fabric learns from verified evidence, not from its own generated assertions. An improvement candidate records:

- target subsystem and exact source revision;
- failure or opportunity statement and supporting evidence;
- proposed change, alternatives, expected benefits and risk budget;
- pre-change baseline and comparable workload;
- required tests and independent falsification strategy;
- expected runtime, memory and correctness impacts;
- rollback conditions and a no-change fallback;
- actual results, unexplained differences and verifier report.

Improvement cycle:

OBSERVE → DIAGNOSE → PROPOSE → ISOLATE → SIMULATE → TEST → MEASURE → INDEPENDENTLY VERIFY → REVIEW → ADOPT OR REJECT

The system may autonomously recommend and test in a controlled branch or disposable sandbox. It may not autonomously rewrite constitutional authority, disable required checks, alter access boundaries, merge protected changes, delete historical sources, deploy physical control, or promote itself to a higher trust state.

Optimization success is multi-objective:
- correctness and invariant preservation;
- forecast calibration and uncertainty quality;
- reproducibility;
- time-to-feedback and wall-clock test cost;
- defect detection and regression escape rate;
- security, privacy, and license compliance;
- repository and historical-source coverage.

A faster test run is not an improvement if it omits relevant tests or raises escaped defects.

## 7. Test acceleration contract

Use impact-based selection only where the dependency map is known and complete for the changed paths. The reference tool tools/engineering_test_router.py produces a JSON receipt and applies these rules:

1. known source-to-test mapping → execute the mapped focused tests;
2. multiple known changes → union the target tests;
3. unknown, cross-cutting, schema, registry, governance, documentation-index, or workflow change → full unit-test suite;
4. missing base/head, failed Git diff, or empty change set → full unit-test suite;
5. no selection mode waives required CI, integration, security, conformance, release, or independent-verification gates.

Record actual wall-clock time, exit code, selected files, selection reason, and a digest of test output. Speed claims require a baseline measured on equivalent commits and comparable runner conditions; proposed targets are not measured results.

## 8. Capability composition and fast integration

External tools and repository workers are integrated through versioned capability contracts instead of provider-specific shortcuts. Each adapter declares:
- capabilities and explicit unsupported operations;
- input/output schema and unit semantics;
- identity, network, data residency, licensing and permission scope;
- timeout, retry, idempotency, rate/resource budget and cancellation semantics;
- deterministic/replay behavior and evidence output;
- conformance, failure-injection and security tests.

Independent read-only retrieval, linting, or pure simulations may run concurrently after scope preflight. Writes, governance, canonical updates and external side effects remain gated. Cache reuse is keyed by complete content digests, tool/version and policy; stale or incomplete keys cannot return trusted results.

## 9. Evidence states and promotion boundaries

| State | Meaning |
|---|---|
| PROPOSED | candidate design or hypothesis |
| SPECIFIED | contract and intended behavior are documented |
| IMPLEMENTED | source exists at a pinned revision |
| TESTED | specified tests were executed, with results retained |
| VERIFIED | relevant independent proof obligations and reproducibility checks passed |
| VALIDATED | model/behavior compared with independent real-world/reference observations in the declared domain |
| LIVE_VERIFIED | deployed runtime operation evidenced over the stated conditions and time |
| INCONCLUSIVE / BLOCKED | evidence is insufficient or a gate did not pass |

A status never advances merely because a later stage exists in a diagram or because a script returns exit code zero. Record exact gate scope and evidence location.

## 10. First bounded implementation slice

This branch adds:
- vcre/predictive.py: fixed-step RK4 integration with step-doubling local truncation diagnostics, explicit invariant checks, stable result hashes, parameterized scenario comparisons, and observation-validation metrics;
- tests/test_vcre_predictive.py: synthetic-system, determinism, invariant, input-contract, budget, scenario and validation-boundary tests;
- tools/engineering_test_router.py: conservative change-impact test routing, full-suite fallback, and machine-readable duration/exit-code/output-digest receipt;
- tests/test_engineering_test_router.py: selection and fail-safe policy tests.

This is a bounded reference slice, not yet a federation-wide production simulation service. Live integration with every repository, remote compute workers, GPU/HPC solvers, external lab measurements, learned uncertainty calibration, and persistent long-run performance history require separate evidence.

## 11. Acceptance criteria

- Same pinned model/input/config returns equivalent canonical result content.
- Non-finite or schema-mismatched states fail before results can be emitted.
- Declared invariants are checked at every committed state.
- Scenario comparison preserves receipts and states the causal-interpretation boundary.
- Observations without declared tolerance are INCONCLUSIVE, never silently validated.
- Unknown test impact selects the full unit-test suite.
- Router failure or missing diff metadata cannot result in an empty green test run.
- Performance claims include test-selection receipt, baseline, comparable conditions, and regression/coverage guardrails.
- No code or model automatically authorizes its own canonical admission.

## 12. Non-claims

No claim is made that the system can predict arbitrary future events, derive universally valid physical laws, simulate every domain exactly, preserve repositories inaccessible to its credentials, run every tool/server live, or autonomously self-improve safely without governance. These remain research goals whose readiness must be earned with independent evidence.
