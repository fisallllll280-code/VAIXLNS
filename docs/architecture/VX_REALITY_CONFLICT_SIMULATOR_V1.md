# VX Reality & Conflict Simulator v1

Status: IMPLEMENTATION CANDIDATE — TESTS REQUIRED — NOT PRODUCTION VERIFIED

## Purpose

Deterministically detect selected contradictions across supplied system snapshots,
declared dependency versions, shared contract invariants, and registry identifiers.
The simulator is read-only and emits a report with evidence and a stable SHA-256 digest.

## Checks in v1

- Duplicate registry identifiers.
- Conflicting exact dependency version declarations.
- Conflicting values for the same explicitly declared contract invariant.
- Promotion block when a HIGH or CRITICAL finding exists.

## Run

    python -m unittest tests.test_vx_reality_conflict_simulator -v
    python scripts/vx_reality_conflict_simulator.py --systems systems.json --contracts contracts.json --registry registry.json --output report.json

Each supplied input must be a JSON array of objects. Systems use `system_id` and
`dependencies`; contracts use `system_id` and `invariants`; registry records should
include `id`, `system_id`, or `instance_id`.

## Required safety behavior

- Never auto-edit source systems or auto-approve a repair.
- Missing data is not proof of absence and is not automatically labeled a conflict.
- A clean result is limited to the supplied snapshots and checks.
- HIGH/CRITICAL conflicts block promotion until reviewed and resolved.
- Any repair must be simulated in isolation and re-tested independently.
- Production rollout requires source integration, authenticated inventory, access controls, CI enforcement, and explicit approval.

## Known limitations

This version does not perform semantic reasoning over arbitrary source code, prove
formal correctness, infer every possible conflict, access live systems, or model legal
or financial rules automatically. Expand only through explicit checks and tests.
