# SIRAP — Index Recovery Gap Closure Register (2026-10-21)

Status: AUDIT BASELINE / NOT CANONICAL / NO VERIFIED PROMOTION.

## Scope and invariants
- Canonical authority: VAIXLNS. VX routes review and execution; no direct federation implied.
- Immutable protected files: `project.genome`, `Ω.000`. No changes or automatic merge.
- Preserve Original / Derived, exact source paths and Git commit, raw hashes and normalized digests separately.
- `NOT_OBSERVED` and `INACCESSIBLE` must never be promoted to `MISSING` without a complete bounded source inventory.
- A document claiming ACTIVE, ENFORCED, VERIFIED, or PROVED is not itself runtime evidence.
- Declared historical 0001–2750 coverage is NOT complete.

## Existing implementation: reuse first
- `scripts/recover_zero_loss_index.py` orchestrates unit tests, `scripts/build_zero_loss_index.py`, verification, five artifacts and a recovery receipt.
- `registry/indexes/zero-loss-index-taxonomy.v1.json`: 28 index views (00–27).
- `docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md`: ordered Git-tree inventory from a pinned snapshot; file display IDs are not historical Ω IDs.
- `docs/recovery/VAIXLNS_GAP_REGISTER_2026-10-06.md`: GAP-012..018 unresolved in that historical baseline.
- `docs/indexes/README.md` explicitly says legacy 0001–2750 atomic rows are not fully exposed.

## Evidence-graded backlog (not asserted closed)
| Finding | Item | Observed basis | Required closure proof | State |
|---|---|---|---|---|
| SIRAP-001 | Historical 0001–2750 | docs/indexes/README.md; GAP-015 | atomic records + source links + gap coverage + reproducible receipt | OPEN |
| SIRAP-002 | Semantic constitutional admission | GAP-012 | policy tests and independent admission evidence | OPEN |
| SIRAP-003 | Runtime telemetry | GAP-013 | OpenTelemetry export/integration receipt | OPEN |
| SIRAP-004 | Branch protection | GAP-014 | live API ruleset evidence and required reviews | REVIEW |
| SIRAP-005 | Cross-repository consolidation | GAP-016 | interface contracts, lineage, tests, no duplicate runtimes | OPEN |
| SIRAP-006 | Full reconstruction | GAP-017 | pinned restore, semantic equivalence and replay evidence | OPEN |
| SIRAP-007 | Financial execution | GAP-018 | independently admitted end-to-end execution, not mock revenue | BLOCKED |
| SIRAP-008 | Uploaded React SIRAP dashboard | user-provided React source | replace mock findings and setTimeout 'scan' with authorized backend + real receipts | REVIEW |
| SIRAP-009 | Model/realm naming | ordered index notes VLNS/NAXLNS and NEXNET/NEXENT unresolved identity | authoritative explicit mapping proof | REVIEW |

## Uploaded dashboard discrepancies (source-based)
The uploaded source contains `SIRAP_MOCK_FINDINGS` with Ω.0950, Ω.0812, Ω.0401, Ω.1022. Those entries are mock fixtures, not observed repository findings. The scan button runs `setTimeout` without source enumeration. Causal impact figures and grammar proof claims are hard-coded examples. Those must not be emitted as VERIFIED or measured outcomes. The audit score UI currently calls scores >=80 'acceptance'; correct to advisory-only, require all applicable gates G0–G5.

## Execution order and gates
1. Pin SHA of each accessible repository; capture permission/branch list, tree coverage and inaccessible sources.
2. Reuse existing zero-loss builder/tests; archive raw logs, exit codes, SHA-256 of artifacts, immutable commit identities.
3. Compare normalized identity, filenames, provenance and contract references; classify candidate duplicates for human review.
4. Emit machine ledger: finding_id, source_repo, source_commit, raw_sha256, normalized_hash, classification, evidence_refs, confidence, owner, decision, review_status, audit_run_id.
5. Run G0 source, G1 schema, G2 invariants, G3 tests, G4 authority, G5 replay. Any required FAIL/HOLD blocks VERIFIED.
6. Review fixes only on isolated branches; close with independent rerun. No main merge without authorization.

## Source links
- https://github.com/fisallllll280-code/VAIXLNS/blob/main/docs/indexes/README.md
- https://github.com/fisallllll280-code/VAIXLNS/blob/main/scripts/recover_zero_loss_index.py
- https://github.com/fisallllll280-code/VAIXLNS/blob/main/docs/recovery/VAIXLNS_GAP_REGISTER_2026-10-06.md
- https://github.com/fisallllll280-code/VAIXLNS/blob/main/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md

## External compatibility references
GitHub Git Trees can return truncated recursive trees; `truncated=true` requires per-subtree traversal. GitHub SARIF ingestion requires stable rule IDs/paths/fingerprints and eligible code scanning permissions:
- https://docs.github.com/en/rest/git/trees
- https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/sarif-support

The present file is a documented audit baseline, **not** proof that recovery scripts were executed nor that gaps were fixed.
