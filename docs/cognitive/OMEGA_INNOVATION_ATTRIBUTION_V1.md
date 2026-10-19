# Ω Innovation Attribution and Seven-Day Revalidation v1

**Status:** DERIVED / SPECIFIED  
**Authority:** `project.genome::v1.0.0`  
**Canonical owner:** VAIXLNS  
**Primary execution boundary:** VX

## Purpose

This contract connects Ω-Arena outcomes to the existing Atomic System Record, Capability Genome, Evidence, Provenance, and Replay surfaces. It does **not** introduce a parallel registry or a new memory layer.

## Attribution rule

1. The originator is the earliest evidenced source of the novel proposal.
2. Later models, minds, teams, or systems receive contribution/derivation credit.
3. Reuse of an existing invention is not a new invention.
4. If novelty cannot be established from evidence, attribution remains `UNRESOLVED`.
5. Attribution never promotes an object to VERIFIED; verification remains evidence-gated.

## Evidence chain

`proposal -> first_observation_event -> invention_fingerprint -> execution -> verification -> replay -> revalidation`

The attribution record references existing event/evidence/provenance artifacts rather than duplicating their contents.

## Seven-day window

The seven-day champion is scoped to a frozen evaluation window:

`FREEZE -> BASELINE -> CAPABILITY_TRIALS -> EXECUTION -> ADVERSARIAL_TEST -> REPAIR/COMPOSITION -> REPLAY/AUDIT -> FINAL_CHAMPION`

`TOURNAMENT_CHAMPION` means the best **validated capability composition** for that task/domain/constraint/window. It does not establish permanent model superiority.

## Integration

- **VLNS:** discovers and activates eligible model capabilities.
- **Mind Composer:** composes participating capabilities.
- **Capability Compiler:** produces the candidate capability.
- **VX:** owns execution, experiment control, Arena orchestration, verification, replay, and admission flow.
- **Existing Evidence/Provenance/Atomic Record surfaces:** remain the source of lineage and evidence.
- **∞ Memory:** receives the resulting lineage through existing memory/event mechanisms; no new memory layer is introduced.

## Status discipline

This document and its schema are DERIVED/SPECIFIED until executable conformance tests and reproducible evidence exist. No field in this contract is itself proof of invention, success, or verification.
