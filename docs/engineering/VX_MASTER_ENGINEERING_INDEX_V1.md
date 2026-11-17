# VX — Master Engineering Index and Formulation Contract v0.1.0

> Status: PROPOSED / NOT VERIFIED. Branch-only design contract; not a runtime success claim.
> Authority: VAIXLNS. Execution routing: VX. Canonical admission: explicit authorized review only.
> Scope: M0–M25, ΩΣ, Meta-Theory, Ω∞, Evolution-of-Evolution, Ω91–Ω100.
> Protected: `project.genome`, `Ω.000`; no edits, merge to main, or automatic promotion.

## 1. Governing transformation

`EveryFormulation -> Specification -> FormalModel -> Contracts -> Implementation -> Tests -> Evidence -> Verification -> PromotionProposal -> AuthorityDecision`.

A proposal or extracted title is never evidence of implementation. Absence from a bounded checkout is `NOT_OBSERVED`, not `MISSING`. Preserve source-claimed statuses independently from independently verified statuses.

## 2. One atomic formulation record

Each formulation must have 20 applicable facets (or explicit, reviewed `NOT_APPLICABLE` rationale):
1 Identity; 2 Origin; 3 Definition; 4 Formalization; 5 Ontology; 6 Primitives; 7 Operators; 8 Invariants; 9 Constraints; 10 Contracts; 11 Architecture; 12 Mechanism; 13 Algorithms; 14 Dependencies; 15 Failure Model; 16 Recovery Model; 17 Verification; 18 Simulation; 19 Evidence; 20 Evolution.

Required identity/provenance: `formulation_id`, `historic_ids[]`, `aliases[]`, `owner_system`, `source_repository`, `source_path`, `source_commit`, `raw_sha256`, `normalized_sha256` (algorithm + version), `source_claimed_status`, `observation_status`, `verification_status`, `canonical_admission`. Store raw bytes independently; Git blob IDs are not SHA-256.

Required formal data: `model_language`, `assumptions[]`, `axioms[]`, `types`, `units`, `preconditions`, `postconditions`, `invariants[]`, `proof_obligations[]`, `counterexamples[]`, `bounded_scope`, `resource_budget`. Explicitly mark unproved conjectures and unsupported domains.

Required execution data: `interfaces`, `runtime_dependencies`, `implementation_paths[]`, `test_commands[]`, `test_receipts[]`, `evidence_artifact_digests[]`, `replay_instructions`, `failure_modes[]`, `recovery_procedure`, `reviewer`, `authority_decision`. Credentials must be references, never secrets in registry files.

## 3. Capability map — targets, not existing engines

| Module | Target | Minimum bounded demonstrator | Acceptance evidence |
|---|---|---|---|
| M0 | Master Engineering Atlas Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M1 | Formulation Parser & Registry | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M2 | Law and Axiom Evaluator | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M3 | Primitive & Operator Runtime | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M4 | Algorithm Execution Framework | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M5 | Architecture Composer | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M6 | Ontology & Model Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M7 | Protocol & Contract Validator | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M8 | Knowledge Graph Fabric | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M9 | Proof & Evidence Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M10 | Failure & Counterexample Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M11 | Innovation Registry | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M12 | Evolution & Derivation Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M13 | Canonical Admission Registry | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M14 | Meta-Engineering Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M15 | Ontological Genesis Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M16 | Computational Possibility Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M17 | System Genesis Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M18 | Evolution-of-Evolution Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M19 | Knowledge & Truth Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M20 | Civilization Engineering Fabric | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M21 | Agent Fabric | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M22 | Structural Delta Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M23 | Engineering Closure Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M24 | Primitive Genesis Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |
| M25 | Law Synthesis Engine | Typed input/output contract; reject malformed or unauthorized input | Test receipt + source digest + reviewer |

Modules share the existing atomic index, source inventory, authority gate, and contract validator. They are capabilities, not 26 independent services. The modules M14–M25 have **no runtime-ready claim** from this document.

## 4. Historical formulation families

### ΩΣ System-of-Systems Genesis
Model entities, legal composition operators, ownership and trust edges. Validate that each assembled node has identity, authority, interfaces, and evidence lineage. A generated architecture remains a candidate until independently checked.

### Meta-Theory
Represent theories as typed assumptions, inference rules, falsifiable predictions, and scope. Distinguish syntactic consistency, model-checker satisfiability, empirical support and verified implementation. Never equate these proofs.

### Ω∞ Computational Possibility Engine
Explore explicitly bounded candidate spaces with reproducible seeds/budgets. Output candidate alternatives, objective functions, failure/counterexample traces, and Pareto comparisons; never assert exhaustive exploration of an unbounded space.

### Evolution-of-Evolution
Record strategy versions and mutation operators, run immutable baseline comparisons, test regressions, and block self-approval. A new optimizer cannot silently modify its own admission policy.

### Ω91–Ω100
Use one record per historically grounded domain, retain original IDs/names/source references, and mark gaps `UNRESOLVED`. Do not invent meanings or implementations without source extraction.

## 5. Repository integration (develop existing assets)

- `docs/indexes/INNOVATION_MASTER_INDEX.md`: historical innovation catalog; do not replace.
- `docs/innovation/INNOVATION_OPERATION_INDEX.md`: generated read-only projection; edit its source inputs, not generated output.
- `registry/innovation-operation-index.v1.json`: existing structured innovation projection.
- `tools/build_innovation_operation_index.py`: existing index generator.
- `docs/indexes/VAIXLNS_ZERO_LOSS_INDEX_V1.md`: 28-view source-bound index contract.
- `scripts/build_zero_loss_index.py`, `scripts/recover_zero_loss_index.py`: existing builder/recovery orchestration.
- `schemas/zero-loss-atomic-record.schema.json`: existing atomic-record contract; extend compatibly only after migration impact review.
- `registry/omega/omega-000-master-index.json` and `project.genome`: **read only**, no modifications.
- `VX-runtime`, `VAIXLNS-unified`, `NEXENT`: references must be source-inventoried with pinned revisions before asserting cross-repo coverage.

## 6. Stage plan and stopping conditions

| Stage | Work | Required evidence |
|---|---|---|
| E01 | Pin source revisions, identities, laws, protected-file hashes | Source inventory and SHA-256 |
| E02 | Parse formulations into typed registry without promotion | Schema test + lossless roundtrip |
| E03 | Ontology and primitive definitions | Type/invariant checks |
| E04 | Meta-Theory and knowledge assertions | Contradiction/unknown handling |
| E05 | Relation multigraph | Broken-link and cycle tests |
| E06 | ΩΣ system synthesis | Negative contract cases |
| E07 | Ω∞ bounded possibility exploration | Reproducible seed/counterexample |
| E08 | Agent orchestration through VX | Permission/identity/fail-closed tests |
| E09 | Independent proof and evidence validation | Signed or digest-bound receipts |
| E10 | Evolution strategy evaluation | Before/after and regression metrics |
| E11 | Ω91–Ω100 extraction from primary sources | Per-domain traceability |
| E12 | End-to-end federation and recovery | Replay, tamper, rollback evidence |

## 7. Mandatory test set

- T01: identity uniqueness and historical alias collision detection
- T02: source provenance and raw/normalized digest distinction
- T03: parse -> serialize -> parse semantic preservation
- T04: dependency/reference integrity and conflict reporting
- T05: invalid contract or unauthorized tool must fail closed
- T06: counterexample for an intentionally false invariant
- T07: replay determinism in an explicitly controlled environment
- T08: interrupted build and recover without silent data loss
- T09: external model claims never promote their own verification
- T10: protected-file diff unchanged
- T11: regression tests for existing index builders
- T12: unobserved/inaccessible never escalated to confirmed missing
- T13: baseline vs optimized throughput and latency on identical workloads
- T14: immutable evidence tied to a tested Git commit and environment
- T15: adversarial federation edge and identity mismatch blocked

Each result records command, exit status, environment, commit SHA, timestamp, evidence file and digest, reviewer, and reproduction instructions. All tests are **NOT_RUN** until executed and inspected.

## 8. Acceptance model

`SPECIFIED` requires linked source + typed contract. `IMPLEMENTED` requires actual code and corresponding recorded execution. `VERIFIED` requires a separate reproducible verification receipt tied to the exact artifact and environment. `CANONICAL` requires explicit authority decision and provenance continuity; no score overrides mandatory gates.

Before each acceptance: no prohibited changes to `project.genome` or `Ω.000`; no main merge; external spend = SAR 0 unless separately authorized; no deployment without approval. If independent checks are absent, decision is HOLD. Never label a source-reported assertion as observed runtime proof.

## 9. Sources and standard compatibility

SLSA Build Provenance: https://slsa.dev/spec/v1.0/provenance
in-toto attestation framework: https://in-toto.io
These inform artifact provenance and attestations; do not claim SLSA compliance without measuring actual conformance.

## 10. Current review state

- Documentation created on isolated branch only if repository write succeeds.
- Runtime tests: NOT_RUN.
- Source corpus completeness: UNKNOWN beyond checked files.
- Canonical promotion: DISABLED.
- Merge to main: NOT AUTHORIZED.
