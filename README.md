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
- [Unified innovation delivery map](docs/recovery/VAIXLNS_UNIFIED_INNOVATION_DELIVERY_MAP_2026-10-10.md)
- [AEPF adversarial engineering and proof fabric](docs/architecture/AEPF_ADVERSARIAL_ENGINEERING_AND_PROOF_FABRIC_V1.md)
- [Typed federation contract edges](registry/federation/federation_contract_edges.v1.json)
- [Federation preflight CLI](scripts/federation_preflight.py)
- [Tools / ARC-X Ω](docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md)
- [ARC-X Federated Integration & Link Compiler](docs/tools/ARC_X_FEDERATED_INTEGRATION_LINK_COMPILER_V1.md)
- [ARC-X Bounded Adaptive Evolution Planner](docs/tools/ARC_X_BOUNDED_ADAPTIVE_EVOLUTION_V1.md)
- [ARC-X Universal Model Gateway](docs/tools/ARC_X_UNIVERSAL_MODEL_GATEWAY_V1.md)
- [ARC-X Bounded Self-Provisioning Compute Fabric](docs/tools/ARC_X_SELF_PROVISIONING_COMPUTE_FABRIC_V1.md)
- [VA Genesis Operational Engine v1](docs/tools/VA_GENESIS_OPERATIONAL_ENGINE_V1.md)

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


## VX Sovereign Tool Control & Universal Agents

- [Sovereign Tool Control Fabric](docs/tools/VAIXLNS_SOVEREIGN_TOOL_CONTROL_FABRIC_V1.md)
- [Universal VX Agent Runtime & Engineering Fabric](docs/architecture/VX_UNIVERSAL_AGENT_RUNTIME_AND_ENGINEERING_FABRIC_V1.md)
- [Tool action envelope schema](schemas/vx-tool-action-envelope.v1.schema.json)
- [Tool policy decision schema](schemas/vx-tool-policy-decision.v1.schema.json)
- [Agent runtime profile schema](schemas/vx-agent-runtime-profile.v1.schema.json)
- [VX runtime role binding map (proposed, not active)](registry/vx-runtime-role-binding-map.v1.json)
- [VX agent role catalog (35 logical role templates)](registry/vx-agent-runtime-profiles.v1.json)
- [Default tool-control policy (inactive proposal)](registry/vx-tool-control-default-policy.v1.json)
- [Reference policy evaluator](tools/vx_tool_control_reference.py)
- [Evaluator unit tests](tests/test_vx_tool_control_reference.py)

**Boundary:** every agent profile requires the VX runtime and federation gate; direct tool invocation is disabled by contract. The catalog is a set of role templates, not evidence of deployed agents. The reference evaluator does not execute tools and does not itself establish runtime enforcement.

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


## Four-System Federation Readiness

Run the deterministic, read-only preflight from the repository root:

```bash
python scripts/federation_preflight.py
```

The command validates the system and typed-edge manifests and emits a digest-bound JSON readiness report. A structurally valid report does not mean that services are connected or running. Identity mappings marked UNVERIFIED remain blocked, and the preflight never grants authority, writes canonical state, executes workloads, or probes external endpoints.

The federation contract regression suite can be run with:

```bash
python scripts/validate_four_system_federation.py
python scripts/validate_federation_contract_edges.py
python -m unittest tests.test_four_system_federation tests.test_federation_contract_edges tests.test_federation_preflight -v
```
