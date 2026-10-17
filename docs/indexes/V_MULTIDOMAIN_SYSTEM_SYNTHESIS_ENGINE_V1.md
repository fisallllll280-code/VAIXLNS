# VAIXLNS — Governed Multidomain System Synthesis Engine V1

**Status:** Implementation baseline; candidate-to-review gate  
**Canonical parent:** VAIXLNS  
**Domain engine:** VCRE  
**Discovery and candidate generation:** NEXENT / XV  
**Execution boundary:** VX  
**Independent verification:** VV / ARC-X  
**Operational assurance:** OIF  
**Canonical memory and lineage:** Ω.000 / Nexus

## 1. Purpose

This specification closes one engineering gap between the existing mathematical/physical computation foundations and system creation: a generated architecture must become a typed, comparable, bounded, and reviewable candidate before it can enter implementation.

The reference implementation in the repository:
- validates a cross-domain candidate contract;
- rejects unsafe self-promotion and explicit hard-constraint failure;
- holds candidates with unknown mandatory obligations;
- records a deterministic SHA-256 fingerprint of JSON-compatible candidate input;
- compiles a deterministic verification task DAG;
- computes a Pareto frontier only for structurally reviewable candidates with comparable objective definitions.

It does **not** generate arbitrary code, run a physical simulation, invoke external agents, verify a live integration, authorize production, or certify physical truth.

## 2. One synthesis fabric, not another disconnected hierarchy

The new gate composes existing VAIXLNS boundaries rather than replacing them:

~~~text
Ω∞ / Ω0 / Constitution
          |
          v
Ω.000 + Nexus: recover source, identity, lineage, constraints
          |
          v
NEXENT / XV: discover gap and propose candidate architectures
          |
          v
Mathematics + Computation + Software + Physics contracts
          |
          v
VCRE: formalize model, units, invariants, numerical method, uncertainty
          |
          v
VAMM / VAIXLNS-IR: typed, reviewable candidate representation
          |
          v
vcre.synthesis: candidate assessment + verification DAG
          |
          v
VX sandbox: bounded implementation, test, benchmark, simulation
          |
          v
VV / ARC-X: independent checks, counterevidence, replay receipt
          |
          v
Authority / OIF: admission, rollout constraints, observation, recovery
          |
          v
Ω.000 / Genome: preserve result, failure, lineage, and verified reuse
          |
          +------> NEXENT search / next candidate (never self-promoted)
~~~

The gate's output is a review package. Existing constitutional, admission, verification, and runtime mechanisms retain their authority.

## 3. Cross-domain contracts

### 3.1 Mathematics

A candidate declares its formalism, assumptions, constraints, and proof obligations. Depending on the domain these may include:
- dimensional and type consistency;
- domain/range restrictions;
- boundary and initial-condition consistency;
- satisfiability of hard constraints;
- conservation or symmetry obligations;
- stability and sensitivity questions;
- theorem-prover or symbolic-check obligations where applicable.

A list of obligations is not proof that they have been discharged.

### 3.2 Computation

The computation contract binds the algorithm, determinism policy, numerical tolerances, maximum steps, memory budget, and wall-clock budget. Execution workers should emit the actual solver/runtime, environment, random-seed policy, residuals, error diagnostics, and output digest.

Exact, symbolic, bitwise deterministic, and numerically equivalent are different contracts. Floating-point execution across hardware is compared against declared tolerances and invariants, not assumed byte-identical.

### 3.3 Software

The candidate pins an implementation language, build recipe, dependency-lock reference, test targets, static/security checks, and rollback plan. A passing unit-test suite is only one evidence item; it does not establish architecture correctness, security, or the validity of a physical model.

### 3.4 Physics and real-world systems

The physical contract records:
- variables and units;
- initial and boundary conditions;
- invariants and admissible state;
- numerical tolerance and validity domain;
- validation basis;
- actuation mode and safety/authority boundary.

The validator recognizes analytic references, benchmarks, experiments, independent solvers, and test fixtures as declared validation bases. Actual evidence must still be generated and reviewed independently. A converged solver is not proof that the model matches the world.

Modes:
- OBSERVE_SIMULATE: default for model evaluation and virtual tests;
- HARDWARE_IN_LOOP: requires an explicit HIL plan and safety contract;
- REAL_ACTUATION: remains on hold without separate authority and safety references, and still cannot be executed by this candidate compiler.

For robotics, vehicles, industrial control, or other physical actuators, real-world action remains behind a separately authorized safety contract.

### 3.5 Integrations

Every integration adapter declares identity, version, input/output schema references, permission scope, timeout, idempotency behavior, and fail-closed failure semantics. Secrets are represented only by separately governed secret handles; raw credentials must not be embedded in candidate manifests.

Connectivity is not trust. A response from a reachable tool or server still requires contract validation, provenance capture, and result verification.

## 4. Mathematical selection without hiding catastrophic constraints

System creation is a constrained multi-objective search. A candidate can be compared over cost, latency, error, energy, throughput, robustness, and other explicitly defined metrics:

~~~text
minimize / maximize: f(candidate) = [f1, f2, ..., fn]
subject to: hard_constraints(candidate) = PASS
            domain_contracts(candidate) = VALID
            resource_budget(candidate) = BOUNDED
            authority(candidate) = EXPLICIT
~~~

Hard constraints are gates, not weighted preferences. A severe safety or dimensional violation cannot be compensated for by a higher throughput score.

Pareto comparison is permitted only when candidate objective sets have identical metric names, units, direction, and evidence state. Estimated, simulated, and measured values must not be silently mixed. Pareto rank is an exploration aid, not verification or admission.

## 5. Agent execution: specialist profiles over the existing registry

Do not create an unbounded number of permanent autonomous agents. Route existing registered agents through narrow, task-scoped specialist profiles:

| Specialist profile | Primary responsibility | Required outputs |
|---|---|---|
| System architect | composition, dependency graph, failure boundaries | candidate genome, contracts, blast radius |
| Mathematical formalist | equations, dimensional consistency, proof obligations | formal obligations, counterexamples |
| Computational scientist | solver selection, numerical stability, resource budgets | method choice, residual/convergence report |
| Physics model specialist | validity domain, units, invariants, experiment links | physics contract, model limitations |
| Software engineer | implementation, dependency pinning, tests, SBOM/security artifacts | patch, build/test receipts |
| Integration engineer | adapter identity, schemas, timeout/idempotency, permissions | integration contract and conformance evidence |
| Adversarial reviewer | attacks, failure injection, boundary violations | findings, anti-spec, recovery tests |
| Independent verifier | replay and independent checking | verification report and counterevidence |
| Evolution judge | review of evidence, blast radius, authority, rollback | ADMIT / HOLD / REJECT recommendation |

Profiles map onto the existing agent operating model (AG-003 through AG-013 as applicable); assignment does not create authority. The builder must not be the sole verifier of its own consequential work.

### 5.1 Handoff envelope

Each task handoff carries task ID, source/target agent IDs, capability contract, source revision, candidate fingerprint, proof obligations, budget, permitted tools, expiry, evidence references, expected artifact, failure behavior, and authority scope.

Every tool result is data until validated. Unknown identity, missing scope, malformed outputs, or absent evidence produces HOLD or quarantine.

## 6. Verification DAG and evolution lifecycle

The reference compiler emits a review plan in this order:

1. contract preflight;
2. mathematical and dimensional checks;
3. physical invariant checks;
4. numerical convergence and sensitivity;
5. software build, tests, and supply-chain checks;
6. integration conformance;
7. adversarial and failure/recovery testing;
8. independent replay and verification;
9. authority and evolution review.

Independent tasks may run in parallel where the DAG permits. Shared mutable state and external side effects remain serialized. If impact analysis is uncertain, the repository's existing fast-feedback router should choose the full test suite rather than an unsafe subset.

### System-after-system development loop

~~~text
observed gap / incident / performance regression / new evidence
           ↓
recover lineage + known-good baseline
           ↓
generate alternative candidate genomes (NEXENT/XV)
           ↓
compile typed contracts + proof obligations
           ↓
mutate one controlled axis at a time in a candidate branch
           ↓
simulate / build / test / benchmark / attack
           ↓
independent verification + comparison to baseline
           ↓
authority decision + staged rollout plan
           ↓
post-rollout observation / rollback if guardrail fails
           ↓
failure genome + regression test + evidence-backed memory
           +--------------------> next research cycle
~~~

Evolution triggers are allowed to produce proposals, not privileged mutations. The candidate compiler forbids self-promotion and limits mutation to sandbox/candidate-branch scope. No autonomous merge, deployment, external message, financial act, or physical actuation is introduced here.

## 7. Status semantics

- INVALID: malformed or incomplete candidate contract.
- REJECTED: explicit hard-constraint failure, forbidden self-promotion, or unsafe mutation scope.
- HOLD: mandatory condition unknown or evidence/safety boundary incomplete.
- READY_FOR_REVIEW: structurally complete enough to enter the independent review process.

READY_FOR_REVIEW is not IMPLEMENTED, VERIFIED, VALIDATED, ADMITTED, COMMITTED, or CERTIFIED. The plan compiler emits PLANNED_NOT_EXECUTED by design.

## 8. First acceptance bar

The first executable slice is accepted only when:
- candidate fingerprints are repeatable for identical JSON inputs;
- invalid units/contracts fail closed;
- unknown hard constraints cause HOLD;
- failed hard constraints cause REJECTED;
- builder/verifier identity collision is surfaced;
- real actuation without authority is held;
- the DAG fingerprint is deterministic;
- Pareto comparison excludes blocked candidates and rejects incomparable evidence states;
- the VCRE tests run in GitHub Actions.

## 9. Research boundaries

The synthesis engine is a candidate-control primitive, not a universal invention machine. It cannot prove arbitrary mathematics by itself, discover physical laws by assertion, make a simulation equal to an experiment, or establish that an integration is live simply because its manifest is valid. Those claims require separate algorithms and evidence.

## 10. Implementation map

- vcre/synthesis.py — reference candidate assessor, deterministic plan compiler, constrained Pareto frontier.
- tests/test_vcre_synthesis.py — executable fixtures for status gates, identity, plan stability, and comparisons.
- schemas/engineering-system-candidate.schema.json — machine-readable candidate envelope.
- docs/indexes/V_COMPUTATIONAL_REALITY_ENGINE_V1.md — canonical parent reference.
