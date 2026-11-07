# VAIXLNS-ARCHIVE

Immutable historical preservation surface inside the canonical repository until a dedicated GitHub archive repository is provisioned.

Rules:
- Preserve source repository, ref, version, commit, path, digest, and lineage.
- Never overwrite a historical snapshot.
- Every snapshot is append-only.
- Canonicalization creates a pointer; it does not destroy the source.

Snapshot naming: `ARCHIVE-YYYYMMDD-HHMMSS`.

See `archive/repository_snapshots.v1.json` and `registry/version_registry.v1.json`.
