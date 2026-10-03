# ARC-X Ω — Epistemic Reality Compiler
## Canonical Tool Specification v1.0

**Status:** SPECIFIED  
**Authority:** project.genome::v1.0.0  
**Authority Anchor:** Ω0_GENESIS_CORE  
**Master Registry:** Ω.000  
**Canonical Owner:** VAIXLNS  
**Primary Surface:** Repository / Architecture / Evidence tooling  
**Source date:** 2026-10-03

> This specification consolidates the previously drafted repository-recovery, index-reconstruction, epistemic verification, language, architecture-compilation, and closed-loop evolution concepts into one coherent tool definition. It does not claim production implementation.

---

## 1. Definition

ARC-X Ω (Epistemic Reality Compiler) is the governed tool that translates repository and runtime evidence into a typed, provenance-preserving representation of system reality, then translates verified findings into architecture candidates, proof obligations, and controlled execution requests.

ARC-X is a compiler and reconstruction boundary, not a sovereign authority.

It may:
- retrieve and fingerprint sources;
- reconstruct repository/system structure;
- atomize architecture and capabilities;
- separate observation, evidence, inference, proof, and authority;
- detect gaps, contradictions, and divergence;
- build an Epistemic Intermediate Representation (EIR);
- compile EIR into architecture and execution candidates;
- generate proof obligations and verification plans;
- construct counterfactual and adversarial test scenarios;
- reconstruct observed reality after execution;
- emit architecture deltas and controlled evolution proposals.

ARC-X may not grant authority to itself or to generated artifacts.

## 2. Canonical Position in VAIXLNS

```text
                         ΩΩ CANON
                            │
                     AUTHORITY GATE
                            │
                  VERIFICATION FABRIC
                            │
              ┌─────────────▼─────────────┐
              │          ARC-X Ω            │
              │ Epistemic Reality Compiler │
              └─────────────┬─────────────┘
                            │
                      EPISTEMIC IR
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          NEXENT            VV             VX
       discover/design   verify/prove    execute/observe
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                       OBSERVED REALITY
                            │
                            ▼
                         ARC-X Ω
                            │
                            └────► next reconstruction
```

### Responsibility boundaries

| Surface | Responsibility | ARC-X relationship |
|---|---|---|
| VAIXLNS | Canonical authority, governance, registry, recovery | Owns ARC-X contract and admission |
| NEXENT / NEXNET boundary | Discovery, search, design, synthesis, evolution candidates | Supplies candidate knowledge; never canonical authority |
| VLNS / NAXLNS boundary | Knowledge/discovery and adversarial analysis | Supplies knowledge/evidence candidates; identity mapping remains separately evidenced |
| VV | Verification, proof, conformance | Validates ARC-X obligations and candidate claims |
| VX | Deterministic execution, events, state, replay | Executes admitted candidates and produces observations |
| ARC-X | Compilation, reconstruction, semantic normalization, provenance, gap analysis | Bridges the above without replacing them |

## 3. Governing Epistemic Separation

ARC-X MUST keep these categories distinct:

```text
OBSERVATION ≠ EVIDENCE ≠ INFERENCE ≠ CLAIM ≠ PROOF ≠ AUTHORITY
```

Forbidden implicit promotions:

```text
Inference  → Truth         ✗
Evidence    → Canon        ✗
Projection  → Canon        ✗
Generation  → Genesis      ✗
AI          → Authority    ✗
README      → Runtime Fact ✗
Startup     → Verification ✗
```

Canonical admission path:

```text
Evidence
   ↓
Claim
   ↓
Justification
   ↓
Verification
   ↓
Proof
   ↓
Authority Gate
   ↓
Canonical Commit
```

ARC-X MUST preserve uncertainty and explicitly represent missing evidence.

## 4. Source and Retrieval Contract

ARC-X operates on versioned evidence, not on an implicitly moving repository head.

### Required source metadata

- repository identifier;
- source revision / commit SHA;
- path or artifact identifier;
- content hash;
- retrieval timestamp;
- retrieval result;
- parser/schema version;
- extraction result;
- provenance link.

### Deterministic retrieval

```text
SOURCE
  ↓
REVISION PIN
  ↓
HASH CAPTURE
  ↓
RETRIEVAL RECEIPT
  ↓
PARSE
  ↓
EXTRACTION
```

The same pinned source revision and equivalent configuration MUST produce the same normalized extraction result.

## 5. Repository Reconstruction

The repository toolchain is a concrete ARC-X input lane.

### Pipeline

```text
GitHub / Files / Runtime Evidence
        ↓
Deterministic Retrieval
        ↓
Source Revision + Hash Capture
        ↓
Schema / Identity Extraction
        ↓
Repository Atomization
        ↓
System / Capability / Contract Graph
        ↓
Ω.000 Index Reconstruction
        ↓
Cross-System Reconciliation
        ↓
Evidence Classification
```

### Repository atomization

A repository MUST NOT be treated as a single opaque system object.

ARC-X decomposes it into:

```text
Repository
├── Identity
├── Source Revisions
├── Files / Artifacts
├── Languages
├── Modules
├── Components
├── Interfaces
├── Contracts
├── States
├── Events
├── Dependencies
├── Policies
├── Authority Boundaries
├── Capabilities
├── Failure Modes
├── Recovery Paths
├── Tests
├── Observability
├── Evidence
├── Proof Obligations
└── Lineage
```

A repository-to-system mapping is evidence-bearing. Similar names do not establish identity equivalence.

## 6. Architecture Atomization and Genome

ARC-X normalizes architectures into comparable structures.

### Architecture Genome

```text
GENOME
├── Purpose
├── Capabilities
├── Components
├── Topology
├── Contracts
├── State Model
├── Event Model
├── Authority Model
├── Resource Model
├── Failure Model
├── Recovery Model
├── Security Model
├── Proof Model
├── Observability Model
└── Evolution Rules
```

The genome is a representation, not a source of authority.

Historical variants remain addressable:

```text
Legacy ID → Canonical ID → Variant/Fork → Supersession → Lineage
```

No historical item is silently deleted because a newer architecture exists.

## 7. Epistemic Intermediate Representation (EIR)

EIR is the canonical interchange layer between repository evidence, semantics, architecture, proof, and execution.

### EIR domains

```text
EIR
├── Identity IR
├── Source IR
├── Evidence IR
├── Claim IR
├── Justification IR
├── Contradiction IR
├── Uncertainty IR
├── Capability IR
├── Architecture IR
├── State IR
├── Event IR
├── Policy IR
├── Proof IR
├── Governance IR
├── Execution IR
└── Observation IR
```

### Core EIR relation

```text
Source
  ↓
Evidence
  ↓
Claim
  ↓
Justification
  ↓
Proof Obligation
  ↓
Verification Result
  ↓
Authority Decision
```

EIR MUST carry provenance to the original source object from which each material statement was derived.

## 8. Language Control Layer

ARC-X supports the project language direction as a semantic control layer, not as decorative syntax.

```text
Language
   ↓
Meaning
   ↓
Type
   ↓
EIR
   ↓
Proof Obligation
   ↓
Architecture
   ↓
Server Contract
   ↓
Execution Candidate
```

Candidate language families may include:
- VSL — semantic language;
- VML — meaning/model language;
- VDL — definition/decomposition language;
- VPL — proof/policy language;
- VQL — verification/query language.

These names remain specified/proposed unless independently implemented and verified.

### Epistemic typing

The language/type system SHOULD prevent invalid category transitions such as:

```text
Inference<T> → CanonicalTruth
Evidence<T>  → Authority
Candidate<T> → ProductionSystem
```

without an explicit verification and admission path.

## 9. Proof-Carrying Architecture

An ARC-X architecture candidate is incomplete without its verification envelope.

```text
ARCHITECTURE CANDIDATE
├── Contracts
├── Invariants
├── Assumptions
├── Constraints
├── Proof Obligations
├── Simulation Evidence
├── Adversarial Results
├── Causal Evidence
├── Failure Analysis
├── Verification Result
└── Lineage
```

A candidate is not canonical merely because it was generated.

## 10. Gap and Contradiction Analysis

ARC-X MUST represent at least:
- Knowledge Gap;
- Capability Gap;
- Architecture Gap;
- Execution Gap;
- Verification Gap;
- Ontology Gap;
- Identity Conflict;
- Dependency Conflict;
- Evidence Gap;
- Reality Divergence.

### Gap loop

```text
Observed Reality
      ↓
Current Capability Map
      ↓
Required Capability Map
      ↓
Delta
      ↓
Gap
      ↓
Candidate
      ↓
Verification
```

### Contradiction handling

Conflicting records are preserved as conflicting records until resolved by evidence.

```text
CONFLICT → EXPOSE → ANALYZE → TEST / RESEARCH → RECONCILE
```

Never:

```text
CONFLICT → SILENT MERGE
```

## 11. Counterfactual and Adversarial Compilation

ARC-X may compile architecture candidates into controlled experiments.

### Counterfactuals

```text
Architecture
   ↓
Digital Twin
   ↓
Counterfactual World
   ↓
Simulation
   ↓
Causal Analysis
   ↓
Blast Radius
```

Examples include:
- component removal;
- dependency failure;
- policy change;
- load increase;
- state divergence;
- partial recovery;
- alternate topology;
- alternate capability assignment.

### Adversarial path

```text
Candidate
   ↓
Red Team / Fault Injection
   ↓
Adversarial Conditions
   ↓
Failure / Contradiction
   ↓
Causal Diagnosis
   ↓
Mutation Candidate
```

Simulation output is evidence for evaluation, not automatic authority.

## 12. Closed-Loop Architecture Evolution

ARC-X participates in a controlled loop:

```text
REALITY
  ↓
OBSERVE
  ↓
RETRIEVE
  ↓
RECONSTRUCT
  ↓
MODEL
  ↓
VERIFY
  ↓
PROPOSE
  ↓
NEXENT CANDIDATE GENERATION
  ↓
VV VERIFICATION / PROOF
  ↓
VAIXLNS ADMISSION
  ↓
VX EXECUTION
  ↓
OBSERVE
  ↓
RECONSTRUCT
```

The loop MUST preserve the previous state and its lineage.

```text
System_0
  ↓
System_1 Candidate
  ↓
Verification
  ↓
System_1 Admitted
  ↓
Observed Runtime
  ↓
System_2 Candidate
```

ARC-X does not directly overwrite the canonical system as part of discovery.

## 13. Server Genesis Interface

The server-side factory lane is compiled from verified contracts.

```text
Capability Algebra
       ↓
Server Specification
       ↓
Server Contract
       ↓
Architecture Candidate
       ↓
Proof Obligations
       ↓
Sandbox / Simulation
       ↓
Verification
       ↓
Performance / Reliability
       ↓
Governance
       ↓
Canonical Server
```

When ARC-X discovers a missing capability:

```text
CAPABILITY GAP
   ↓
INNOVATION CANDIDATE
   ↓
LANGUAGE / EIR REPRESENTATION
   ↓
SERVER CONTRACT
   ↓
NEXENT CANDIDATE
   ↓
VV VERIFICATION
   ↓
VX EXECUTION
   ↓
OBSERVED EVIDENCE
   ↓
ARC-X RECONSTRUCTION
```

## 14. Runtime Admission Boundary

ARC-X integrates with, but does not replace, the existing Index Recovery Engine + Runtime Admission Engine.

Canonical runtime states:

```text
DISCOVERED
   ↓
RETRIEVED
   ↓
RECONSTRUCTED
   ↓
RECONCILED
   ├── CONFLICT → BLOCKED
   ├── MISSING  → BLOCKED
   └── READY
        ↓
     ADMITTED
        ↓
     STARTING
        ↓
   HEALTH_CHECK
        ↓
     TESTING
        ↓
     RUNNING
        ↓
   OBSERVED / EVIDENCED
```

Admission invariants:
- no deterministic source → no canonical reconstruction;
- no dependency resolution → no startup;
- no health result → no RUNNING;
- no test result → no verified execution;
- no evidence → no VERIFIED;
- no authority gate → no canonical commit.

## 15. Evidence Record

Every reconstruction, compilation, admission, execution, and verification boundary MUST be traceable.

Minimum record:

```yaml
tool_id: ARC-X-OMEGA
tool_version: 1.0
system_id: string
repository: string
source_revision: string
content_hash: string
retrieval_timestamp: string
reconstruction_id: string
eir_id: string
verification_state: VERIFIED|SPECIFIED|PARTIAL|MISSING|CONFLICT|PROPOSAL
dependency_resolution: PASS|FAIL|PENDING
startup_result: PASS|FAIL|PENDING
health_result: PASS|FAIL|PENDING
test_result: PASS|FAIL|PENDING
proof_status: PASS|FAIL|PENDING
authority_decision: ADMITTED|BLOCKED|PENDING
execution_evidence: string|null
previous_state: string|null
transition_reason: string
```

## 16. Logical Operations

The concrete transport is implementation-specific. The semantic operations are:

### Retrieval
- retrieve_source
- fingerprint_source
- capture_retrieval_receipt

### Reconstruction
- extract_identity
- atomize_repository
- reconstruct_index
- reconstruct_genome
- build_lineage

### Epistemic compilation
- normalize_evidence
- compile_claims
- build_eir
- detect_contradictions
- compute_gaps

### Architecture compilation
- compile_architecture_candidate
- compile_proof_obligations
- compile_counterfactuals
- compile_adversarial_tests

### Federation
- reconcile_systems
- resolve_dependencies
- prepare_admission

### Runtime bridge
- request_verification
- request_execution
- capture_observation
- reconstruct_runtime
- replay_reconstruction

### Evolution
- emit_architecture_delta
- create_evolution_candidate
- request_governed_adoption

## 17. Outputs

ARC-X SHOULD emit inspectable artifacts rather than opaque responses.

Recommended artifact set:

```text
source.receipt.json
repository.model.json
system.identity.json
architecture.genome.json
eir.json
claims.jsonl
evidence.bundle/
proof.obligations.json
verification.plan.json
counterfactual.plan.json
adversarial.plan.json
reconstruction.record.json
architecture.delta.json
admission.request.json
```

## 18. Conformance Requirements

A conforming ARC-X implementation MUST demonstrate:

### C1 — Deterministic retrieval
Pinned revision + equivalent configuration produces equivalent source normalization.

### C2 — Provenance
Every material derived object retains source lineage.

### C3 — Epistemic separation
Inference, evidence, proof, and authority remain distinct types/states.

### C4 — Conflict preservation
Conflicts are retained and surfaced.

### C5 — Historical preservation
Historical artifacts remain addressable.

### C6 — Deterministic reconstruction
Equivalent inputs reconstruct an equivalent EIR/index.

### C7 — No self-authority
ARC-X cannot change a canonical authority decision by itself.

### C8 — Proof obligations
Every canonical promotion candidate has explicit obligations.

### C9 — Runtime boundary
ARC-X cannot treat startup/health as semantic proof.

### C10 — Replay
A reconstruction can be replayed from immutable inputs and recorded provenance.

### C11 — Evolution isolation
Generated modifications are candidates until admitted.

### C12 — Observability
Every state transition is evidence-bearing.

## 19. Status Model

Use the existing project evidence model:

```text
RECOVERED
CANONICAL
PROPOSED
IMPLEMENTED
VERIFIED
```

For uncertainty and audit state, retain:

```text
SPECIFIED
PARTIAL
MISSING
CONFLICT
```

These states MUST NOT be treated as a quality ranking.

For ARC-X specifically, the current state is:

```text
CANONICAL OWNER: VAIXLNS
SPECIFICATION: SPECIFIED
IMPLEMENTATION: NOT PROVEN BY THIS DOCUMENT
PRODUCTION RUNTIME: NOT PROVEN
```

## 20. Historical Preservation / Deduplication Rule

This specification supersedes no historical wording.

The repository corpus may contain overlapping names such as:
- Architecture Self-Discovery Engine;
- Architecture Laboratory;
- System-of-Systems Compiler / T2C;
- Architecture Recombination Engine;
- CSE;
- MCI;
- SFC;
- RDV;
- FPO;
- OIF;
- Reality Divergence Engine;
- Reality Twin + Architecture Twin;
- Index Recovery Engine;
- Runtime Admission Engine;
- System Forge.

ARC-X provides a canonical composition boundary for these concepts where compatible; it does not erase their original names or historical records.

Placement rule:

```text
Existing Canonical Owner
+
Capability
+
Explicit Contract
+
Evidence
+
Proof
+
Lifecycle
+
Lineage
```

Do not create a new top-level authority when a capability can be expressed inside an existing owner.

## 21. Security / Authority Rules

1. ARC-X has no independent sovereignty.
2. Secrets never become evidence payload content.
3. External effects are capability-bound and authorization-bound.
4. Repository access is evidence collection, not authority acquisition.
5. Generated code/artifacts are untrusted until verified and admitted.
6. A successful compile is not a successful deployment.
7. A successful execution is not proof of semantic correctness.
8. A source README cannot override executable evidence.
9. Identity mappings that remain unresolved stay unresolved.
10. Canonical writes occur through one controlled admission path.

## 22. Canonical Formula

```text
REALITY
  ↓
OBSERVATION
  ↓
EVIDENCE
  ↓
SEMANTICS
  ↓
CLAIMS
  ↓
EPISTEMIC IR
  ↓
PROOF OBLIGATIONS
  ↓
ARCHITECTURE
  ↓
EXECUTABLE CANDIDATE
  ↓
VERIFICATION
  ↓
GOVERNANCE
  ↓
EXECUTION
  ↓
OBSERVED REALITY
  ↓
RECONSTRUCTION
  ↓
ARCHITECTURE DELTA
  ↓
NEXT CONTROLLED EVOLUTION
```

### Non-negotiable authority rule

> The system may generate, infer, explain, challenge, simulate, compile, and verify — but it cannot grant itself authority.

## 23. Implementation Gate

This specification becomes IMPLEMENTED only after a repository-backed implementation demonstrates the conformance requirements with reproducible tests and evidence.

The first implementation slice should be:

```text
GitHub Retrieval
  ↓
Pinned Source
  ↓
Repository Atomizer
  ↓
Identity + Capability Extraction
  ↓
EIR
  ↓
Reconstruction Record
  ↓
Deterministic Replay
```

No automatic production mutation is required for the first slice.