# VAIXLNS — Repository Merge Policy v1

Purpose: accelerate federation work while preventing semantic loss, lineage loss, accidental overwrites, and unverified runtime claims.

## Non-negotiable rule

A repository is never merged because its name sounds related. A merge is admitted only when its identity, capability, contracts, dependencies, tests, lineage, and unique evidence are mapped to a canonical owner.

## Preservation-before-integration

1. Record source repository, default branch, head SHA and repository role.
2. Record every moved path and its source SHA.
3. Record SOURCE → EVIDENCE → IDENTITY → RELATION → STATUS → CANONICAL OWNER.
4. Preserve the source repository as historical or specialized evidence until the integration is verified.
5. Never convert PROPOSAL, SPECIFIED, or RECOVERED to IMPLEMENTED or VERIFIED by relocation alone.

## Merge admission gates

| Gate | Required evidence |
|---|---|
| Identity | Canonical repository role and subsystem owner |
| Coverage | All source paths accounted for |
| Lineage | Legacy/source SHA and predecessor/successor mapping |
| Uniqueness | No unique capability or engineering point lost |
| Dependency | Imports, packages, runtime assumptions and external interfaces mapped |
| Contract | Inputs, outputs, invariants, authority and failure modes retained |
| Tests | Existing tests retained or replaced with equivalent coverage |
| Runtime | Runnable claims supported by reproducible execution evidence |
| Security | Secrets, permissions and trust boundaries reviewed |
| Rollback | Source tag, branch or SHA retained until post-merge verification |
| Provenance | Evidence links and source references recorded |

## Merge classes

- SELECTIVE-CODE-MERGE: only proven implementation paths move.
- DOC-MERGE: canonical documents are copied or synchronized; source remains.
- DEPENDENCY: external repository is referenced as an upstream dependency, never copied blindly.
- SPECIALIZED-KEEP: repository remains independent because it owns a bounded subsystem.
- QUARANTINE: repository is preserved without promotion until evidence improves.
- HISTORICAL-VARIANT: lineage is retained; no canonical promotion without reconciliation.

## World's GitHub ecosystem

Public repositories may be discovered and evaluated as:

EXTERNAL-REFERENCE → DEPENDENCY → ADAPTER → SELECTIVE-IMPORT

No external repository becomes part of the canonical VAIXLNS trust boundary merely because it is popular or compatible by description. License, maintenance, API compatibility, security, tests, and architectural fit are required before adoption.

## Fast-path rule

Parallelize discovery and evidence collection, not canonical mutation.

Safe parallel lanes: repository inventory, source-path enumeration, dependency analysis, test and CI inspection, terminology extraction, lineage mapping, and external candidate research.

Canonical writes happen through one controlled admission path.

## Protected surfaces

The following are loss-sensitive and must not be silently deleted or overwritten:

archive/
docs/recovery/
docs/indexes/
registry/
schemas/

A removal requires explicit lineage and replacement evidence.
