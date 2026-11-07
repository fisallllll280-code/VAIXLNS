# VAIXLNS Canonical Control Plane v1

## Authority

- Golden Source: project.genome::v1.0.0
- Authority Anchor: Ω0_GENESIS_CORE
- Master Index: Ω.000
- Canonical repository: fisallllll280-code/VAIXLNS

## State separation

Lifecycle and epistemic state are independent.

Lifecycle:
DRAFT → ACTIVE → EVOLVING → QUARANTINED → ARCHIVED

Epistemic:
PROPOSAL → SPECIFIED → IMPLEMENTED → VERIFIED

Non-success states remain explicit:
PARTIAL, MISSING, CONFLICT, RECOVERED

A repository, module, or proposal MUST NOT become VERIFIED merely because it is present in Git history.

## Canonical control graph

project.genome
  ↓
Ω.000 Master Index
  ↓
Repository / System Contracts
  ↓
Implementation
  ↓
Tests + Conformance Gates
  ↓
Evidence + Provenance
  ↓
VERIFIED
  ↓
Authority-controlled promotion
  ↓
CANONICAL

## Failure rule

Rejected changes preserve the prior canonical state. Recovery creates a new evidenced state/branch rather than rewriting historical truth.

## Cross-repository role boundary

- VAIXLNS: canonicalize, govern, verify, adopt.
- VAIXLNS-unified: integrated execution surface.
- NEXENT: discovery, search, synthesis and research.
- Specialized kernels remain behind explicit contracts until evidence supports consolidation.

## Determinism boundary

The canonical control plane treats deterministic computation as the default for identity, hashing, registry ordering, admission decisions and replay-critical state. Wall-clock time, random UUID generation and external nondeterminism must not become implicit inputs to replay-critical decisions.

## Reconstruction

The next closure stage is a machine-executable reconstruction command that rebuilds the control model from project.genome, Ω.000, contracts, source and recorded evidence, then emits a reproducibility/equivalence score. This document does not claim that the reconstruction engine is already implemented.
