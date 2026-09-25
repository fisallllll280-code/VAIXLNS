# VAIXLNS — Repository Map

> Canonical map for the VAIXLNS GitHub estate. This document organizes repositories by role without deleting or moving existing source.

## 1. Canonical root
- **VAIXLNS** — primary public root, documentation, schemas, templates, and tools.
- Default branch: `main`.

## 2. Unified integration
- **VAIXLNS-unified** — unified implementation/integration workspace.
- Contains: `core/`, `execution/`, `docs/`, `tests/`, and Python dependencies.
- Default branch: `main`.

## 3. Core / kernel
- **vaixlns-core** — core implementation repository.
- **vaixlns-csd-kernel** — CSD/kernel layer; contains `VAIXLNS_ROOT.lns`.
- **VX-runtime** — VX runtime layer.

## 4. Build / execution
- **VX50_COMPLETE_BUILD** — private build workspace.
- **VAIXLNS-Intent-to-Reality** — private intent-to-execution workspace.

## 5. Governance / naming
- **VAIXLNS-Naming-Constitution-v1.0** — naming/governance reference.

## 6. Execution contract / assurance
- **VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml** — execution/build contract.
- **VAIXLNS_OPERATIONAL_ASSURANCE.md** — operational assurance reference.

## Repository discipline
1. `VAIXLNS` is the public documentation and canonical-index root.
2. Runtime code belongs in implementation/runtime repositories, not in the root documentation repository.
3. Governance and naming artifacts remain separate from executable code.
4. Private build/work-in-progress repositories must not be treated as public canonical releases.
5. Every new repository should have a README stating its role, inputs, outputs, dependencies, branch, and relationship to the canonical root.
6. Avoid duplicating the same canonical specification across repositories; link to the authoritative copy instead.

## Current relationship

```text
VAIXLNS (canonical root)
├── Governance / naming
│   └── VAIXLNS-Naming-Constitution-v1.0
├── Core
│   ├── vaixlns-core
│   └── vaixlns-csd-kernel
├── Runtime
│   └── VX-runtime
├── Unified integration
│   └── VAIXLNS-unified
├── Build / execution
│   ├── VX50_COMPLETE_BUILD
│   └── VAIXLNS-Intent-to-Reality
└── Contracts / assurance
    ├── VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml
    └── VAIXLNS_OPERATIONAL_ASSURANCE.md
```
