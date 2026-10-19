# VX Capability Non-Regression & Evidence Gate v1

**Status:** IMPLEMENTED AS A LOCAL EVALUATOR AND BOUNDED MISSION RUNNER; CI execution evidence must be checked for the latest commit. No live production VX runtime connection is claimed.

## Objective

Make improvement a measured engineering loop rather than a promise that a system can never fail. VX should preserve known-good capabilities, learn from measured outcomes, propose bounded improvements, and reject candidates that regress any required metric.

Absolute zero degradation cannot be guaranteed in every environment. This gate makes a narrower, enforceable promise: **a candidate with a measured regression against the pinned benchmark is not eligible for promotion by this gate**.

## Components

- scripts/vx_nonregression_gate.py: deterministic JSON benchmark comparator.
- scripts/vx_mission_runner.py: bounded runner for allowlisted repository verification commands; no shell execution.
- tests/test_vx_nonregression_gate.py: regression, missing-data, metric-direction, revision, and determinism tests.
- tests/test_vx_mission_runner.py: successful execution, receipt creation, unsafe-command rejection, path traversal rejection, and duplicate-step checks.
- .github/missions/vx-gate-self-check.v1.json: sample verification mission.
- .github/workflows/vx-nonregression-gate.yml: runs the mission, runs tests, and uploads a JSON evidence receipt.

## Bounded mission runner contract

The runner accepts a mission ID and a non-empty ordered list of steps. At this stage, commands are restricted to Python unittest modules under tests.* and Python compileall over scripts/ or tests/ paths. Shell commands, arbitrary Python snippets, paths outside the allowlist, duplicate step IDs, and timeouts outside 1–300 seconds are blocked. A failure stops the mission; it does not silently continue to later steps.

The receipt records step status, exit code, elapsed time, output digests, bounded output tails, final state, and a deterministic SHA-256 digest. A receipt proves only what its recorded commands executed in that CI environment; it does not prove that arbitrary user projects can be executed or deployed.

## Benchmark contract

Each baseline and candidate JSON document contains:
- revision: exact 40-character lowercase Git commit SHA;
- metrics: non-empty object with identical metric keys in both documents;
- each metric has a finite numeric value and an unchanged direction (higher or lower).

Example:

    {
      "revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "metrics": {
        "task_success_rate": {"value": 0.92, "direction": "higher"},
        "p95_latency_ms": {"value": 180, "direction": "lower"}
      }
    }

The numbers must come from a real benchmark run. The comparator does not invent or collect measurements.

## Decisions

- BLOCKED: invalid revision, missing or mismatched metrics, non-finite values, or changed metric direction.
- REJECTED_REGRESSION: any metric regressed.
- NO_MEASURED_IMPROVEMENT: no metric regressed, but no metric improved.
- ELIGIBLE_FOR_REVIEW: at least one metric improved and none regressed.

ELIGIBLE_FOR_REVIEW is not approval. promotion_authorized and deployment_performed always remain false; an independent reviewer, broader test suite, security gates, and explicit deployment authorization are still required.

## Learning loop (target operating contract)

1. Observe a real task and capture baseline metrics with pinned source revision.
2. Record failure, counterexample, environment, input/output digests, and reproducible steps.
3. Propose a bounded candidate on an isolated branch or sandbox.
4. Run the same benchmark and required correctness/security/regression suite.
5. Compare candidate to baseline using this gate.
6. Reject regressions; retain the failed experiment and reason in lineage (do not erase it).
7. Independently review improvements and promote only through a governed workflow.
8. Monitor the promoted version; if production metrics regress, stop rollout and restore the last known-good revision through an authorized rollback procedure.
9. Update capability/memory records only with provenance and verification status; distinguish observations from conclusions.

## Safety and truth boundaries

- No self-modification of canonical authority, project.genome, or Ω.000.
- No automatic production changes or unbounded recursive loops.
- Missing evidence is not zero, success, or proof.
- Scores from different benchmark versions are not compared without an explicit compatibility decision.
- Rollback is a deployment responsibility; this comparator does not perform it.
- This feature does not make a live VX connection and does not establish autonomous learning. It is a first enforceable building block toward measured, evidence-gated improvement.

## Run

    python scripts/vx_mission_runner.py .github/missions/vx-gate-self-check.v1.json --output build/vx/vx-gate-self-check-receipt.json
    python -m unittest tests.test_vx_nonregression_gate tests.test_vx_mission_runner -v
    python scripts/vx_nonregression_gate.py baseline.json candidate.json --output build/vx/nonregression-report.json

Exit codes for the benchmark comparator: 0 for review-eligible or no-measured-improvement reports, 1 for rejected/blocked candidate reports, 2 for unreadable or invalid input files.
