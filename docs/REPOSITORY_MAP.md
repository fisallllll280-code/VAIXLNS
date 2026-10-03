# VAIXLNS — Repository Map

> Canonical map for the VAIXLNS GitHub estate. This document organizes repositories by role without deleting or moving existing source.

## 1. Four-system federation

```text
VAIXLNS
├── VLNS
│   └── NAXLNS (identity UNVERIFIED)
├── VX
│   ├── VX-runtime
│   └── VX50_COMPLETE_BUILD
└── NEXNET
    └── NEXENT (identity UNVERIFIED)
```

VAIXLNS is the canonical federation/control-plane root. The four system identities are retained independently; repository names do not establish identity by themselves.

## 2. Canonical root

- VAIXLNS — primary public root, documentation, schemas, templates, registries, recovery, and tools.
- Default branch: main.

## 3. Knowledge / discovery

- NAXLNS — candidate repository surface for VLNS; identity mapping remains unverified.
- NEXENT — discovery / architecture search / research implementation surface; identity mapping to NEXNET remains unverified.

## 4. Unified integration

- VAIXLNS-unified — unified implementation/integration workspace.
- Contains: core/, execution/, docs/, tests/, and Python dependencies.
- Default branch: main.

## 5. Core / kernel

- vaixlns-core — core implementation repository.
- vaixlns-csd-kernel — CSD/kernel layer.
- VX-runtime — VX runtime contract/specification surface.

## 6. Build / execution

- VX50_COMPLETE_BUILD — build/history surface for VX.
- VAIXLNS-Intent-to-Reality — intent-to-execution workspace.

## 7. Governance / naming

- VAIXLNS-Naming-Constitution-v1.0 — naming/governance reference.

## 8. Execution contract / assurance

- VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml — execution/build contract artifact.
- VAIXLNS_OPERATIONAL_ASSURANCE.md — operational assurance reference.

## Repository discipline
1. VAIXLNS is the public documentation and canonical-index root.
2. Runtime code belongs in implementation/runtime repositories, not in the root documentation repository.
3. Governance and naming artifacts remain separate from executable code.
4. Private build/work-in-progress repositories must not be treated as public canonical releases.
5. Every new repository should have a README stating its role, inputs, outputs, dependencies, branch, and relationship to the canonical root.
6. Avoid duplicating the same canonical specification across repositories; link to the authoritative copy instead.
7. Preserve unresolved identity mappings as explicit evidence gaps.
8. Preserve historical repositories and their history; organize through roles and lineage rather than destructive renames.

## Current relationship

```text
VAIXLNS (canonical root)
├── FOUR-SYSTEM FEDERATION
│   ├── VLNS → NAXLNS [UNVERIFIED]
│   ├── VX → VX-runtime + VX50_COMPLETE_BUILD
│   └── NEXNET → NEXENT [UNVERIFIED]
├── Governance / naming
│   └── VAIXLNS-Naming-Constitution-v1.0
├── Core
│   ├── vaixlns-core
│   └── vaixlns-csd-kernel
├── Runtime / integration
│   ├── VAIXLNS-unified
│   └── VX-runtime
├── Build / execution
│   ├── VX50_COMPLETE_BUILD
│   └── VAIXLNS-Intent-to-Reality
└── Contracts / assurance
    ├── VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml
    └── VAIXLNS_OPERATIONAL_ASSURANCE.md
```