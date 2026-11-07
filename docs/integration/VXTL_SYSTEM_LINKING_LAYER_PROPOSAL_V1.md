# VXTL — VX System-Linking Layer (Proposal)

**Status:** PROPOSAL — architecture clarification only; implementation and live connectivity are not verified.
**Scope:** VAIXLNS + VLNS + VX + NEXNET
**Branch:** feat/omega-arena-four-system-audit-20261015

## Intent

Record the user's architectural clarification that **VXTL is the linking/integration tool for the systems, with VX as the governed execution/runtime boundary**. This document does not claim that VXTL already exists as executable code or that the four systems are connected.

## Proposed responsibility split

- **VAIXLNS / Ω.000:** canonical identity, authority, registry, provenance, admission decisions, recovery policy.
- **VXTL (proposed linking layer):** discover registered endpoints; resolve declared system identities; negotiate versioned contracts; route requests/events; normalize transport errors; propagate correlation IDs; expose connection health and evidence.
- **VX:** execute only authorized operations through its governed runtime/supervisor; enforce capability and resource boundaries; record execution events.
- **VLNS:** knowledge/discovery capability only after the repository identity and contract are verified.
- **NEXNET:** network/discovery capability only after the NEXNET ↔ NEXENT identity mapping and contract are verified.
- **ARC-X:** independently assess claims, evidence, contradictions, and admission gates; it must not infer successful connectivity from configuration alone.
- **Ω-Arena:** exercise the integration contracts with deterministic simulations first, then authenticated sandbox integration tests after identity and endpoint verification.

## Required VXTL contract

Every connection record should include:
- stable `system_id` and `endpoint_id`
- canonical repository and immutable source revision
- `identity_state`, `contract_state`, `connectivity_state`
- protocol and schema versions
- declared capabilities and least-privilege authorization
- timeout, retry, idempotency, and circuit-breaker policy
- request/correlation ID and event provenance
- health-check evidence with timestamp and source revision
- secret references only (never raw credentials)
- replayable test evidence and verifier identity

## State model

`DISCOVERED → IDENTITY_VERIFIED → CONTRACT_VERIFIED → AUTHORIZED → CONNECTIVITY_TESTED → ADMITTED`

Any failed or missing gate returns `HOLD`; identity is never inferred from a repository name. A simulation can reach only `SIMULATED`, never `CONNECTIVITY_TESTED` or `ADMITTED`.

## Mandatory blockers carried from the current federation record

- `VLNS ↔ NAXLNS`: `UNVERIFIED`; do not activate the adapter.
- `NEXNET ↔ NEXENT`: `UNVERIFIED`; do not activate the adapter.
- `VX`: one system with multiple repository surfaces; implementation is `PARTIAL`.
- `VAIXLNS`: canonical control plane is identified, but runtime readiness is not established.

## Ω-Arena acceptance tests

1. Unknown system identity is denied.
2. A repository name alone cannot satisfy identity verification.
3. Contract/schema version mismatch returns `HOLD`.
4. Missing or insufficient capability authorization is denied.
5. Simulation results are marked `SYNTHETIC` and cannot promote a connection.
6. Timeouts/retries do not duplicate non-idempotent operations.
7. Correlation IDs and immutable source revisions appear in every evidence record.
8. A stale health check cannot establish current connectivity.
9. Provider/adapter self-report is not sufficient evidence; an independent verifier is required.
10. No automatic promotion, merge, or production deployment occurs.

## Change boundary

This proposal is additive. Do not modify `project.genome`, `registry/omega/omega-000-master-index.json`, or historical source artifacts. Do not merge or deploy as part of this task.

## Current disposition

- VXTL role: `SPECIFIED` by this proposal.
- VXTL executable implementation: `MISSING / NOT INSPECTED`.
- Four-system live connectivity: `UNVERIFIED`.
- Permission to merge/deploy: not granted.
