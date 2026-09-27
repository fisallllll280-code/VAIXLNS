# VAIXLNS Ω∞ Integrated Architecture Specification

## Objective

Turn governed intent into deterministic, observable, verifiable execution while retaining complete provenance through failure and recovery.

## Canonical lifecycle

INTENT -> PLAN -> AUTHORIZE -> EXECUTE -> OBSERVE -> VERIFY -> PROVE -> RECORD -> REPLAY -> FAILURE -> RECOVERY -> VERIFY

## Core objects

- Intent: immutable request with canonical identifier.
- Plan: deterministic execution plan derived from Intent.
- Authorization: explicit policy decision bound to the plan.
- Event: append-only state transition with parent/hash provenance.
- Observation: runtime evidence produced by execution.
- Proof: independently derived verification result.
- Failure: explicit event/state, never deletion.
- Recovery: new branch/state referencing the failed state.
- Replay: reconstruction from recorded events and immutable inputs.
- Gap: explicit uncertainty or unavailable evidence.

## Security boundary

Authorization precedes execution. Execution cannot manufacture its own authority. Secrets and privileged capabilities are outside the evidence payload and referenced by capability identifiers only.

## Determinism

Equivalent canonical inputs and policy produce equivalent plans and event semantics. Every event has a stable canonical representation and content hash.

## Recovery invariant

For a failed execution F and recovered execution R:

1. F remains addressable.
2. R references F as its predecessor.
3. Replay(F) remains possible.
4. Verification(R) is independent of the mechanism that performed R.
5. The final record contains both failure and recovery evidence.

## Evidence bundle

A golden run MUST emit:

- intent.json
- plan.json
- authorization.json
- events.jsonl
- observations.jsonl
- verification.json
- failure.json
- recovery.json
- replay.json
- gaps.json

## Acceptance states

VERIFIED | SPECIFIED | PARTIAL | MISSING | CONFLICT | PROPOSAL

These are evidence states, not quality rankings.

## Compatibility rule

This architecture integrates with existing VAIXLNS concepts rather than replacing them. Existing V/VV/VX/XV, Ω registries, Genome/Canonical Index, SUF, intelligence, governance, verification, security, simulation, and recovery concepts remain first-class.

## Test contract

The companion test must prove:
- canonical lifecycle exists;
- failure is represented;
- recovery references failure;
- failure history is not deleted;
- replay can reconstruct the event chain;
- gaps are explicit.
