# VAIXLNS Operational Bootstrap

## Required lifecycle
DEFINE → GENERATE → BOOT → EXECUTE → RECORD → VERIFY → PROVE → COMMIT → OPERATE → RECOVER → EVOLVE

## Repository organization policy
1. Preserve source history.
2. Classify before merging.
3. Prefer one canonical owner per responsibility.
4. Keep variants as lineage rather than silently deleting them.
5. Separate specification, implementation, experiments and generated artifacts.
6. Every executable component must expose contract, state, events, evidence and recovery boundaries.
7. Do not mark IMPLEMENTED or RUNNING without repository evidence.

## First integration targets
- canonical registry
- VX execution boundary
- OIF operational assurance
- verification/proof boundary
- NEXENT discovery boundary
- CI validation and repository health checks
