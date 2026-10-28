# Ω Index-Driven Engineering Autopilot v1

**Status:** SPECIFIED / INTEGRATION PLAN / NOT VERIFIED IN CI  
**Authority:** VAIXLNS  
**Canonical index:** Ω.000  
**Protected sources:** project.genome and Ω.000 are read-only inputs.  
**Execution:** VX-runtime  
**Independent verification:** VV verification fabric  
**Evidence reconstruction:** ARC-X  
**Discovery and candidate synthesis:** XV / NEXENT  
**Intent normalization:** VAIXLNS-Intent-to-Reality

## Objective

Compose existing indexed capabilities into one governed engineering loop that detects likely defects before execution, routes the right checks, learns from verified failures, proposes bounded repairs, and proves only what its evidence supports.

This is an integration plan, not a claim that all workers or providers are connected. The target is measurable defect prevention and verified operation, not an unqualified 100% correctness promise.

## Existing assets to reuse (no parallel system)

| Existing asset | Intended role in this loop | Current boundary |
|---|---|---|
| `registry/omega/omega-000-master-index.json` (Ω.000) | Authoritative capability/reference map | Read-only; no automatic canonical promotion |
| `scripts/build_zero_loss_index.py` + `scripts/recover_zero_loss_index.py` | Inventory, source-bound records, coverage gaps, digest verification | Scope is the pinned VAIXLNS checkout and declared inputs |
| `scripts/omega_engineering_cycle.py` | Recover context, turn declared gaps into source-linked task candidates and a DAG | Deterministic synthesis; not a verified root-cause engine |
| `tools/engineering_test_router.py` | Select focused tests when mapping is known; full suite for unknown impact | Accelerator only; never waives required CI gates |
| `scripts/omega_pattern_foundry.py` | Generate and adversarially evaluate candidate engineering patterns | Candidates remain proposals until independently verified |
| `schemas/omega-failure-genome.schema.yaml` | Record failure origin, observations, root cause, repair, verification, replay and disposition | Schema specified; records need source-bound evidence |
| `scripts/vx_stage_runtime.py` + `scripts/vx_federation_gate.py` | Bounded runtime admission and isolation surfaces | Admission and identity proof remain required |
| `tools/vx_auto_repair.py` in VX-runtime branch `feat/vx-auto-repair-agent-v1` | Initial test-failure triage and one bounded adapter attempt | Prototype; not CI-verified and not yet an autonomous code-fixing model |
| `vxruntime/core.py` | Governed execution, capability policy, event hash chain and replay | Reference runtime; not proof of production deployment |
| `docs/INTENT_PIPELINE_V1.md` in VAIXLNS-Intent-to-Reality | Intent → contract → authorization → plan → execution → evidence → verification | Separate repository; integrate by contract and evidence, not by copying |

If an asset cannot be retrieved or its status is unclear, report NOT_OBSERVED/INACCESSIBLE and retain the gap; do not invent a replacement.

## One control loop

```text
Ω.000 + ZERO-LOSS INDEX (read-only discovery)
  -> PINNED SOURCE SNAPSHOT + COVERAGE / GAP REPORT
  -> IMPACT GRAPH (changed files -> contracts -> dependents -> tests)
  -> RISK PREFLIGHT (static checks, types, secrets, dependency/security scans)
  -> TEST ROUTER (focused only with known mapping; otherwise full suite)
  -> CONTRACT / PROPERTY / INTEGRATION / ADVERSARIAL TESTS
  -> VX SANDBOX SIMULATION + DETERMINISTIC REPLAY
  -> VV INDEPENDENT VERIFICATION + ARC-X EVIDENCE RECONSTRUCTION
  -> PASS: produce a reviewed repair candidate and proof bundle
  -> FAIL/UNKNOWN: record Failure Genome, quarantine candidate, generate new tests
  -> HUMAN AUTHORITY GATE for merge, canonical promotion, release, or deployment
```

## Failure-to-prevention learning contract

A failure record is not considered resolved until it has:
1. exact repository, commit, path, environment and command;
2. sanitized original failure observation and reproducible minimal case;
3. root-cause hypothesis explicitly separated from verified root cause;
4. affected contracts, dependents and cross-system targets;
5. proposed minimal patch and exact changed-path list;
6. failing test reproduced before repair;
7. targeted test and relevant regression suite passing after repair;
8. independent replay or equivalent deterministic reproduction;
9. evidence references and hashes;
10. disposition: OPEN, QUARANTINED, REPAIRED, VERIFIED, INVALID, or ARCHIVED.

A verified defect should generate a regression test and a reusable failure pattern. A model-generated explanation alone cannot mark a record VERIFIED.

## Safety and authority invariants

- Never modify `project.genome` or `Ω.000` automatically.
- Never merge to main, deploy, release, or spend external funds without explicit owner approval.
- No provider credentials or secrets in prompts, logs, artifacts, or failure genomes.
- No network, filesystem, or production side effects from simulation by default.
- Repairs run in an isolated branch/worktree with an allowlisted path scope.
- Maximum one repair attempt per automated cycle by default; repeated failure means quarantine and escalation, not an infinite loop.
- A repair must not bypass a failing policy/security test to obtain a green status.
- Unknown dependency impact, missing evidence, identity conflict, or unavailable required test means HOLD/BLOCKED, not PASS.
- Status changes require evidence and a separate verification step.
- A passing test command proves only the tested conditions, not universal correctness.

## Execution phases and acceptance gates

### Gate 0 — Inventory and baseline
- Run the zero-loss index unit tests and builder verification on a pinned revision.
- Capture exact revision, coverage summary, opaque sources and unresolved historical ranges.
- Run current required tests and retain logs/artifact hashes.
- Do not mark complete if the inventory reports declared gaps.

### Gate 1 — Impact and preflight
- Add an index-derived impact graph without editing Ω.000.
- Ensure unknown or cross-cutting changes route to the full suite.
- Validate protected paths, deterministic report generation, and no secret leakage.

### Gate 2 — Failure Genome and prevention
- Validate failure records against the existing schema.
- Add tests proving a verified failure produces a stable regression test and remains linked to its source evidence.
- Keep root-cause confidence explicit; unknown stays unknown.

### Gate 3 — Bounded repair and replay
- Use the existing VX-runtime prototype only inside an isolated branch.
- Add a trusted repair adapter only after path allowlisting, timeout/cancellation, diff inspection, and protected-file tests exist.
- Re-run the original failing test, the selected regression suite, and replay checks.
- Quarantine on any unrelated diff, policy bypass, or failed verification.

### Gate 4 — Continuous operation
- Wire the stages into GitHub Actions with read-only permissions by default.
- Use fast preflight on each change, targeted tests when safe, and full required suite before approval.
- Schedule broader regression, adversarial and long-horizon simulation separately.
- Upload evidence artifacts; do not automatically commit generated canonical changes.

### Gate 5 — Measured readiness
Publish these measured metrics from seeded defects and historical incidents:
- pre-merge defect recall and precision;
- false-block and missed-defect rates;
- repair acceptance and regression rate;
- replay reproducibility;
- CI duration and minutes saved;
- security findings and protected-path violations;
- percentage of indexed capabilities with fresh, reproducible evidence.

No universal 100/100 claim is permitted. Report metric-specific scores with sample size, time window, test coverage and known blind spots. A readiness score is earned from evidence; it is not a configuration value.

## Completion criteria

This integration is eligible for a readiness review only when:
- all required steps run from a pinned revision;
- the same inputs produce reproducible planning and evidence summaries;
- mandatory tests and security checks pass;
- seeded defects are detected at the declared thresholds;
- all repair attempts are bounded and auditable;
- no protected canonical file was changed;
- every claimed status maps to a fresh evidence receipt;
- owner approval remains required for merge/release/deployment.

**Current status:** this document is a specification in an isolated branch. No implementation or CI result is implied by its existence.
