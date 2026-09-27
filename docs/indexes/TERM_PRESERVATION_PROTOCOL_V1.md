# VAIXLNS — Term / Innovation Preservation Protocol v1

## Objective

Ensure that no historical term, abbreviation, innovation, engineering rule, architectural point, experiment, repository artifact, or design decision disappears during recovery, canonicalization, or repository consolidation.

## Atomic preservation record

Every recovered item is represented by an atomic record with at least:

legacy_id → canonical_id → name → aliases → type → family → origin → status → meaning → lineage → dependencies → capabilities → contracts → authority → events → evidence → proof → implementation → repository → files → lifecycle

The canonical JSON schema is schemas/atomic-system-record.schema.json.

## Status discipline

Evidence-supported implementation transitions are explicit:

RECOVERED → CANONICAL → IMPLEMENTED → VERIFIED

Historical and research states remain explicit:

VARIANT | PROPOSED | SUPERSEDED

Relocation, renaming, copying, or documentation does not itself change status.

## Loss-prevention invariant

For every consolidation operation:

source_items = mapped_items + explicitly_excluded_items

Every explicit exclusion carries a reason and retains provenance.

## Terminology rule

Never collapse two names solely because they appear similar.

Possible relationships are:

ALIAS | VARIANT | SUBSYSTEM | DERIVED_CAPABILITY | SUPERSEDES | DUPLICATE | CONFLICT

The relationship must be evidenced before canonical collapse.

## Engineering-point preservation

A design point is not preserved unless its operational intent survives, including where relevant:

contract, preconditions and postconditions, invariants, authority boundary, state transition, events, failure modes, recovery behavior, observability, test and proof obligations, lineage and evolution rule.

## Source-of-truth hierarchy

ARCHIVE SOURCE → RECOVERY RECORD → CANONICAL REGISTRY → IMPLEMENTATION → RUNTIME EVIDENCE

No lower layer silently rewrites the meaning of a higher layer.

## Acceleration mechanism

Create immutable evidence packets per source repository or file. Each packet can then be admitted to the canonical graph without re-reading the same source repeatedly.

Recommended packet fields:

source_sha, path, extracted_terms, extracted_entities, capabilities, dependencies, tests, status, proposed_owner, evidence_links, conflicts

## Coverage boundary

Current project materials establish a historical Master Index of approximately 2750 entries across 40+ families, but the complete 0001–2750 item-by-item source is not independently exposed in the current evidence surface. Therefore the system must not claim 100% item-level recovery until that original source is available.
