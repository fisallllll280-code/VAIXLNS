# VAIXLNS — Master Operational Control Plane v1

## Purpose

This document is the canonical wiring contract between everything previously designed in VAIXLNS/NEXENT and the executable operating sources in GitHub.

## Source hierarchy

ARCHIVE → RECOVERY → REGISTRY → CANONICAL ARCHITECTURE → EXECUTION PLAN → SIMULATION → RUNTIME → VERIFICATION → PROOF → OPERATION → RECOVERY → EVOLUTION

No document becomes an implementation merely by being indexed.

## Canonical operating sources

| Source | Role |
|---|---|
| VAIXLNS | Canonical architecture, registry, lineage, governance |
| VAIXLNS-unified | Integrated executable runtime surface |
| NEXENT | Discovery, search, synthesis, candidate generation |
| vaixlns-core | Selective implementation source after reconciliation |
| VX-runtime | Runtime contracts/specification source |
| VAIXLNS-Intent-to-Reality | Intent-to-execution pipeline source |
| vaixlns-csd-kernel | Specialized kernel source |
| VX50_COMPLETE_BUILD | Quarantined/recovery build source until executable evidence exists |

## Operational planes

### 1. Recovery plane
Collect historical files, specifications, diagrams, terminology, innovations and repository evidence. Preserve source SHA/path and provenance.

### 2. Knowledge plane
Convert recovered material into Atomic System Records, innovation records, terminology records, lineage and dependency graphs.

### 3. Architecture plane
Resolve canonical identities, subsystem ownership, interfaces, contracts, invariants and authority boundaries.

### 4. Planning plane
Turn canonical operations into executable plans and dependency DAGs.

### 5. Simulation plane
Execute deterministic scenarios against models/fixtures before promoting to integrated runtime.

### 6. Runtime plane
Boot, execute, observe and record real executable targets.

### 7. Verification plane
Run unit, integration, contract, invariant, replay and recovery checks.

### 8. Evidence plane
Persist run IDs, code SHA, inputs, configuration, dependencies, logs, artifacts, verification and proof status.

### 9. Recovery plane
Snapshot → classify → rollback/repair → replay → verify.

### 10. Evolution plane
Use verified operational evidence to propose new architecture; proposals return through simulation and verification before canonical promotion.

## Required operation lifecycle

DEFINE → INDEX → PLAN → GENERATE → BOOT → EXECUTE → RECORD → SIMULATE → VERIFY → PROVE → COMMIT → OPERATE → MONITOR → RECOVER → REPLAY → REGRESSION → EVOLVE

## Status discipline

RECOVERED → CANONICAL → IMPLEMENTED → VERIFIED

Side states:
PROPOSED | VARIANT | SUPERSEDED | QUARANTINED | BLOCKED

A status transition requires evidence appropriate to the target state.

## Lossless invariant

For every consolidation:

source_items = mapped_items + explicitly_excluded_items

Every excluded item retains provenance and a reason. Protected archives, recovery records, registries and schemas are never silently deleted.

## Execution authority

GitHub is the controlled change/evidence surface. Runtime truth requires executable evidence. Pull requests are the canonical mutation boundary for repository consolidation.

## Completion condition

The system is operationally complete only when every intended operation has:
- an owner;
- an operation record;
- an executable target or an explicit non-executable status;
- dependencies;
- simulation/test coverage appropriate to its state;
- run/evidence records;
- recovery behavior;
- lineage to source material.
