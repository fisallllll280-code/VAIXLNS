# Legacy Archive Research & Engineering Toolchain v1.0

## Purpose

Implement a lossless, evidence-first ingestion layer for historical VAIXLNS/NEXENT material. It complements, rather than replaces, `innovation_control/research_fabric.py`. Research Fabric investigates claims and candidate novelty; this engine atomizes source documents, preserves provenance, detects exact repetition, proposes similarity links, and exposes deterministic retrieval.

## Current boundary

- Input is source text supplied by an approved local-file, GitHub, archive, or document adapter.
- This module performs no network requests and makes no external provider claims.
- No source, row, ID, or lineage edge is deleted or merged.
- Similarity is a review signal, never a merge authorization.
- A record without an explicit historical ID remains present and is flagged.
- Expected but unseen legacy IDs are emitted as gaps, not synthesized.
- Search is deterministic lexical retrieval. Semantic embeddings and live source adapters are future integrations, not claimed implemented here.

## Pipeline

`SOURCE → HASH → ATOMIZE → PRESERVE LEGACY ID → EXACT-REPEAT REPORT → SIMILARITY REVIEW → SEARCH → JSONL EXPORT`

Each atomic record retains source URI, source content SHA-256, source ID, ordinal, raw body, and an independent record UID. UIDs are reproducible for identical source URI, revision, content, and record position.

## Status separation

Use the repository's status vocabulary without conflation:

- `RECOVERED`: source record extracted with provenance.
- `PROPOSED`: hypothesis or unconfirmed relationship.
- `IMPLEMENTED`: implementation artifact exists.
- `VERIFIED`: reproducible evidence supports the specific claim.
- `CANONICAL`: authorized canonical placement.
- `MISSING`, `CONFLICT`, `UNRESOLVED`: gaps retained for investigation.

Extraction alone must never promote a record to IMPLEMENTED, VERIFIED, or CANONICAL.

## Required next adapters

1. Read-only filesystem and uploaded-archive adapter with byte-preserving source hashes.
2. GitHub adapter for repository trees, commits, branches, tags, and file history.
3. Arabic/English normalization and transliteration-aware search.
4. Optional vector index, always retaining exact source snippets and source hashes.
5. Machine-readable historical manifest, once the actual 0001–2750 source is found.

## Acceptance gates

- Stable IDs and SHA-256 hashes across repeat runs.
- Every extracted record links to a source and source digest.
- Exact duplicates are reported while both records remain.
- Missing historical IDs are enumerated, never fabricated.
- Similarity candidates remain human-review-only.
- Export is deterministic JSONL.
- No network, deletion, merge, or canonical promotion is performed by this module.
