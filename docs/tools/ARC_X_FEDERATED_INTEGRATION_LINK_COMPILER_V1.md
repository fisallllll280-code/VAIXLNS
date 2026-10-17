# ARC-X Ω — Federated Integration & Link Compiler v1

**Status:** PROPOSAL  
**Authority:** `project.genome::v1.0.0` (authority must be verified by the canonical governance process)  
**Owner:** VAIXLNS  
**Implementation boundary:** analysis and plan generation only; no implicit writes, remote calls, execution, identity reassignment, or canonical admission.

## Purpose

ARC-X is both a reconstruction compiler and an integration/link compiler. It discovers declared systems and adapters, models interfaces and dependencies, checks compatibility, and emits a provenance-bearing integration plan with explicit proof obligations.

## Federation invariants

1. Repository identity is not system identity.
2. Similar names do not prove identity equivalence. In particular, `VLNS ↔ NAXLNS` and `NEXNET ↔ NEXENT` remain unresolved until independent identity evidence is admitted.
3. Every link is typed: `DATA`, `API`, `EVENT`, `BUILD`, `VERIFICATION`, `EXECUTION_REQUEST`, or `HUMAN_WORKFLOW`.
4. A discovered endpoint is not a validated contract; a valid contract is not authorization; a successful request is not proof of execution correctness.
5. ARC-X can propose links and test plans. It cannot authorize itself, execute production actions, modify canonical identity, or mark a link VERIFIED.
6. Unknown or conflicting interface evidence fails closed to `BLOCKED` or `PENDING_VERIFICATION`.

## Canonical data path

```text
Repository snapshots / registries / API schemas / runtime receipts
                         |
                         v
              Source fingerprints + provenance
                         |
                         v
               ARC-X EIR / identity graph
                         |
                         v
         Link discovery -> contract comparison
                         |
                         v
       compatibility matrix + proof obligations
                         |
                         v
          isolated contract/integration tests
                         |
                         v
         reviewable integration plan + receipt
                         |
             human/authorized admission gate
                         |
                         v
                 governed adapter execution
```

## Required link record

Each candidate link should identify: `link_id`, source and target system IDs, repository and immutable revision references, interface type, contract/schema digest, direction, data classification, authentication method (reference only; never secret values), trust boundary, capability requirements, compatibility findings, proof obligations, verification state, owner, and rollback strategy.

## Compatibility rules

- Compare schemas and protocol versions before generating an adapter.
- Check required/optional fields, types, units, error semantics, idempotency, timeout/retry policy, authentication, authorization, provenance, and version negotiation.
- Never treat natural-language descriptions as machine-verified contracts.
- Keep provider outputs untrusted until validated by the receiving boundary.
- Require simulation/dry-run for execution-affecting integrations.
- Test negative cases: invalid signature, stale revision, replay, duplicate request, schema drift, timeout, partial response, unauthorized capability, and unavailable verifier.
- Preserve independent verification. The producer cannot be the sole verifier of its own output.

## Initial federation roles (declared, not runtime-discovered)

- **VAIXLNS:** canonical governance, registry, provenance and admission boundaries.
- **VX:** governed execution and runtime observation.
- **VV:** independent verification boundary.
- **NEXENT:** discovery/research candidate plane.
- **VLNS / NAXLNS:** identity mapping unresolved pending evidence.
- **NEXNET / NEXENT:** distinct names; equivalence unresolved pending evidence.

The role list is an architectural starting point, not proof that live network links exist.

## State machine

`DISCOVERED -> CONTRACT_PENDING -> COMPATIBLE_PENDING_TEST -> TESTED_PENDING_REVIEW -> AUTHORIZED -> ACTIVE`

Any stage may transition to `BLOCKED` on contradiction, missing provenance, invalid authentication, failed test, revoked authority, or stale revision. Only the governance/authorization layer can admit an integration; ARC-X records evidence but does not self-promote states.

## Acceptance criteria

1. Same input manifest produces the same normalized plan digest.
2. Each proposed edge traces to source records and immutable digests.
3. Ambiguous identity mappings never auto-merge.
4. Incompatible contracts produce actionable blockers rather than guessed transformations.
5. Secret values are never serialized into plans or receipts.
6. No network request or execution occurs during discovery/planning.
7. A plan is explicitly marked `PROPOSAL` / `PENDING_VERIFICATION` until independently tested and authorized.
