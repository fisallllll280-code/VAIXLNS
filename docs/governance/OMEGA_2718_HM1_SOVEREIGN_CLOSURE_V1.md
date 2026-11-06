# Ω.2718 — HM-1 Sovereign Closure Domain

Status: PROPOSAL / NOT CLOSED
Canonical location: VAIXLNS registry and documentation. This specification does not amend project.genome or Ω.000.

## Purpose

Define eleven auditable control domains for constitutional binding, proof governance, closure decisions, historical ratification, failure handling, conflict resolution, proof obligations, constitutional change, trust roots, semantic drift, and independent audit.

## Closure semantics

HM-1 is CLOSED only when every required gate has a current, source-bound evidence record; the evidence passes schema, cryptographic, temporal, semantic, and independent-review checks; no critical drift or unresolved constitutional conflict exists; and the closure decision itself is recorded in a separately controlled ratification ledger.

An absent, stale, malformed, unsigned, revoked, or unverifiable item is BLOCKED or UNKNOWN, never PASS. A schema declaration or successful CI run alone does not prove live trust, real-world authority, immutability, or production readiness.

## Eleven layers

1. Constitutional Binding — binds authority to the canonical source and read-only boundaries. project.genome and Ω.000 remain read-only in this domain.
2. Meta-Proof — validates proof format, verifier identity/version, assumptions, dependencies, and reproducibility. Avoid infinite regress: the verifier and its trust basis are audited independently; the system does not claim every proof is proven by an endlessly recursive proof.
3. Sovereign Closure Engine — computes STRUCTURAL, SEMANTIC, TEMPORAL, and CONSTITUTIONAL gate results. Any missing required gate blocks closure.
4. Historical Ratification Ledger — append-only event model with canonical serialization, sequence numbers, previous-entry hash, current-entry hash, and signed receipts. Actual immutability requires external access controls or WORM storage and is not asserted by this specification.
5. Failure Sovereignty — storage, signature, clock, activation, and integrity failures preserve prior evidence and fail closed. Recovery appends a new event; it must not rewrite history.
6. Dominion Conflict Resolver — resolves conflicts using declared authority, policy priority, proof strength, freshness, and explicit override rules. No numeric authority score may silently override constitutional rules.
7. Proof Obligations Registry — each claim identifies required proof classes, evidence references, verifier, expiry/freshness policy, and pass/block state.
8. Constitutional Evolution Control — proposed amendments identify affected IDs, rationale, compatibility impact, required authorized signers, quorum policy, and delayed activation. Example thresholds are policy proposals, not active authority.
9. Trust Root Registry — only cryptographically validated, non-revoked roots with verified issuance and revocation state may anchor signatures. No placeholder public-key hashes count as trust roots.
10. Semantic Drift Detection — compares canonical semantic snapshots under named ontology and canonicalization versions. CRITICAL drift blocks ratification pending re-analysis and approval.
11. Sovereign Audit Domain — the engine under review cannot be its sole auditor. Independent reviewer identity, scope, source revision, method, evidence hash, findings, and disposition are required.

## Guided links

- Ω2718-HM1-L01: Constitutional Binding
- Ω2718-HM1-L02: Meta-Proof
- Ω2718-HM1-L03: Sovereign Closure Engine
- Ω2718-HM1-L04: Historical Ratification Ledger
- Ω2718-HM1-L05: Failure Sovereignty Model
- Ω2718-HM1-L06: Dominion Conflict Resolver
- Ω2718-HM1-L07: Proof Obligations Registry
- Ω2718-HM1-L08: Constitutional Evolution Control
- Ω2718-HM1-L09: Trust Root Registry
- Ω2718-HM1-L10: Semantic Drift Detection
- Ω2718-HM1-L11: Sovereign Audit Domain

## Required invariants

- Constitutional sources are referenced, never mutated by HM-1.
- No ratification without a complete, valid trust chain and required signatures.
- No claim is promoted to VERIFIED without evidence tied to an exact source revision and reproducible verifier result.
- Critical semantic drift, unresolved authority conflict, invalid signature, stale evidence, or failed independent audit blocks closure.
- Recovery preserves the event history and records the recovery as a new event.
- An engine may not be its sole auditor.
- Configuration examples, thresholds, sample IDs, timestamps, hashes, and signatures are illustrative until supplied and validated by an authorized operator.

## Acceptance gates

1. Structural: schema, IDs, required fields, references, and version compatibility validate.
2. Provenance: every evidence reference is revision-pinned and hash-checked.
3. Cryptographic trust: signatures validate against an approved, non-revoked trust chain.
4. Temporal: timestamp policy, clock uncertainty, expiry, and replay protections validate.
5. Semantic: ontology versions match and drift is below the ratification threshold.
6. Conflict: no unresolved constitutional conflict or unauthorized override exists.
7. Independent audit: an independent reviewer signs the audit receipt.
8. Recovery: fault-injection tests prove append-only history preservation.
9. Reproducibility: a second clean environment reproduces the same decision from the same inputs.
10. Ratification: authorized signers approve the exact closure digest.

## Current disposition

HM-1 specification: SPECIFIED by this document. Operational closure: BLOCKED / NOT VERIFIED. No trust root, live signing key, independently operated auditor, immutable storage service, or ratification receipt is provisioned by this document. Do not describe Ω.2718 as fully closed until all acceptance gates have independently verified evidence.