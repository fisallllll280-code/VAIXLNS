# VX / VLNS Pinned Repository Snapshot Capture v1

**Status:** IMPLEMENTATION CANDIDATE — repository snapshots remain pending until this tool is run against a pinned plan and its receipts are reviewed.

## Purpose

Produce a revision-bound, restorable snapshot for the four repository references already registered by the VX/VLNS continuity manifest:

- fisallllll280-code/VX50_COMPLETE_BUILD
- fisallllll280-code/VX-runtime
- fisallllll280-code/NAXLNS
- fisallllll280-code/NEXENT

The NEXENT entry is a source/specification reference; snapshotting it does not prove a separate VLNS runtime exists.

## Immutable input plan

Create a local JSON plan whose schema is VAIXLNS.PinnedSnapshotPlan.v1 and whose repositories array contains each of the four repository names exactly once, with a full 40-character commit SHA for each. Do not pass a branch name or moving tag as the revision.

Example shape (replace each all-zero placeholder with the independently inspected full commit SHA):

    {
      "schema": "VAIXLNS.PinnedSnapshotPlan.v1",
      "repositories": [
        {"repository": "fisallllll280-code/VX50_COMPLETE_BUILD", "commit_sha": "0000000000000000000000000000000000000000"},
        {"repository": "fisallllll280-code/VX-runtime", "commit_sha": "0000000000000000000000000000000000000000"},
        {"repository": "fisallllll280-code/NAXLNS", "commit_sha": "0000000000000000000000000000000000000000"},
        {"repository": "fisallllll280-code/NEXENT", "commit_sha": "0000000000000000000000000000000000000000"}
      ]
    }

Validate before network access:

    python scripts/capture_pinned_repo_snapshots.py --plan ./local-pinned-plan.json --output-dir ./secure-snapshots --validate-plan-only

Capture and restore-test:

    python scripts/capture_pinned_repo_snapshots.py --plan ./local-pinned-plan.json --output-dir ./secure-snapshots

Exit code 0 means every planned repository has a clean capture and restore test. Exit code 2 means the batch is blocked or incomplete; inspect each per-repository receipt and blocker.

## Artifacts per repository

- Git bundle: refs and reachable Git history from a mirror clone, including a temporary ref to the pinned commit.
- Source-tree TAR.GZ: the tracked source tree at the exact pinned commit, including dotfiles and symlink entries.
- File inventory JSON: per-file SHA-256, sizes, symlink-target hashes, Git LFS pointer declarations, submodule gitlinks, and the aggregate source-tree inventory digest.
- Snapshot receipt JSON: repository/commit identity, bundle and tree digests, restore-test results, blockers, and non-claims.
- Batch receipt JSON: batch status and plan digest.

The tool clones from GitHub over HTTPS and creates derived artifacts only in the selected local output directory. It never writes to source repositories, project.genome, Ω.000, or the continuity manifest. The output contains repository history and should be stored as a protected backup, not committed into the canonical repository without a separate storage/security review.

## Fail-closed conditions

A source-tree restore test and a Git bundle restore test must both pass. GIT_LFS_PAYLOAD_NOT_CAPTURED and SUBMODULE_CONTENT_NOT_CAPTURED are blockers: the pointer/gitlink is recorded, but its payload is not falsely counted as recovered. Unsafe archive paths, non-UTF-8 Git paths, mismatched commit identities, digest mismatches, incomplete artifacts, or existing immutable destination paths also block the run.

## Acceptance gate

A snapshot may be marked PASS only when the requested commit is exact, the Git bundle can be restored and inspected, the source archive restores to the identical file inventory, all per-file digests match, and no LFS/submodule payload gaps remain. Snapshot success establishes source preservation for that pinned revision only. It does not prove runtime health, system identity, live connectivity, canonical admission, or complete recovery of the historical 0001–2750 index.
