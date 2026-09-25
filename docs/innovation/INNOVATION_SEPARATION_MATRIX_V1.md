# VAIXLNS Innovation Separation Matrix v1

Snapshot: 2026-09-25

This matrix separates innovation by canonical owner, evidence source and implementation state.

## VAIXLNS canonical innovations

| Innovation | Family | Owner | State |
|---|---|---|---|
| Omega infinity / Constitution | Meta / Constitution | VAIXLNS | RECOVERED / CANONICAL |
| CME | Semantics | VAIXLNS | RECOVERED / CANONICAL |
| CTM | Truth | VAIXLNS | RECOVERED / CANONICAL |
| CDG | Derivation / Lineage | VAIXLNS | RECOVERED / CANONICAL |
| Master Registry | Canon | VAIXLNS | CANONICAL |
| Nexus / Graph of Everything | Graph / Canon | VAIXLNS | CANONICAL |
| Identity Fabric | Identity | VAIXLNS | RECOVERED / CANONICAL |
| Contract Fabric | Contracts | VAIXLNS | RECOVERED / CANONICAL |
| Decision Fabric | Decision | VAIXLNS | RECOVERED / CANONICAL |
| Policy Algebra | Governance | VAIXLNS | PROPOSAL |
| Trust Boundary | Security | VAIXLNS | RECOVERED |
| External World Boundary | Integration | VAIXLNS | RECOVERED |
| Resource Fabric | Resource | VAIXLNS | RECOVERED |
| Lifecycle Engine | Lifecycle | VAIXLNS | RECOVERED |
| Knowledge Lifecycle | Knowledge | VAIXLNS | RECOVERED |
| Contract-Centered Runtime | Runtime governance | VAIXLNS | RECOVERED / DERIVED |
| Canonical Semantic Engine | Semantics | VAIXLNS | PROPOSAL |
| Evidence DNA | Evidence / Provenance | VAIXLNS | PROPOSAL |
| Master Capability Indexer | Registry / Capability | VAIXLNS | PROPOSAL |
| Semantic Fingerprint Canonicalizer | Canonicalization | VAIXLNS | PROPOSAL |

## VX execution innovations

| Innovation | Family | Owner | State |
|---|---|---|---|
| VX deterministic runtime | Execution | VX | IMPLEMENTED / PARTIAL across execution surfaces |
| Event + State + Ledger | Event / State | VX | IMPLEMENTED / PARTIAL |
| Deterministic Replay | Verification | VX | IMPLEMENTED / PARTIAL |
| Replay Determinism Verifier | Conformance | VX | PROPOSAL |
| Deterministic Causal Execution Graph | Causality / Runtime | VX | PROPOSAL |
| Operational Integrity Fabric | Assurance | VAIXLNS + VX | PROPOSAL |
| Proof Lease | Authorization | VX / Core | IMPLEMENTED-BASELINE in source-bearing core surfaces |
| V-IR / VAMM | Semantic IR | VAIXLNS + VX | RECOVERED / DERIVED |
| Capability boundary | Execution governance | VX | IMPLEMENTED / PARTIAL |
| Self-healing runtime boundary | Recovery | VX | SPECIFIED |

## NEXENT-native innovation families

| Family | Representative innovations | Owner | State |
|---|---|---|---|
| Discovery | ASDE, Missing System Discovery Engine, Canonical Indexing Engine, Semantic Linking / Auto-Classification | NEXENT | SOURCE-ASSERTED / IMPLEMENTED-BASELINE mix |
| Architecture Search | Capability Genome, Architecture Genome + Mutation, Search Space, Laboratory, Recombination | NEXENT | SOURCE-ASSERTED |
| Synthesis | System-of-Systems Compiler / T2C, Theory-to-Rule, Recursive Generation | NEXENT | SOURCE-ASSERTED |
| Multi-Mind | Specialist Registry, Capability Routing, Dependency Coordination, Bounded Autonomy | NEXENT | IMPLEMENTED-BASELINE / SPECIFIED |
| Verification Research | Contradiction Engine, Formal Proof Orchestrator, Cross-Runtime Equivalence, Proof-Carrying Architecture | NEXENT | IMPLEMENTED-BASELINE / SOURCE-ASSERTED |
| Impact / Causality | Causal Architecture Graph, Blast-Radius Prediction, Temporal Architecture, Counterfactual Engine | NEXENT | SOURCE-ASSERTED / SPEC |
| Resilience | Failure Genome, Architecture Immune System, Complexity Budget, Conservation Laws, Evolution Firewall, Self-Healing Architecture, Recovery Certificate | NEXENT | SOURCE-ASSERTED |
| Simulation / Reality | Reality Divergence, Reality Twin + Architecture Twin, physics and deterministic simulation | NEXENT | SOURCE-ASSERTED / IMPLEMENTED-BASELINE |
| Memory / Evolution | Event Ledger, Replay, Provenance, Evolution Genealogy, Assumption Lifecycle, Semantic Regression | NEXENT | IMPLEMENTED-BASELINE / SOURCE-ASSERTED |
| Language / Ontology | NEX-DSL, NEO, Atomic Record, Canonical ID generation | NEXENT | IMPLEMENTED-BASELINE |
| Ecosystem | Standards, Certification, Integration, Compatibility, Benchmarking, Innovation Exchange, SDK | NEXENT research | SOURCE-ASSERTED |

## Anti-duplication rule

When a proposal overlaps an existing canonical capability, create a derived capability record instead of a new top-level system.

Required relation:
EXISTING OWNER + CAPABILITY + CONTRACT + EVIDENCE + PROOF + LIFECYCLE + LINEAGE

## Evidence rule

Research document, code prototype, test, simulation and production capability are separate evidence classes. None silently upgrades another.
