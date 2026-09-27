# VAIXLNS Repository Federation v2

Snapshot: 2026-09-27

## Purpose

This document is the human-readable control surface for the GitHub federation.

`VAIXLNS` is the canonical architecture/registry/governance surface.
`NEXENT` is the independent discovery, architecture-search, synthesis, simulation and research engine.
Runtime repositories implement projections; they do not redefine canonical authority.

## Repository flow

```text
REPOSITORY OBSERVATION
        ↓
IDENTITY / ROLE
        ↓
EVIDENCE + LINEAGE
        ↓
CANONICAL GRAPH
        ↓
CONTRACT CHECK
        ↓
BUILD / TEST / VERIFY
        ↓
PROOF / REVIEW
        ↓
CONTROLLED ADOPTION
```

## Federated project repositories

| Repository | Role | Evidence state | Boundary |
|---|---|---|---|
| `VAIXLNS` | CANONICAL | ACTIVE CANON SURFACE | Canonical architecture, registry, governance |
| `NEXENT` | DISCOVERY | IMPLEMENTED BASELINE + RESEARCH | Discover → design → simulate → prove → propose |
| `VAIXLNS-unified` | RUNTIME | PARTIAL IMPLEMENTATION | Executable projection |
| `vaixlns-core` | CORE | VERTICAL-SLICE REFERENCE | Constitutional/core reference |
| `vaixlns-csd-kernel` | SPECIALIZED-KERNEL | SPECIFIED | CSD / signed / replay kernel |
| `VAIXLNS-Intent-to-Reality` | INTENT | INCOMPLETE / RECOVERY REQUIRED | Intent boundary |
| `VX-runtime` | RUNTIME-SPECIALIZATION | SPECIFIED | VX runtime specialization |
| `VX50_COMPLETE_BUILD` | BUILD-SURFACE | INCOMPLETE | Build/recovery surface |
| `VAIXLNS-Naming-Constitution-v1.0` | CONSTITUTIONAL-SUPPORT | SPECIFIED | Naming and identity governance |
| `VAIXLNS_OPERATIONAL_ASSURANCE.md` | ASSURANCE | SPECIFIED | Operational assurance |
| `VAIXLNS-` | HISTORICAL-VARIANT | QUARANTINED | Provenance only until reconciled |
| `VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml` | CONTRACT | SPECIFIED ARTIFACT | Execution contract |
| `tools-vaixlns-meta-core-v0.3.ts` | TOOLING | TOOLING ARTIFACT | Meta-core tooling |

## The remaining owned repositories

There are 40 owned repositories visible to the connected GitHub account at this snapshot. The remaining 27 are explicitly **UNCLASSIFIED** and are not modified by the federation process until their contents establish a defensible relationship to VAIXLNS.

## AI Agent Provider Fabric

External models—including the user-supplied `claude-fable-5.md` reference—sit behind a provider adapter. A model may inspect, reason, generate code, run review-oriented tasks, or propose changes, but it does not become a constitutional authority.

```text
NEXENT
  ↓
AGENT TASK
  ↓
PROVIDER ADAPTER
  ├── Anthropic Fable
  ├── Other remote models
  └── Local models
  ↓
ARTIFACT / EVIDENCE
  ↓
TEST / VERIFY / PROVE
  ↓
VAIXLNS GOVERNANCE
```

Provider-neutrality is mandatory: provider/model replacement must not require rewriting canonical contracts.

## Safety of the federation

- No history deletion as a “cleanup” shortcut.
- No document-only promotion to VERIFIED/IMPLEMENTED.
- No silent mutation across repository boundaries.
- Historical variants retain lineage.
- Runtime code cannot redefine canonical meaning merely by existing in a runtime repository.
- External AI remains an execution/research capability, not authority.

See `registry/repository-federation/REPOSITORY_FEDERATION_V2.json` for the machine-readable source.
