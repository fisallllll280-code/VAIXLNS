# Omega Readiness Bridge — executable slice v1

Status: **implemented locally in repository source; CI evidence pending**.
This module evaluates a supplied JSON observation packet. It does not probe machines,
call cloud APIs, dispatch workloads, authorize people, or establish production readiness.

## Run

```bash
python -m unittest discover -s tests -p "test_omega_readiness_bridge.py" -v
python scripts/omega_readiness_bridge.py fixtures/omega-readiness/synthetic-ready.json --output /tmp/readiness-report.json
```

The sample is explicitly synthetic. A READY result means only that the provided packet
passed this evaluator's contract; it is not evidence that a real node or service is live.

## Input contract

- `capability_id`, timezone-aware `observed_at`, and `max_age_seconds`
- hard-gate statuses: availability, integrity, dependencies, capacity, security,
  recovery, governance, evidence_quality
- dependency records with IDs, statuses, and fresh timestamps
- evidence records with references, SHA-256-shaped digests, verified=true, and timestamps

Missing/invalid/stale/future observations, failed dependencies, missing hard gates,
and missing valid evidence fail closed. Reports include blockers, a deterministic
SHA-256 digest over the report before the digest field is added, and explicit
`execution_performed=false` / `external_calls_performed=false` fields.

## Boundary and next integration

The evaluator now includes an in-process adapter for the existing VX Stage instance contract. The adapter reads stage state/capability/authority scope, while requiring independent explicit inputs for integrity, capacity, recovery, governance, dependencies and evidence. Contract tests cover both a fully evidenced synthetic Stage instance and an ACTIVE instance with missing gates. This is not a live telemetry adapter or a leadership UI; only synthetic fixtures are used. Human review remains
mandatory and the module is not intended to rank or determine the fitness of individuals.
