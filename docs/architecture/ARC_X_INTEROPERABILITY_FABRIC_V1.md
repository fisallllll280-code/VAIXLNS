# ARC-X Interoperability Fabric v1

Status: PROPOSAL until implementation and CI evidence are reviewed.

## Objective

Provide a shared contract for tools and services so ARC-X can discover declared capabilities, check connector provenance, evaluate authorization and risk, and produce a route plan with explicit capability gaps. A registry entry is not proof of a live connection.

## Connector contract

Every connector declaration must identify:

- stable tool ID, provider, adapter version, and contract version;
- lifecycle state: PROPOSED, REGISTERED, CONNECTED, VERIFIED, DISABLED, or QUARANTINED;
- typed capabilities, input/output schema references, and risk class;
- requested and granted scopes, declared side effects, and credential-handling mode;
- pinned source/provenance and content digest;
- health evidence, last verification time, policy version, and audit receipt.

## Capability lifecycle

PROPOSED -> CONTRACT_VALIDATED -> REGISTERED -> CONNECTIVITY_TESTED -> INDEPENDENTLY_VERIFIED -> POLICY_ADMITTED

Any failed or stale check transitions to QUARANTINED or DISABLED. REGISTERED does not mean CONNECTED; CONNECTED does not mean VERIFIED; VERIFIED does not itself grant write authority.

## Routing contract

A route planner may select only tools whose manifest is valid, state is VERIFIED, policy admission is explicit, and required capability is declared. Write-capable routes remain unavailable unless separately enabled and approved. The planner emits candidate routes and unresolved capabilities; it does not invoke connectors.

## Required interoperability invariants

1. Least privilege and per-capability scopes.
2. No unrestricted shell, arbitrary URL fetch, or generic tool passthrough.
3. Strict input/output schema validation, size limits, timeouts, idempotency keys, and bounded retries.
4. Untrusted connector outputs cannot modify ARC-X policy or system instructions.
5. Every result binds to tool ID, adapter version, policy version, request digest, response digest, timestamp, and evidence references.
6. Missing provenance, stale verification, schema mismatch, permission mismatch, or invalid receipt fails closed.
7. Secrets are referenced through a secret manager; secret values never enter EIR or audit reports.
8. Side-effecting operations require a separate authorization decision.
9. Human approval and provider/workspace permissions remain authoritative.
10. Tool failures and unavailable capabilities are explicit; no fabricated success or inferred connectivity.

## Integration layers

- Discovery: list connectors and declared capabilities.
- Contract: validate schemas and compatibility.
- Trust: verify source, identity, signatures, freshness, and revocation.
- Policy: evaluate scope, risk, approval, and environment.
- Routing: choose eligible capability providers and preserve fallback gaps.
- Invocation gateway: execute only typed, authorized calls (future component; not supplied by the registry alone).
- Evidence: normalize receipts and preserve provenance.
- Reconciliation: compare requested outcome to observed postconditions.
- Evolution: propose adapter changes, run contract regression, and require review before admission.

## Current boundary

This document defines a target architecture. It does not claim that all external tools are connected. Each connector must be implemented and tested individually. ARC-X is not the root authority, and the registry must not become a source of self-authorization.

## Acceptance tests

- Invalid or stale manifest rejected.
- Capability absent from verified connectors is reported as unresolved.
- REGISTERED or CONNECTED connector is never treated as VERIFIED.
- Write capability excluded unless explicit policy permits it.
- Missing granted scope blocks route.
- Connector output cannot override policy.
- Replay, stale receipt, response digest mismatch, and wrong tool identity are rejected.
- Same pinned manifests and policy produce a deterministic route plan.
- End-to-end test proves a result's lineage from intent through invocation receipt to verified postcondition.
