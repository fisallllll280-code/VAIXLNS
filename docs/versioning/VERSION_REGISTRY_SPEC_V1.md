# VAIXLNS Version Registry Specification v1

## Purpose

Track project versions without collapsing historical lineage.

## Version dimensions

1. Historical version — exact label found in the source project.
2. Canonical version — version assigned by the unified VAIXLNS release process.
3. Archive snapshot — immutable timestamped archive capture.
4. Recovery revision — a new restoration attempt; it never overwrites the archived source.

## Registry record

Each record should carry at minimum:
- item_id
- project_id
- source_repository
- source_ref
- historical_version
- canonical_version
- status
- supersedes
- superseded_by
- merged_into
- archived_at
- recovered_from
- content_digest
- lineage
- evidence

## Canonical release scheme

Use semantic versioning for executable/canonical releases: MAJOR.MINOR.PATCH.
MAJOR = incompatible canonical architecture/runtime contract change.
MINOR = backward-compatible capability or subsystem addition.
PATCH = correction, test, documentation, or non-breaking implementation repair.
This canonical number does not replace historical project versions.

## Snapshot naming

Archive snapshots use ARCHIVE-YYYYMMDD-HHMMSS.
Recovery operations use RECOVERY-YYYYMMDD-HHMMSS-N.

## Release gates

DRAFT -> BUILDABLE -> RUNNABLE -> INTEGRATED -> CONFORMANT -> REPRODUCIBLE -> VERIFIED
Only evidence-backed gates may advance a release.
