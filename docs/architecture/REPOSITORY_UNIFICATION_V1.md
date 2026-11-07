# VAIXLNS Repository Unification v1

## Canonical roles

VAIXLNS remains the canonical architecture, registry, governance, and lineage root.
VAIXLNS-unified remains the executable integration surface.
NEXENT remains the discovery/search/architecture-synthesis system.
VX-related repositories remain execution/runtime/build inputs until their contents are validated and promoted.

## Target topology

```text
VAIXLNS
  ├── canonical architecture
  ├── master system registry
  ├── version/lineage registry
  ├── governance + architecture decisions
  └── pointers to executable integrations

VAIXLNS-unified
  └── integrated runtime

NEXENT
  └── discovery / search / synthesis

VX execution repositories
  └── runtime/build components

VAIXLNS-ARCHIVE
  └── immutable historical snapshots and source-preserving records

VAIXLNS-RECOVERY
  └── recoverable retired/deleted material, quarantine records, and restoration manifests
```

## Zero-loss rule

No historical project, file, identifier, version, alias, branch-derived artifact, or design record is destroyed during consolidation.
A consolidation operation may copy content into a canonical location, mark an item as merged/superseded/retired/quarantined, add lineage and provenance, or replace a canonical pointer. It must not erase the historical record.

## Promotion states

DISCOVERED -> RECOVERED -> CLASSIFIED -> CANONICAL -> INTEGRATED -> CONFORMANT -> VERIFIED
QUARANTINED and RETIRED remain recoverable states.

## Merge rule

Projects are unified by function and lineage, not by filename similarity.
A research repository is not promoted to runtime merely because its README describes a runtime. Duplicate names are linked through lineage before canonicalization.

## Version rule

Historical versions keep their original version identifiers.
Canonical releases receive a canonical release identifier and point back to every source version used to form them.

## Recovery rule

Deletion from an active surface means a state transition, not destruction:
ACTIVE -> RETIRED -> ARCHIVED -> RECOVERABLE
A restoration creates a new event and never rewrites historical provenance.

## Anti-regression rule

No repository is marked VERIFIED from README claims alone. Runnable claims require execution, tests, and reproducible evidence.
