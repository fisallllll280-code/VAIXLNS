# VAIXLNS Repository Contract

## Identity

- System ID: VAIXLNS
- Repository: fisallllll280-code/VAIXLNS
- Role: CANONICAL CONTROL PLANE / REGISTRY / GOVERNANCE / RECOVERY
- Family: Sovereign System Registry
- State: ACTIVE

## Authority

VAIXLNS is the canonical architecture, registry, provenance, governance, and recovery authority for the federation. This contract does not grant authority to generated artifacts or runtime components.

## Required evidence

Documentation is not implementation proof. A VERIFIED claim requires a reproducible source revision, dependency resolution, executable entrypoint where applicable, tests, health/runtime evidence where applicable, and captured provenance.

## Lifecycle

```text
SPECIFIED → IMPLEMENTED → TESTED → VERIFIED → EVOLVING
                         ↘ FAILED / QUARANTINED
```

## Canonical boundaries

- Golden Source: project.genome::v1.0.0
- Authority Anchor: Ω0_GENESIS_CORE
- Master Registry: Ω.000
- Tool boundary: ARC-X Ω
- Runtime admission boundary: Index Recovery + Runtime Admission Engine
- Repository federation boundary: Repository Perpetual Engine

## Contract

Every governed repository record must declare:

- System ID
- Repository identity
- Family and role
- Lifecycle state
- Authority boundary
- Input/output boundary
- Entrypoint and build command when executable
- Test/verification command when executable
- Runtime dependencies
- External interfaces
- Security boundary
- Canonical lineage
- Evidence location
- Performance/operational metrics when applicable
- Innovation relationship

## Evidence states

Use the project evidence vocabulary without treating it as a quality ranking:

```text
VERIFIED
SPECIFIED
PARTIAL
MISSING
CONFLICT
PROPOSAL
```

## Anti-duplication

Before introducing a new top-level system, reconcile against the VAIXLNS federation, recovery, and innovation indexes. Overlapping capabilities become derived capability records unless a distinct system boundary is justified by explicit contract, identity, lineage, and evidence.

## Non-loss rule

Historical names, specifications, variants, and repositories are preserved through lineage. No historical artifact is silently deleted or reclassified as canonical without evidence.

## Admission rule

A repository may be admitted to runtime only through deterministic retrieval, reconciliation, dependency resolution, startup/health checks, testing, and evidence capture. Successful startup is not semantic proof.

## Change control

Canonical changes must remain reviewable through Git history and reproducible from pinned source revisions. Generated artifacts remain candidates until verified and admitted through the governed authority path.
