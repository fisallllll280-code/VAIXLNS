# VAIXLNS Knowledge Genome Engineering Slice v1

**Status:** IMPLEMENTATION CANDIDATE — LOCAL TEST EVIDENCE REQUIRED BEFORE ADMISSION
**Canonical authority:** `project.genome::v1.0.0` / `Ω0_GENESIS_CORE`
**Registry relationship:** extend existing `Ω.000`, `REPOSITORY_DECISION_REGISTER_V1.md`, `INNOVATION_MASTER_INDEX.md`, and ARC-X; do not replace them.

## Purpose

Create a deterministic, provenance-preserving file-level source inventory that can be used by ARC-X reconstruction. A repository is a source surface, not the Knowledge Genome itself. The tool produces stable artifact identifiers, SHA-256 content fingerprints, transparent path/name classification hints, resolvable/unresolved local Markdown reference edges, and exact byte-duplicate edges.

## Boundaries

- It is a file-level inventory, not a semantic understanding engine.
- It never edits source files, GitHub repositories, registry entries, or canonical state.
- It never deletes, merges, renames, moves, or archives repositories or artifacts.
- Sensitive-key/credential-like files are excluded; oversize files, symlinks, excluded build/cache directories, and in-repository baseline/output control files are counted or explicitly excluded.
- Baseline and output files are excluded from the scan when they reside inside the scanned tree, preventing self-referential reports. A hash proves byte equality only. It does not prove correctness, semantic equivalence, authority, completeness, or runtime behavior.
- The report remains `PARTIAL`; records state `semantic_status: NOT_EXTRACTED`.
- Git revision is captured only when the root is a Git checkout. A dirty working tree is explicitly labeled `DIRTY_OR_UNKNOWN`; run against a clean, pinned checkout for release evidence.

## Pipeline

`PINNED CHECKOUT → SAFE FILE WALK → STABLE ARTIFACT ID → SHA-256 → NON-AUTHORITATIVE HINTS → LOCAL LINK GRAPH → OPTIONAL BASELINE DIFF → FINGERPRINTED REPORT`

## Record identity

`artifact_id = KG.FILE + first20(uppercase(SHA-256(repository_id + NUL + relative_path)))`

This identifier is stable across content edits at the same repository path. `content_sha256` identifies the observed file bytes. A changed hash therefore changes the file revision evidence without silently changing the artifact identity. If a file disappears relative to a baseline, the old ID is written to `missing_from_current_snapshot`; this is not a delete instruction.

## CLI

```bash
python scripts/knowledge_genome.py . \
  --repository-id fisallllll280-code/VAIXLNS \
  --output /tmp/vaixlns-knowledge-genome.json

python scripts/knowledge_genome.py . \
  --repository-id fisallllll280-code/VAIXLNS \
  --baseline /tmp/previous-knowledge-genome.json \
  --output /tmp/current-knowledge-genome.json
```

## Admission gates

1. Unit tests pass for determinism, stable identity, secret exclusion, local-link edges, changed/missing baseline handling, size limits, and non-promotion.
2. JSON output conforms to `schemas/knowledge-genome.schema.json`.
3. Execute against a clean, pinned repository snapshot and preserve stdout, commit SHA, and report SHA-256 as evidence.
4. ARC-X integration review confirms the artifact record aligns with existing evidence/provenance schemas; no duplicate canonical registry is introduced.
5. A separate authority-controlled change may then register the tool in Ω.000. This implementation does not grant itself canonical authority.

## Known limitations / next increments

- Remote federation retrieval and pagination are not implemented here.
- Language-aware dependency/import parsing and semantic extraction are not implemented here.
- Contradiction detection, duplicate-semantic detection, capability graph synthesis, and evidence-strength evaluation require separate typed extractors and independently tested logic.
- The current Markdown resolver intentionally handles local relative links only; anchors are stripped for target lookup. Local links that escape the repository are reported as unresolved boundaries.
- Exact-byte duplicate edges do not collapse records and do not imply semantic equivalence.
- Source-level scanning is not a malware scanner or secret-scanning replacement.
