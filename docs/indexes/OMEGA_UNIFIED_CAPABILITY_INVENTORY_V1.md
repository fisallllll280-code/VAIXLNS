# Ω Unified Capability, Tool & Innovation Inventory — v1
Date: 2026-10-21
Status: WORKING / EVIDENCE-BOUND
Owner: VAIXLNS; execution authority: VX only.

## Scope
Read-only recovery across VAIXLNS, VX-runtime, VAIXLNS-unified, NEXENT, plus discoverable owned historical repositories and branches. Enumerate tools, agents, mathematical/physical/computational innovations, APIs, interfaces, libraries, indexes, tests and source lineage. Zero silent deletion.

## Verified source observations (not runtime verification)
- VAIXLNS docs/indexes/README.md records 28 Zero-Loss index views, a historical 0001–2750 target with incomplete item-level extraction, and a 97-item recovered review portfolio.
- VAIXLNS docs/indexes/INNOVATION_MASTER_INDEX.md enumerates at least 89 innovation entries, some descriptions being proposals, not execution proof.
- Existing builders/validators include tools/build_innovation_index.py, tools/build_innovation_operation_index.py, tools/validate_innovation_registry.py, tools/validate_innovation_operation_index.py, tools/validate_deep_innovation_register.py.
- NEXENT docs/NEXENT_COMPLETE_SYSTEM_AND_INNOVATION_INVENTORY.md defines atomic record, provenance, deduplication and status rules.
- VAIXLNS-unified docs/SYSTEM_EVOLUTION_STATUS_CARD_V1.md separates DOCUMENTED, CODE_PRESENT, TEST_REPORTED, UNVERIFIED.
These counts refer to differing units and MUST NOT be summed.

## Mandatory record contract
Each source item has immutable source_record_id, repository, path, revision_sha, content_sha256, original_name, exact excerpt location, retrieval timestamp, first_seen when provable, record_type, family, owner, originating_system, aliases, dependencies, canonical_candidate_id, authority, state, test_ref, evidence_ref, replay_ref, issue/conflict_refs.
Record type: INDEX_VIEW | TOOL | AGENT | INNOVATION | ALGORITHM | MODEL | LIBRARY | API | INTERFACE | TEST | SPEC.
State: RECOVERED | CANONICAL | PROPOSED | IMPLEMENTED | VERIFIED. Record separate fields for evidence_status and readiness_status; VERIFIED requires independently reproduced execution evidence.

## Recovery & reconciliation pipeline
1. Enumerate all visible repositories, branches, tags and archival paths; pin SHA for every input.
2. Run existing indexing builders in a disposable isolated environment; retain raw source files and command logs before generating projections.
3. Parse indexes/catalogs, registry/, docs/, tools/, agents, src, tests and workflows into append-only source records.
4. Compare exact content hashes; propose near-duplicates via normalized names, signatures, and dependency graphs. Never auto-merge semantic matches.
5. Preserve ORIGINAL and DERIVED lineage and all aliases; unresolved conflicts remain explicit.
6. Build stable canonical mapping and export searchable JSONL, SQLite FTS, and human-readable summary. No automatic authorization, promotion or main-branch merge.
7. Validate schemas, lineage completeness, test references, pinned commits, SHA-256, deterministic rebuild/replay and fail-closed policies.
8. Present coverage denominator (discovered source records) and unvisited source gaps; never call historic 2750 complete until individually reconciled.

## UI specification: Ω Registry Observatory
A searchable, filterable table (system / family / type / origin / state / evidence), record detail with provenance and dependency graph, conflict workbench, recovery coverage, missing-test queue, change diff, build receipt and evidence/replay links. Actions that modify runtime must pass VX admission, auth, governance and proof gates. Read-only by default.

## Acceptance gates
G0 complete source/repository discovery and permissions.
G1 pinned snapshot and SHA receipts.
G2 schema-valid raw extraction and zero-loss comparison.
G3 dedup suggestions reviewed; original records preserved.
G4 tests actually run with logs and independent verification.
G5 UI displays only traceable status and source.
G6 reviewer approves release; main stays untouched.
No financial spend; publish only after approval. Do not modify project.genome or Ω.000.

## First implementation priority
Reuse tools/build_innovation_operation_index.py and existing registry schemas. Add a read-only adapter to consume their output; do not create another index authority or a duplicate VX runtime. Measure build time, source coverage, candidate duplicates, and successful deterministic replays.
