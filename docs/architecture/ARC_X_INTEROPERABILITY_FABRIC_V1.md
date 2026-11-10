# ARC-X Interoperability Fabric v1

Status: PARTIAL implementation. Contract validation and deterministic route-candidate planning exist; cryptographic receipt verification, live invocation, sandbox enforcement, and production secret-manager integration are NOT_IMPLEMENTED by these files. CI evidence is required before promotion.

## Objective

Provide a shared contract for tools and services so ARC-X can discover declared capabilities, validate manifests, evaluate per-capability scopes, and produce route candidates with explicit capability gaps. A registry entry is not proof of a live connection.

## Connector contract

Every connector declaration must identify:

- stable tool ID, provider, adapter version, contract version, and policy version;
- lifecycle state: PROPOSED, REGISTERED, CONNECTED, VERIFIED, DISABLED, or QUARANTINED;
- typed capabilities, input/output schema references, risk class, and required scopes for each capability;
- granted scopes, policy-admission state, and credential-handling mode;
- pinned source/provenance and a full SHA-256 digest in `sha256:<64 lowercase hex>` form;
- for VERIFIED manifests, a verifier identity and full SHA-256 receipt digest.

The verifier receipt fields are references/claims. This module checks their shape, not their signature, truth, freshness, or revocation. A separate trusted verifier must do that before a connector is admitted.

## Capability lifecycle

PROPOSED -> CONTRACT_VALIDATED -> REGISTERED -> CONNECTIVITY_TESTED -> INDEPENDENTLY_VERIFIED -> POLICY_ADMITTED

Any failed or stale check transitions to QUARANTINED or DISABLED. REGISTERED does not mean CONNECTED; CONNECTED does not mean VERIFIED; VERIFIED does not itself grant write authority.

## Routing contract

A route candidate is emitted only if the manifest passes structural validation, state is VERIFIED, policy admission is explicitly true, and the capability's required scopes are a subset of the granted scopes. Write-capable routes remain unavailable by default. The `allow_write` flag only permits a candidate to be described; it does not grant authority or execute the operation.

The planner emits candidates and unresolved capabilities; it does not invoke connectors or grant execution authority.

## Secret boundary

Secret values must never be placed in manifests, source code, canonical files, test fixtures, route plans, or audit output. Manifests may carry a logical secret-manager reference only. `scripts/arcx_secret_boundary.py` validates a conservative reference syntax for an allowlisted scheme; it does not retrieve a secret, prove the referenced object exists, or authorize access. Runtime retrieval must use a trusted workload identity and an external secrets manager/KMS/HSM with least-privilege access, auditing, rotation, and revocation. Production keys must never be generated or printed by repository tests.

## Required interoperability invariants

1. Least privilege and per-capability scopes.
2. No unrestricted shell, arbitrary URL fetch, or generic tool passthrough.
3. Strict input/output schema validation, size limits, timeouts, idempotency keys, and bounded retries in the future invocation gateway.
4. Untrusted connector outputs cannot modify ARC-X policy or system instructions.
5. Every result binds to tool ID, adapter version, policy version, request digest, response digest, timestamp, and evidence references.
6. Missing provenance, stale verification, schema mismatch, permission mismatch, or invalid receipt fails closed.
7. Secret values never enter evidence envelopes or audit reports.
8. Side-effecting operations require a separate authorization decision.
9. Human approval and provider/workspace permissions remain authoritative.
10. Tool failures and unavailable capabilities are explicit; no fabricated success or inferred connectivity.

## Integration layers

- Discovery: list connectors and declared capabilities.
- Contract: validate schemas and compatibility.
- Trust: verify source, identity, signatures, freshness, and revocation.
- Policy: evaluate scope, risk, approval, and environment.
- Routing: choose eligible capability providers and preserve fallback gaps.
- Invocation gateway: execute only typed, authorized calls (not implemented by this contract validator).
- Evidence: normalize receipts and preserve provenance.
- Reconciliation: compare requested outcome to observed postconditions.
- Evolution: propose adapter changes, run contract regression, and require review before admission.

## Current boundary

This is a bounded contract layer, not a universal connector runtime. It does not claim that all external tools are connected. It does not verify cryptographic signatures or connector health by itself. Each connector must be implemented and tested individually. ARC-X is not the root authority, and the registry must not become a source of self-authorization.

## Acceptance tests

- Invalid schema and malformed SHA-256 digests are rejected.
- Capability absent from verified connectors is reported as unresolved.
- REGISTERED or CONNECTED connector is never treated as VERIFIED.
- A VERIFIED label without a verifier receipt reference is rejected.
- Missing required scope blocks a route.
- Write capability excluded by default; explicit candidate flag does not grant authority.
- Secret references reject unapproved schemes, inline credentials, and path traversal.
- Connector output cannot override policy.
- Replay, stale receipt, response digest mismatch, and wrong tool identity must be rejected by the future receipt verifier.
- Same pinned manifests and policy produce a deterministic route plan.
- End-to-end integration proves lineage from intent through invocation receipt to verified postcondition.
