# VAIXLNS × VX — Index Evidence & G0 Continuation (2026-10-25)

Status: AUDIT / NOT VERIFIED. Branch: `audit/vx-index-evidence-20261025`.
Authority: VAIXLNS; no canonical promotion or release authorized.

## Observed in repository (read-only connector inspection)
- `scripts/recover_zero_loss_index.py` exists and orchestrates unit tests, a 28-view build, verification, and a JSON recovery receipt.
- `.github/workflows/zero-loss-index.yml` exists and invokes tests, build, verify and integrated recovery.
- `schemas/zero-loss-atomic-record.schema.json` exists and defines source-bound atomic records.
- `deploy/federation/INDEX_RECOVERY_RUNTIME_PROTOCOL.md` explicitly states that the document is a specification, not proof of production runtime.
- `docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md` is a historical pinned inventory, not current coverage proof.

## Identified gaps requiring verification
1. The recovery receipt currently includes `source_root` but does **not** explicitly record a pinned `source_revision` commit SHA. A filesystem path is not revision evidence. Add an immutable revision identifier to the receipt, and reject/declare unpinned contexts according to the contract.
2. The orchestrator returns process code 0 for `PASS_WITH_DECLARED_GAPS`. Downstream admission must consume the receipt's status, not merely its exit code; a zero exit is not full historical recovery.
3. The receipt records a `--skip-tests` execution without an explicit `tests_skipped` flag. Include an unambiguous skip indicator and ensure skipped tests never confer VERIFIED.
4. A CI workflow definition is not a successful Actions run. Fetch run logs and commit SHAs before any verification claim.
5. Recovering 28 index **views** does not establish coverage of historical identities 0001–2750+.
6. `VLNS/NAXLNS` and `NEXNET/NEXENT` identity equivalence remains unproved; keep explicit review states.

## Minimal next implementation slice
- Extend the existing recovery orchestrator; do **not** create a parallel index engine.
- Add tests for pinned source revision, `--skip-tests`, unresolved gaps, absent artifacts, mismatched digests, and fail-closed admission.
- Rerun existing suites and GitHub Actions on this branch; capture exact run URLs, SHA, exit codes, artifacts, and protection hashes.
- Execute VX-INT-EXEC-001 in order T01–T05 → T06–T10 → T15 → T11–T14 only after G0 gate passes.
- Mark each test NOT_RUN until actual execution is observed. Gate G0 is HOLD pending evidence.

## Hard constraints
- No edits to `project.genome` or `Ω.000`.
- No automatic merge to `main`; no deployment; no paid API calls.
- No unverifiable VERIFIED claims, silent deletion, historical renumbering, or direct federation bypassing VX.
- Draft audit content is not implementation proof.
