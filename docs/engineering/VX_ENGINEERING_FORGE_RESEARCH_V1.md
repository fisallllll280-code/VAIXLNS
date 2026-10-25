# VX Engineering Forge — Research & Computational Engineering v0.1

Status: PROPOSED / branch-only. No runtime activation, no benchmark claim, no deployment.

## Objective
Coordinate reproducible research in mathematics, computational mathematics, physics, computer engineering, and software performance through the existing VX and Ω mechanisms. No claim of superiority to other models is made without controlled comparative benchmarks.

## Existing integration points (read from main, 2026-10-25)
- tools/engineering_test_router.py: focused tests with fail-closed full-suite fallback. Never waives CI.
- tools/arcx_mcp/server.py: bounded read-only repository evidence.
- tools/model_mcp/server.py: explicit model calls; no automatic routing; provider credentials and spending not authorized.
- tools/server_discovery_probe.py: bounded GET reachability checks, not service correctness.
- tools/vx_tool_control_reference.py: reference policy evaluator, not an enforced security boundary.
- scripts/omega_engineering_cycle.py; scripts/measure_innovations.py; registry/research/: candidates for further audit before wiring.

## Proposed modules
1. Research Intake: claim, problem, domain, units, assumptions, citations, novelty check, hypothesis and falsification conditions.
2. Mathematical Core: symbolic/numeric computation adapters; property-based checks; independent solver cross-checks; error bounds and precision.
3. Physics Simulation: unit-consistent models, boundary conditions, conservation checks, mesh/time-step convergence, uncertainty and domain limitations.
4. Engineering Design: design alternatives, constraints, trade-offs, BOM where applicable, standards and safety review.
5. VX Job Planner: DAG with immutable inputs, dependency tracking, bounded concurrency, idempotency and cancellation.
6. Ω Evidence: source commit, tool/version, inputs/outputs SHA-256, environment digest, test receipts, reproducibility and independent reviewer.
7. VV Dashboard: READ-ONLY status display until a verified authenticated API is available.

## Lifecycle
INTAKE -> SOURCE_REVIEW -> FORMAL_SPEC -> BASELINE -> CANDIDATES -> SIMULATION -> ADVERSARIAL_REVIEW -> SANDBOX_TEST -> EVIDENCE -> HUMAN_ADMISSION.
Research novelty is PROPOSED until independent prior-art assessment. Passing a test never alone grants VERIFIED.

## Performance research VX-EF-PERF-001
A. Safe focused tests; unknown impact runs full suite.
B. Content-addressed evidence/index cache; keys include repository SHA, environment, tool version, policy digest, input hash.
C. Parallel independent jobs only after isolation, budget and gate verification.
Compare 30+ paired warm/cold trials per scenario, P50/P95, throughput, CPU/RAM/I/O, correctness, CI pass rate, provenance integrity. Target 10x is aspirational, not measured.

## Required safety gates
- Protected files: project.genome and Ω.000 are never changed.
- No merge, publish, external spending, provider calls, production or physical action.
- Only explicitly approved isolated jobs. Any absent policy, dependency or evidence -> HOLD.
- G0 and VX-INT-EXEC-001 test order: T01-T05, T06-T10, T15, T11-T14; NOT_RUN until receipts exist.
- Scientific simulation is not certification for real-world safety-critical deployment.

## Acceptance checklist
- [ ] Record pinned SHA for every input repository
- [ ] Validate each tool's real API and dependencies
- [ ] Unit tests for registry schema, missing IDs, duplicates, invalid domain, unsupported operations
- [ ] Deterministic smoke tests with no network or paid APIs
- [ ] Baseline benchmark and full-suite CI evidence
- [ ] Independent replication and approval
