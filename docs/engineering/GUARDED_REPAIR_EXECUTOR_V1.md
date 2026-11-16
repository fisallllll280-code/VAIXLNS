# Guarded Repair Executor v1

## Objective

Provide a bounded way to apply a precisely reviewed text repair to a local Git checkout. The executor is the write phase after diagnostic triage; it does not invent a fix, run arbitrary commands, install software or report tests as passing.

## Repair-plan contract

The plan is defined by schemas/guarded-repair-plan.v1.schema.json and has these required fields:

- schema_version: 1.0.0.
- repair_id: stable identifier for the proposed patch.
- repository: GitHub owner/repository identity, matched against origin.
- base_revision: exact 40–64 character Git commit identifier.
- change: one existing file, operation replace_text, expected_sha256 of the whole preimage file, old_text, new_text and optional expected_occurrences (default 1).

Only one file is allowed per plan in v1 to keep each replacement atomic and reviewable. Use separate plans for separate files. Plans cannot request shell commands or arbitrary operations.

## Safe execution

Dry-run is the default:

python tools/guarded_repair_executor.py repair-plan.json --root .

Application is explicit:

python tools/guarded_repair_executor.py repair-plan.json --root . --apply

Application requires the plan revision to match HEAD, origin to match the declared repository, and a clean working tree. The target must be an existing UTF-8 regular file inside the repository. Traversal, symlink paths, non-unique anchors, stale preimage hashes, unknown operations and canonical authority files are rejected. The output file is replaced atomically.

## Evidence states

- PATCH_CANDIDATE_READY: preconditions pass; no file was changed.
- PATCH_APPLIED_NOT_VERIFIED: the requested replacement was applied and its postimage hash was recorded.
- BLOCKED: preconditions did not pass.

No status from this tool means tests passed. Verification requires an observed reproduction, targeted regression, the relevant repository suite, independent review and evidence attached to the precise commit. The executor deliberately has no command runner, network client or model-provider connection.

## Cross-platform validation

The focused GitHub Actions workflow runs the executor regression tests on Ubuntu and Windows runners using only Python standard-library functionality plus Git. This demonstrates tested tool paths on those CI runners only; it does not certify every Windows installation or connect to a Microsoft service.
