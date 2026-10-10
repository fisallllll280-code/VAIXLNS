# Ω-IMpossibility Engine V1 — Executable Prototype

**State:** IMPLEMENTED ON BRANCH; verification pending CI. Not canonical and not a general impossibility solver.

## Purpose

Turn a vague "impossible" claim into a conservative, evidence-oriented engineering assessment. The first version is deterministic and dependency-free. It detects explicit numeric range contradictions, identifies missing specification/evidence, and emits a staged feasibility plan plus alternative routes.

## Run

From the repository root with Python 3.11+:

```powershell
python -m unittest tests.test_impossibility_engine -v
@'
{
  "title": "Low-latency design",
  "goal": "Respond within 40 ms under the stated load",
  "constraints": [
    {"kind": "range", "variable": "latency_ms", "min": 0, "max": 40}
  ],
  "resources": ["local benchmark host"],
  "evidence": [{"state": "OBSERVED", "ref": "baseline-run-001"}]
}
'@ | python -m tools.impossibility_engine
```

## Output contract

- `CONTRADICTION_DETECTED`: a supported contradiction was found in declared numeric range constraints.
- `INSUFFICIENT_SPECIFICATION`: goal, constraints, or evidence are missing.
- `ENGINEERING_CHALLENGE`: no contradiction was detected; feasibility remains unproven.

The engine never equates "not disproven" with "possible", and never promotes a result to `VERIFIED`. It performs no network calls, model calls, shell execution, repository writes, or external side effects.

## Next implementation gates

1. Add domain-specific constraint plugins with explicit assumptions and unit validation.
2. Add proof-obligation records and evidence provenance schemas.
3. Add a sandboxed experiment adapter only after threat modeling and independent permission checks.
4. Compare decisions against a human-labeled adversarial benchmark; report false-positive/false-negative rates.
5. Only then consider agent/model integrations, behind explicit adapters and budgets.

## Canonical boundary

This prototype is a proposal/implementation branch. It does not modify `project.genome`, `Ω0_GENESIS_CORE`, or `Ω.000`. Novelty and scientific completeness remain unassessed.
