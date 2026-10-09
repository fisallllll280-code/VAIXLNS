# VAIXLNS — Canonical Project Hub

This repository is the canonical architecture, registry, recovery, provenance, and documentation root for the VAIXLNS federated project.

## Navigation

- [Master index navigation](docs/indexes/README.md)
- [Master recovery status](docs/indexes/MASTER_RECOVERY_STATUS.md)
- [Archive source index](docs/indexes/ARCHIVE_SOURCE_INDEX.md)
- [Innovation master index](docs/indexes/INNOVATION_MASTER_INDEX.md)
- [Repository federation index](docs/indexes/REPOSITORY_FEDERATION_INDEX.md)
- [Four-system reconciliation](docs/indexes/FOUR_SYSTEM_RECONCILIATION_V1.md)
- [Repository system map](docs/canonical/REPOSITORY_SYSTEM_MAP_V1.md)
- [Repository runtime status](docs/indexes/REPOSITORY_RUNTIME_STATUS_V1.md)
- [Innovation separation matrix](docs/innovation/INNOVATION_SEPARATION_MATRIX_V1.md)
- [Innovation federation JSON](docs/innovation/innovation-federation.json)
- [Engineering decision register](docs/indexes/ENGINEERING_DECISION_REGISTER.md)
- [Conformance gap closure v1](docs/indexes/CONFORMANCE_GAP_CLOSURE_V1.md)
- [Canonical repository layout](docs/indexes/CANONICAL_REPOSITORY_LAYOUT.md)
- [Canonical V6 architecture](docs/canonical/CANONICAL_MASTER_ARCHITECTURE_V6.md)
- [Recovery audit](docs/recovery/VAIXLNS_MASTER_RECOVERY_AUDIT.md)
- [Tools / ARC-X Ω](docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md)

## Canonical boundary

\`\`\`text
NEXENT
DISCOVER → DESIGN → SEARCH → SIMULATE → PROPOSE
                      │
                      ▼
VAIXLNS
CANONICALIZE → GOVERN → VERIFY → ADOPT → OPERATE
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
  VAIXLNS-unified  vaixlns-core  CSD / INTENT / VX
\`\`\`

Historical names and variants remain preserved through provenance and lineage. A proposal is not treated as implemented merely because it appears in an architectural document.

- [VLA Federation Contract](docs/integration/VLA_FEDERATION_CONTRACT_V1.md)
- [OpenVLA provider registry](registry/vla.openvla.7b.json)


## VX Cognitive Fabric

- [VX Ω-Cognitive Fabric](docs/cognitive/VX_OMEGA_COGNITIVE_FABRIC_V1.md)
- [VLNS Model Activation Fabric](docs/cognitive/VLNS_MODEL_ACTIVATION_FABRIC_V1.md)
- [VX Cognitive Fabric Restoration Index](docs/cognitive/VX_COGNITIVE_FABRIC_RESTORATION_INDEX_V1.md)
- [Capability Genome schema](schemas/vx-capability-genome.schema.yaml)
- [Ω-Arena schema](schemas/vx-arena.schema.yaml)

**Boundary:** VAIXLNS is canonical authority; VLNS is the governed model/semantic activation boundary; VX is the cognitive execution, experiment, verification, replay, and capability-synthesis boundary. Historical repository identities remain evidence-gated.


## VLNS → VX Governed Activation

- [Canonical activation bridge contract](docs/integration/VLNS_VX_ACTIVATION_BRIDGE_V1.md)
- [Signed activation envelope schema](schemas/vlns-activation-envelope.schema.json)
- [VLNS activation contract registry](registry/vlns_activation_contract.v1.json)

The contract has a reference implementation under VAIXLNS-unified with a green verification run, plus a companion fail-closed pre-activation gate in the vx-agents-fabric feature branch with green unit-test CI. Live VLNS connectivity, external service conformance, VLNS↔NAXLNS identity, and canonical admission remain unverified until evidence closes the required gates.
