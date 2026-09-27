# VAIXLNS GitHub Repository Inventory

This inventory preserves every accessible repository name and assigns an architectural role without deleting or renaming lineage.

## Canonical VAIXLNS/VX domain

| Repository | Role | Disposition |
|---|---|---|
| VAIXLNS | Canonical architecture, registry, schemas | CANONICAL |
| VX-runtime | Deterministic execution boundary | CANONICAL RUNTIME |
| VAIXLNS-unified | Integrated fabric | INTEGRATION |
| vaixlns-core | Core vertical slice | IMPLEMENTATION |
| vaixlns-csd-kernel | Cryptographic/replay kernel | IMPLEMENTATION |
| NEXENT | Discovery, architecture search, evolution | DOMAIN CANONICAL |
| VAIXLNS-Intent-to-Reality | Intent/state/transformation specification | PRIVATE REFERENCE |
| VX50_COMPLETE_BUILD | Historical/buildable VX pack | HISTORICAL REFERENCE |
| VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml | Execution contract artifact | CONTRACT REFERENCE |
| VAIXLNS_OPERATIONAL_ASSURANCE.md | Operational assurance artifact | ASSURANCE REFERENCE |
| VAIXLNS-Naming-Constitution-v1.0 | Naming rules | CONSTITUTIONAL REFERENCE |
| VAIXLNS- | Historical/auxiliary VAIXLNS repository | LINEAGE |
| tools-vaixlns-meta-core-v0.3.ts | Meta tooling | TOOLING |
| tunnel-client | Connectivity/transport utility | ADAPTER CANDIDATE |

## External/open-source foundations or dependencies

These are not to be merged blindly into VAIXLNS. They should enter through dependency/adaptor records and licensing/security review.

- copilot-sdk
- whisper
- datasets
- desktop
- react-native-website
- starter-workflows
- pylance-release
- Pumpkin
- src-main.rs

## Unclassified / legacy repositories

These remain preserved until repository-content inspection assigns a role:

- y
- --
- Repository-name
- TRMDL-PRECISION-MAX-TRMDL-NO-LATENCY-TRMDL-NO-PROMPTS-TRMDL-AUTO-EXECUTE
- glowing-doodle
- fictional-octo-spoon
- stunning-chainsaw
- legendary-octo-fiesta
- fluffy-chainsaw
- fuzzy-octo-winner
- -
- redesigned-invention
- New-Action
- friendly-engine
- reimagined-garbanzo
- fisallll280-gmail.com

## Canonicalization policy

1. Preserve every repository and its history.
2. Do not rename or delete solely to reduce duplication.
3. Assign each repository a stable role record.
4. Move reusable implementation behind VX adapters/contracts.
5. Keep external projects as dependencies unless their code is intentionally absorbed and license/security checks pass.
6. A repository becomes canonical only when its responsibility, lineage, tests and evidence are established.
7. The canonical execution target is VX-runtime; other runtimes integrate through contracts/adapters.

## Cloud / agent migration rule

A Claude/cloud project is treated as an external implementation source, not as the canonical runtime.

CLOUD/AGENT
-> SOURCE SNAPSHOT
-> LINEAGE RECORD
-> CAPABILITY EXTRACTION
-> VX CONTRACT
-> ADAPTER
-> SIMULATION
-> VERIFICATION
-> EVIDENCE
-> VX EXECUTION
-> OPERATIONS

No blind copy-and-rename operation is permitted.
