# VX Capability Non-Regression & Evidence Gate v1

**Status:** IMPLEMENTED AS A LOCAL EVALUATOR + UNIT TESTS; not yet CI-verified on this branch and not connected to a live VX runtime.

## Objective

Make improvement a measured engineering loop rather than a promise that a system can never fail. VX should preserve known-good capabilities, learn from measured outcomes, propose bounded improvements, and reject candidates that regress any required metric.

Absolute zero degradation cannot be guaranteed in every environment. This gate makes a narrower, enforceable promise: **a candidate with a measured regression against the pinned benchmark is not eligible for promotion by this gate**.

## Components

- scripts/vx_nonregression_gate.py: deterministic JSON benchmark comparator.
- tests/test_vx_nonregression_gate.py: regression, missing-data, metric-direction, revision, and determinism tests.
- .github/workflows/vx-nonregression-gate.yml: run focused tests for changes to the gate.

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
- This feature does not make a live VX connection and does not establish autonomous learning. It provides one enforceable building block toward measured, evidence-gated improvement.

## Run

    python -m unittest tests.test_vx_nonregression_gate -v
    python scripts/vx_nonregression_gate.py baseline.json candidate.json --output build/vx/nonregression-report.json

Exit codes: 0 for review-eligible or no-measured-improvement reports, 1 for rejected/blocked candidate reports, 2 for unreadable or invalid input files.
