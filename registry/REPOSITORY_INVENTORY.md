# VAIXLNS GitHub Repository Inventory

**Snapshot:** 2026-10-03  
This inventory preserves repository identity and lineage while assigning an architectural role from observed repository evidence.

## Four-system surfaces

| System | Repository | Role | Disposition |
|---|---|---|---|
| VAIXLNS | VAIXLNS | Canonical architecture, registry, schemas, recovery | CANONICAL |
| VLNS | NAXLNS | Knowledge / discovery / adversarial analysis candidate | IDENTITY UNVERIFIED |
| VX | VX-runtime | Governed execution boundary specification | CANONICAL RUNTIME SPEC |
| VX | VX50_COMPLETE_BUILD | Historical/build surface | HISTORICAL BUILD SURFACE |
| NEXNET | NEXENT | Discovery / architecture search / research | IMPLEMENTED DISCOVERY BASELINE; IDENTITY UNVERIFIED |

## Supporting VAIXLNS surfaces

| Repository | Role | Disposition |
|---|---|---|
| VAIXLNS-unified | Integrated executable fabric | INTEGRATION / PARTIAL EVIDENCE |
| vaixlns-core | Focused core / vertical slice | IMPLEMENTATION |
| vaixlns-csd-kernel | Cryptographic/replay kernel surface | IMPLEMENTATION / DSL |
| VAIXLNS-Intent-to-Reality | Intent/state/transformation specification | PRIVATE REFERENCE |
| VAIXLNS-Naming-Constitution-v1.0 | Naming / identity governance | CONSTITUTIONAL REFERENCE |
| VAIXLNS_OPERATIONAL_ASSURANCE.md | Operational assurance artifact | ASSURANCE REFERENCE |
| VAIXLNS- | Historical/auxiliary VAIXLNS repository | LINEAGE |
| VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml | Execution contract artifact | CONTRACT REFERENCE |
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
- NATIONAL-
- joke-generator

## Canonicalization policy

1. Preserve every repository and its history.
2. Do not rename or delete solely to reduce duplication.
3. Assign each repository a stable role record.
4. Move reusable implementation behind VX adapters/contracts.
5. Keep external projects as dependencies unless their code is intentionally absorbed and license/security checks pass.
6. A repository becomes canonical only when its responsibility, lineage, tests and evidence are established.
7. The canonical execution target is the VX runtime surface; other execution implementations integrate through explicit contracts/adapters.
8. Unverified system/repository identity mappings must remain non-destructive and visibly unresolved.

## Cloud / agent migration rule

A Claude/cloud project is treated as an external implementation source, not as the canonical runtime.

\`\`\`text
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
\`\`\`

No blind copy-and-rename operation is permitted.


## VX specialist-agent coordination proposal — 2026-10-09

| Repository | Role | Disposition |
|---|---|---|
| vx-agents-fabric | Versioned VX research, financial-analysis and engineering specialist orchestration; Ω Parent Multi-Mind review adapters | PROPOSED INTEGRATION — PR OPEN; NOT CANONICALLY ADMITTED |

The repository is maintained as a distinct implementation surface. It must enter through the universal integration gate, preserve its own versions and lineage, and may not mutate canonical VAIXLNS state. A green unit-test workflow is implementation evidence only; it is not proof of production readiness or runtime connectivity.
