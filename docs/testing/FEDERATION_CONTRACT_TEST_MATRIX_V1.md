# Federation Contract Test Matrix — Enforcement Slice 001

**Status:** SPECIFIED; tests are not marked VERIFIED until CI or a local run produces a receipt tied to the tested commit.
**Canonical boundary:** additive-only. Do not modify `project.genome` or `registry/omega/omega-000-master-index.json`.
**Execution boundary:** these tests validate offline declarations only; they do not connect adapters, grant authority, or execute production work.

| ID | Invariant | Negative/positive case | Expected result | Evidence status |
|---|---|---|---|---|
| FED-001 | Required typed edges exist | Remove or misdirect a required edge | Validation errors | NOT RUN |
| FED-002 | Unverified identity blocks activation | Enable VLNS or NEXNET edge | Validation errors | NOT RUN |
| FED-003 | Explicit authority is required | Remove grant requirement or self-authorization prohibition | Validation errors | NOT RUN |
| FED-004 | Active edge requires source revision | Omit or malformed commit SHA | Validation errors | NOT RUN |
| FED-005 | Evidence is independently reviewed | Submitter equals reviewer | Validation errors | NOT RUN |
| FED-006 | Evidence digests are well-formed | Invalid evidence or verification digest | Validation errors | NOT RUN |
| FED-007 | Evidence cannot implicitly promote non-active edge | Add receipt while status is non-active | Validation errors | NOT RUN |
| FED-008 | Preflight is not runtime proof | Valid declarations with unresolved identity | BLOCKED; runtime_observed=false | NOT RUN |
| FED-009 | Preflight report is deterministic | Same inputs in repeated calls | Same report digest | NOT RUN |
| FED-010 | Canonical artifacts are preserved | Compare canonical blob identities before/after branch | No canonical file changes | NOT RUN |

## Required activation evidence fields

An `ACTIVE_VERIFIED` edge must include non-empty `source_revision`, `evidence_uri`, `observed_at`, `submitted_by`, `reviewer_id`, and `reviewed_at`; `source_revision` must be a full 40-character Git commit SHA; `digest` and `verification_digest` must be 64-character SHA-256 hex digests; the submitter and reviewer must differ.

This schema-level check establishes only that the receipt is well-formed. It does **not** establish that the URI is reachable, the evidence is truthful, the reviewer is authorized, or the source revision is the current deployment. Those require separate evidence admission and policy checks.

## Run

```bash
python -m unittest tests.test_federation_contract_edges tests.test_federation_preflight -v
python scripts/validate_federation_contract_edges.py
python scripts/federation_preflight.py
```

Record the exact commit SHA, CI run URL, command, exit status, and raw output before changing any row from `NOT RUN`.
