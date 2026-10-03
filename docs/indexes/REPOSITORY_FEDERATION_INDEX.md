# GitHub Repository Federation Index

**Snapshot:** 2026-10-03  
**Accessible owned repositories observed:** 43

## Four-System Architecture Federation

The federation is governed as four independent system identities. Repository identity is not automatically equated with system identity.

| System | System Role | Current Repository Evidence | Federation State |
|---|---|---|---|
| **VAIXLNS** | Sovereign canonical authority / governance / registry / recovery | \`VAIXLNS\` | CANONICAL |
| **VLNS** | Independent system identity | \`NAXLNS\` exists; identity equivalence is not established by repository name alone | SPECIFIED / UNVERIFIED |
| **VX** | Governed execution / runtime system | \`VX-runtime\`, \`VX50_COMPLETE_BUILD\` | CANONICAL SYSTEM / MULTI-REPOSITORY SURFACE |
| **NEXNET** | Independent network / discovery system identity | \`NEXENT\` exists as a distinct discovery/research repository; identity equivalence is not established by repository name alone | SPECIFIED / UNVERIFIED |

**Integration rule:** these four systems are federated under VAIXLNS; they are not collapsed into one repository. Each system retains its own identity, contracts, evidence, lifecycle, and verification boundary.

**Unresolved identity conflicts:** \`VLNS ↔ NAXLNS\` and \`NEXNET ↔ NEXENT\` require explicit identity evidence before repository reassignment, renaming, or destructive merge. No destructive merge is performed on the basis of name similarity.

See [Four-System Reconciliation v1](FOUR_SYSTEM_RECONCILIATION_V1.md) for the current machine-actionable interpretation.

## Canonical VAIXLNS federation

| Repository | Role | Status |
|---|---|---|
| \`VAIXLNS\` | Canonical architecture / registry / recovery / docs | CANONICAL |
| \`NAXLNS\` | Knowledge / adversarial analysis / discovery candidate for VLNS | IDENTITY UNVERIFIED |
| \`NEXENT\` | Discovery / architecture search / innovation research | IMPLEMENTED DISCOVERY BASELINE |
| \`VAIXLNS-unified\` | Executable sovereign runtime surface | RUNTIME / PARTIAL EVIDENCE |
| \`vaixlns-core\` | Focused core / vertical slice | CORE |
| \`vaixlns-csd-kernel\` | Specialized signed/replay kernel | SPECIALIZED-KERNEL |
| \`VAIXLNS-Intent-to-Reality\` | Intent → reality pipeline | INTENT |
| \`VAIXLNS-Naming-Constitution-v1.0\` | Naming / identity governance | CONSTITUTIONAL-SUPPORT |
| \`VAIXLNS_OPERATIONAL_ASSURANCE.md\` | Operational assurance artifact | ASSURANCE |
| \`VAIXLNS-\` | Historical variant | HISTORICAL-VARIANT |
| \`VX50_COMPLETE_BUILD\` | Build / developer VX surface | BUILD-SURFACE |
| \`VX-runtime\` | Runtime specialization | RUNTIME-SPECIALIZATION |
| \`VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml\` | Execution contract artifact | CONTRACT |
| \`tools-vaixlns-meta-core-v0.3.ts\` | Meta-core tooling artifact | TOOLING |

## Adjacent / unclassified repositories

The remaining owned repositories are inventoried here and are intentionally not merged automatically.

\`-\`, \`--\`, \`copilot-sdk\`, \`datasets\`, \`desktop\`, \`fictional-octo-spoon\`, \`fisallll280-gmail.com\`, \`fluffy-chainsaw\`, \`friendly-engine\`, \`fuzzy-octo-winner\`, \`glowing-doodle\`, \`joke-generator\`, \`legendary-octo-fiesta\`, \`New-Action\`, \`NATIONAL-\`, \`pylance-release\`, \`Pumpkin\`, \`redesigned-invention\`, \`reimagined-garbanzo\`, \`Repository-name\`, \`src-main.rs\`, \`starter-workflows\`, \`stunning-chainsaw\`, \`TRMDL-PRECISION-MAX-TRMDL-NO-LATENCY-TRMDL-NO-PROMPTS-TRMDL-AUTO-EXECUTE\`, \`tunnel-client\`, \`verbose-engine\`, \`whisper\`, \`y\`.

**Rule:** unclassified repositories remain untouched until their contents establish a defensible VAIXLNS relationship.

## Perpetual factory lane

The following are **target repositories declared by the governed factory manifest**, not yet counted as existing repositories:

| Target repository | Role | Creation policy |
|---|---|---|
| \`VAIXLNS-repository-orchestrator\` | FACTORY | auto-create when authorized |
| \`VAIXLNS-performance-fabric\` | RUNTIME-SUPPORT | auto-create when authorized |
| \`VAIXLNS-development-fabric\` | BUILD | auto-create when authorized |
| \`VAIXLNS-innovation-factory\` | FACTORY | auto-create when authorized |
| \`VAIXLNS-integration-lab\` | LAB | auto-create when authorized |

The factory executes only from \`registry/repository-orchestration/REPOSITORY_FACTORY_MANIFEST_V1.json\`. Existing unrelated repositories remain untouched.

## Operational server binding

- [Four-system operational federation](../../deploy/federation/README.md)
- [Federation deployment manifest](../../deploy/federation/federation.yaml)

These artifacts bind system identities to repository surfaces and define the required server infrastructure. They do not claim that the server has been deployed or that identity mappings marked UNVERIFIED have been proven.
