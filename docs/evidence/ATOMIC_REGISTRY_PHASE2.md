# VAIXLNS Atomic Evidence Registry — Phase 2

## Purpose
Introduce a non-destructive, provenance-first registry contract for recovering architecture records from archived text.

## Canonical evidence boundaries
- `SOURCE_MENTION_ONLY`: heading extracted from a document. Not proof of working code.
- `UNVERIFIED_SYMBOL`: heuristic symbol occurrence. Not necessarily a component or canonical identity.
- `SPEC_ONLY`, `CONTRACTED`, `IMPLEMENTED`, `UNIT_TESTED`, `INTEGRATION_TESTED`, `RUNTIME_VERIFIED`, `REPLAY_VERIFIED`, `CANONICAL`: promotion states. Never infer promotion from prose.

## Source record contract
Required: `source_id`, `filename`, `sha256`, `bytes`, `lines`.

## Atomic heading mention contract
Required: `record_id`, `source_id`, `filename`, `line`, `level`, `title`, `path`, `status`, `implementation_evidence`, `source_sha256`.

## Validation gate
1. Source count equals input file count.
2. Unique stable source IDs.
3. Unique stable heading mention IDs.
4. Heading line references inside source boundaries.
5. Initial mentions must not claim implementation.
6. Recomputed SHA-256 equals source digest.

## Known limitations
- Historical 2,750 canonical positions are NOT asserted as recovered.
- Mentions are not deduplicated as entities and aliases are not merged silently.
- Execution, CI, runtime operation and integration are not verified by text indexing.
- This document defines an import and verification contract; it is not the full archive.

## Local audit evidence (2026-10-27)
76 source text files; 2,034 heading mentions; 9,159 symbol occurrences; 2,017 case-folded unique symbols; 81 URL mentions. Six structural checks passed on the locally supplied source files. The inputs are not yet committed to this GitHub branch.
