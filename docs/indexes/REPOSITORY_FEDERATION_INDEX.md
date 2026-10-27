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


## VX specialist-agent fabric binding — proposal (2026-10-09)

| Implementation repository | System boundary | Current evidence state | Canonical treatment |
|---|---|---|---|
| vx-agents-fabric | VX adapter-based coordination for research, financial analysis, engineering and parent multi-mind reviews | IMPLEMENTED ON FEATURE BRANCH; UNIT TESTS GREEN; LIVE PROVIDERS AND DURABLE LEDGER NOT CONNECTED | PROPOSED / NOT ADMITTED |

### Binding rules

1. Agent identities and versions remain immutable; a role may have multiple explicit versions.
2. Agents route through VX contracts and scoped adapters. Do not wire all agents directly to all systems.
3. Research outputs preserve source/evidence provenance; financial agents analyse and propose only, with no payment/trading authority.
4. The Ω Parent council records an independent review only when that mind's provider adapter actually runs.
5. Missing providers, proof gaps or hard-gate failures force HOLD/REJECT; votes cannot override them.
6. The fabric cannot adopt canonical state or deploy production changes. VAIXLNS governance and the universal external integration gate remain authoritative.
7. The implementation remains PROPOSED until sandbox, failure/recovery, replay, independent verification, fresh proof and explicit admission evidence are attached.

Reference implementation review: https://github.com/fisallllll280-code/vx-agents-fabric/pull/1

## Agent Skills, Prompt, Subscription & Innovation Delivery Fabric — 2026-10-09

- [Agent/Skill/Prompt/Environment/Innovation Fabric V1](../integration/VAIXLNS_AGENT_SKILL_SUBSCRIPTION_FABRIC_V1.md)

This specification defines logical agent roles, versioned skill/prompt contracts, environment/subscription status, innovation lineage, build-source provenance, and gated delivery. It is a proposal pending review and admission; it does not assert that agents are deployed, subscriptions purchased, external accounts connected, or production systems changed. Provider/environment integration requires direct evidence, explicit authorization and the existing VX admission gates.

## Gr8r → VX intake bridge — 2026-10-27

- Implementation: [local intake and authorization bridge](../../tools/gr8r_adapter/README.md).
- Registry: [GR8R-VX-INTAKE](../../registry/gr8r-vx-intake.integration.v1.json).
- Evidence: [local acceptance receipt](../evidence/gr8r-vx-intake-20261027.json).
- State: IMPLEMENTED, LOCAL_CONTRACT_ONLY; production gate HOLD.
- Specialized role VX-GR8R-INTAKE maps to VCRE INTEGRATION_ENGINEER with proposal-review capability only. No deployed agent instance is asserted.
- Source ZIP lineage, execution authority, tests and runtime connection remain distinct.

## Repository-agent scenario and automation lane — 2026-10-27

- [MiroFish ideas + Zapier under VX](../integration/VX_MIROFISH_ZAPIER_INTEGRATION_V1.md).
- [Machine-readable integration](../../registry/vx-mirofish-zapier.integration.v1.json).
- Existing vx-agents-fabric extension, not a new sovereign system or ChatGPT plugin.
- IMPLEMENTED_ON_FEATURE_BRANCH: offline planners; roles DESIGN_ONLY, live connections NOT_CONFIGURED, production HOLD.

## VX municipal sandbox readiness runner — 2026-10-27

- Implementation: [VX-runtime #29](https://github.com/fisallllll280-code/VX-runtime/pull/29),
  merged as `7fc4fcebb7fccdb70e379df7a52fa7826b4bb2c9`.
- [Machine-readable integration and exact source/evidence links](../../registry/vx-municipal-runtime.integration.v1.json).
- Existing VXRuntime extended by a fixed local role, presence-only input checks,
  scoped host grants and durable, time-bounded SQLite receipts.
- IMPLEMENTED_LOCAL_REFERENCE; 71 local and GitHub CI tests PASS on the feature
  source `c959d11957d981415bc02e2a712c88237694e3d9`. Synthetic local CLI E2E PASS.
- No government transport, official eligibility decision, application submission,
  authenticated production host or complete PDPL certification. Canonical admission
  NOT_GRANTED; government E2E and T01–T15 NOT_RUN; production HOLD, spend 0 SAR.
