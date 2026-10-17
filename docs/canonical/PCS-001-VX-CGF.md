# VX-CGF / PCS-001 — Proof-Carrying State Canonical Invariant

Status: proposed canonical contract; not a claim of repository-wide enforcement until every state transition is wired to the validator and CI proves coverage.

## Names
- **VX-CGF**: VX Carrying-Governance Framework (the state-envelope and transition protocol).
- **PCS-001**: Proof-Carrying State, the minimal admissibility contract.
- **Canonical invariant**: No state may be designated LEGAL, VALIDATED, RELEASED, ACTIVE, or PROMOTED unless it carries sufficient evidence, reproducible execution material, independent verification, provenance, and an authorized promotion transition.

## One law
A state is admissible for a protected status if and only if all required proof obligations pass. Missing, stale, conflicting, unverifiable, or unauthorized proof means DENY. There is no implicit promotion and no fallback that weakens the rule.

## Required state envelope
Every state candidate MUST provide:
1. `state_id`, `state_type`, `schema_version`, and canonical content digest.
2. `evidence[]`: evidence identifiers, content digests, issuer, creation time, scope, and verification status.
3. `replay`: immutable input references/digests, algorithm/runtime version, deterministic configuration, and replay command or executable reference.
4. `verification[]`: verifier identity, verifier version, check result, timestamp, and evidence digest checked.
5. `provenance`: parent state(s), source repository/commit or source artifact digest, creator/producer, and derivation record.
6. `promotion`: from/to states, policy ID/digest, authorized principal, approval evidence, transition timestamp, and transition digest.
7. `validity`: expiry/freshness requirements and revocation status.

## Admission predicate
`ADMIT(s, p, t) = SCHEMA_OK ∧ DIGEST_OK ∧ EVIDENCE_SUFFICIENT ∧ REPLAYABLE ∧ VERIFICATION_PASSED ∧ PROVENANCE_COMPLETE ∧ PROMOTION_AUTHORIZED ∧ POLICY_ALLOWED ∧ FRESH(t) ∧ NOT_REVOKED`

If any predicate is false or unknown, return `DENY`. Unknown is not true.

## State machine
`DRAFT -> EVIDENCE_ATTACHED -> REPLAYABLE -> VERIFIED -> PROMOTION_REQUESTED -> PROMOTED`
Any stage may move to `REJECTED`; a material content change invalidates downstream evidence and returns the candidate to `DRAFT`. Revocation moves any promoted state to `REVOKED`. Only the authorized transition service may write `PROMOTED`.

## Failure semantics
- Missing evidence: `DENY_EVIDENCE_MISSING`
- Digest mismatch: `DENY_INTEGRITY_MISMATCH`
- Replay unavailable/non-deterministic without an explicit tolerance policy: `DENY_NOT_REPLAYABLE`
- Verification missing, failed, stale, or self-attested where independence is required: `DENY_VERIFICATION`
- Provenance chain incomplete: `DENY_PROVENANCE`
- Approval missing, revoked, wrong scope, or wrong policy digest: `DENY_PROMOTION_AUTHORITY`
- Expired or revoked proof: `DENY_STALE_OR_REVOKED`
- Schema or policy ambiguity: `DENY_UNKNOWN`

## Composition rule
Template Forge, Fast-Core, RIRF, Ω-RAC, FailureGenome, and other subsystems may keep domain-specific checks, but all state promotion passes through PCS-001. Domain-specific predicates can add restrictions; they cannot override or weaken PCS-001. The shared law governs admissibility, not domain algorithms.

## Security and operations
- Hashes prove integrity only when the referenced bytes are retrievable; hashes alone do not prove truth.
- Replay must run in a sandbox with explicit resource limits and no inherited secrets.
- Evidence issuers and approvers are authenticated and scope-bound.
- Record decisions append-only with policy digest and reason codes; redact secrets and sensitive payloads.
- Require independent verification for high-impact or externally visible promotion.
- Rollback is a new authorized transition, never silent history rewriting.

## Minimum acceptance tests
1. A state without evidence is denied.
2. A state with evidence but no replay material is denied.
3. Digest mismatch is denied.
4. Missing or failed verification is denied.
5. Missing parent/source provenance is denied.
6. Promotion without matching authorization and policy digest is denied.
7. Expired or revoked evidence is denied.
8. Valid complete proof can pass only when every policy check passes.
9. Any content mutation invalidates prior proof bindings.
10. Domain-specific systems cannot force promotion after a PCS-001 denial.

## Adoption sequence
1. Register this contract as the canonical candidate.
2. Implement the validator and adversarial tests.
3. Wire every protected-state writer and promotion API to the validator.
4. Add repository-wide CI checks and inventory all bypass paths.
5. Enable enforcement only after bypass coverage is proven; until then label status `PROPOSED` or `PARTIALLY_ENFORCED`, never `ENFORCED`.
