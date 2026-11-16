# VX Ω-Arena Runtime v1 — isolated implementation

Status: IMPLEMENTED AS AN ISOLATED SOURCE CANDIDATE; NOT TESTED IN THIS REMOTE WRITE SESSION; NOT VERIFIED; NOT PROMOTED.

## Scope
This additive package supplies deterministic candidate scoring, an in-memory SHA-256 evidence chain, replay verification, and a fail-closed promotion eligibility gate. It uses only the Python standard library.

## Safety boundary
- No network calls or provider invocation.
- Provider descriptors are metadata only; live invocation is always disabled.
- Scores are scoped to a frozen task and do not establish a permanent winner.
- Promotion eligibility is not promotion. Merge and deployment are never performed.
- Canonical files `project.genome` and `Ω.000` are outside this change.
- Synthetic fixtures must never be reported as live provider results.

## Local verification
Run: `python -m unittest tests.test_vx_omega_arena_runtime -v`

A passing local test run and a revision-bound CI receipt are required before marking this candidate VERIFIED.
