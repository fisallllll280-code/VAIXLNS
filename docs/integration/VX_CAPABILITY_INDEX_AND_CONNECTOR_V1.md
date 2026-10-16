# VX Capability Index and Read-only Connector — V1

**Status:** Reference slice implemented; live GitHub smoke test and CI evidence pending.

## Ownership and boundaries
- **VAIXLNS** owns canonical identity, governance, project.genome, and the Ω.000 reference. This slice does not rewrite either canonical artifact.
- **NEXENT** discovers and compares capabilities and proposes changes; it cannot admit tools.
- **VX** is the dispatch boundary and checks trusted caller identity, explicit scope, registration, and read-only mode before invoking the adapter.
- **VLNS** remains a governed semantic/model activation boundary. This slice does not claim a live VLNS integration.
- **VV / ARC-X** independently verify source provenance, tests, receipts, and index digests before any VERIFIED promotion.

## Capability index
Run:
    python tools/vx_capability_gateway.py --root . --repo-id fisallllll280-code/VAIXLNS --ref <commit-or-branch> --output registry/capability-index.v1.json

Each selected source/document record contains relative path, SHA-256, byte size, source repository/ref, and a coarse capability classification. content_digest hashes canonical JSON for the records; generated_at is informational and excluded from the digest. Output is written with fsync and atomic replacement; a failed write leaves the previous file intact. The index is a projection, not a replacement for Ω.000.

## Connector contract
The sole adapter in this slice is github.read_file, using the GitHub Contents API with GET only. The host must supply trusted authenticated identity context and a trusted registry entry with status=ADMITTED and mode=read_only. Required scope is github.read_file. Unknown tools, missing identity/scope, invalid paths and malformed upstream responses fail closed. An optional GITHUB_TOKEN is used only for the request and is never returned or logged. The module does not validate OAuth/JWT signatures itself; the calling host remains responsible for authenticating identity.

## Verification and performance
Run:
    python -m unittest discover -s tests -p 'test_capability_index.py' -v

Tests use a deterministic fake HTTP response and cover connector dispatch, identity/scope rejection, unregistered tools, path traversal, hash changes and atomic index replacement. They do not prove live GitHub access.
For a performance baseline, run the index builder repeatedly on the same checkout and record file count, median/p95 duration, runtime and machine. This implementation has not been benchmarked against a previous implementation, so no speedup claim is made. A live connector smoke test and CI run remain required for VERIFIED status.
