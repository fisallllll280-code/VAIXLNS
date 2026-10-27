# Evidence-First Execution and Test Map

Snapshot drafted 2026-10-27 from repository README and index navigation. This document is a mapping plan, not a test run.

## G0 prerequisite checklist
- [ ] Record full commit SHA and dirty-state indicators for each included repository.
- [ ] Review main branch drift relative to pinned baseline.
- [ ] Verify SHA-256 before/after for project.genome and Ω.000 without modifying them.
- [ ] Confirm no auto-merge, no auto-publish, no chargeable external actions.
- [ ] Confirm isolated worktree/container and test dependencies.
- [ ] Identify CI promotion blockers/secrets without exposing secret values.
- [ ] Produce G0 receipt and independent review.
Decision: BLOCKED / NOT_RUN until proven otherwise.

## Mandatory sequence
| Group | IDs | Requirement | State |
|---|---|---|---|
| G0 | prerequisite | PASS with independent receipt | NOT_RUN |
| Foundation | T01–T05 | Verified source-based entrypoints, execute only after G0 | NOT_RUN |
| Integration | T06–T10 | Execute only after Foundation pass | NOT_RUN |
| Intermediate | T15 | Execute only after Integration pass | NOT_RUN |
| Final | T11–T14 | Execute only after T15 pass | NOT_RUN |

For EACH test capture test_id, repo, commit_sha, test_path, exact_command, environment, prerequisites, expected, observed, exit_code, timestamp, logs_uri, sha256, independent_reviewer, decision. Unknown mapping must remain NOT_MAPPED.

## Candidate EXISTING commands shown in VAIXLNS README
These are documentation-backed candidate checks; they are not assigned to T IDs without reviewing the authoritative test plan:

```bash
python scripts/federation_preflight.py
python scripts/validate_four_system_federation.py
python scripts/validate_federation_contract_edges.py
python -m unittest tests.test_four_system_federation tests.test_federation_contract_edges tests.test_federation_preflight -v
python scripts/omega_arena_audit.py --output build/omega-arena/audit-receipt.json
python -m unittest tests.test_omega_arena_audit -v
```

Offline preflight and audit inspect static configuration only: they DO NOT prove that external service endpoints are live.

## Demo proof journey
Demand → VV request → identity/policy gate → VX authorized dispatch → sandbox execution → evidence sink → deterministic replay → signed review.
Record failure-injection and denied-action scenarios, otherwise do not claim enforcement.
