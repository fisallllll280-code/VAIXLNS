# ARC-X Reality Sovereignty Kernel v1

Status: IMPLEMENTED AS A DETERMINISTIC CONTRACT/CANDIDATE LAYER; NOT YET VERIFIED BY CI OR AN INDEPENDENT TRUST ROOT.

## Architectural position

VAIXLNS Canon remains the canonical authority. The Reality Sovereignty Kernel models claims and their scopes; ARC-X evaluates evidence and contradictions; VX may execute only a separately authorized and enforced transition; XV may propose hypotheses and plans but cannot self-authorize. This module does not replace the Canon, grant itself authority, or define external reality by assertion.

## Reality separation

A Reality Object is bound to an ontology ID/version/digest, a typed proposition, a reality layer, an observation scope, a temporal interval, and evidence envelopes. The layers are intentionally distinct:

1. EXTERNAL_REALITY — proposition about the world, never established by this module alone.
2. OBSERVED_STATE — what a declared observer reported within a specific scope.
3. BELIEVED_STATE — a model or agent belief.
4. AUTHORIZED_STATE — what policy/authority permits.
5. EXECUTED_STATE — what a runtime reports occurred.

A proposed, authorized, or believed transition must not be rewritten as an observed outcome. An execution receipt is not identical to a postcondition check.

## Epistemic states

The evaluator may return INVALID, UNKNOWN, SUPPORTED, CONTRADICTED, CONFLICTING_EVIDENCE, or STALE. SUPPORTED is not VERIFIED. Verification requires a trusted external verifier that authenticates receipt signatures, signer identity, trust roots, revocation, temporal validity, and artifact/scope binding. Receipt references in this module are shape-checked only.

UNKNOWN means the supplied record contains no admissible evidence envelope. It does not mean the proposition is false or absent.

## Bounded proof of ignorance

PROVABLY_UNKNOWN_WITHIN_SCOPE is emitted only when:
- the search/verification universe is explicitly enumerated and marked closed;
- the universe digest commits to the exact scope and unique path IDs;
- a closure-authority reference is provided;
- observations cover every declared path exactly once;
- every path has the same declared scope, a valid receipt digest, and outcome EXHAUSTED_NO_RESULT.

The result is conditional on the accuracy and trustworthiness of those declarations and receipt digests. The module does not authenticate signatures or prove that an omitted path is impossible. This is not a global claim that no knowledge exists anywhere.

## Ontological firewall

Ontology contracts are versioned and digested. Immutable concepts and constitutional terms, including USER, FILE, DELETE, AUTHORIZE, VERIFY, SAFE, and ARCHIVE, are guarded when present. A change to a guarded definition cannot be auto-accepted. A pair of structurally distinct approvals moves a candidate only to external authority verification; the approvals are not cryptographically verified here. Canonical writes are never performed by this module.

## Contradiction handling

Potential contradictions are only paired when subject and predicate match, observed scope matches, temporal scope matches, and canonical object values differ. The kernel preserves both claim IDs, the scope, and the temporal interval. It does not resolve semantic equivalence, source quality, or domain truth. A difference in scope or time is not silently treated as a contradiction.

## Transition proof boundary

The transition evaluator checks required digests, invariant result declarations, simulation/test receipt references, rollback plan reference, and authority ticket reference. It returns at most ELIGIBLE_FOR_SEPARATE_AUTHORITY_CHECK. A PASS value and receipt digest are inputs, not authenticated proofs. The function never grants authority, executes code, changes a canonical record, or claims the deployed runtime enforces these checks.

## Audit continuity

The audit chain uses canonical JSON and SHA-256 chaining and refuses common secret-value field names. It detects edits relative to the supplied chain but is not a digital signature, append-only store, trusted timestamp, or tamper-proof remote witness. For production, export events to an independently controlled append-only system and sign receipts under a protected key held outside this repository.

## Integration architecture

- Ω.000 / VAIXLNS Canon: canonical identity, authority references, schema/version registry.
- Ω∞ Reality Sovereignty: reality objects, ontology contracts, temporal/scope separation, bounded ignorance.
- ARC-X Evidence Core: evidence admission, receipt authentication, provenance independence, contradiction handling.
- VX Transition Gate: executes only against separately enforced policy and verified receipts.
- XV Intelligence: proposes claims, tests, and plans; proposal is not authority.
- Independent Witness Plane: externally held trust roots, signature/revocation checks, timestamps, immutable event retention.

## Explicit non-goals and limitations

This is not a truth oracle. It does not query all repositories, external services, or models. It does not independently authenticate evidence receipts, establish that a verification universe is truly exhaustive, prove semantic equivalence, or ensure that another process cannot bypass its checks. It contains no secrets and performs no network calls, tool invocation, canonical mutation, or production deployment.

## Acceptance criteria

- A missing evidence record produces UNKNOWN, not “absent”.
- Support and counterevidence remain visible as CONFLICTING_EVIDENCE.
- Constitutional ontology changes cannot be marked approved by this module.
- PROVABLY_UNKNOWN_WITHIN_SCOPE requires complete and digest-bound path coverage.
- Contradictions do not cross observation or temporal scopes.
- Transition evaluation always returns authority_granted=false and execution_performed=false.
- Hash-linked audit entries detect tampering and reject events that include secret value fields.
- External verification and runtime enforcement remain explicit dependencies, not implied achievements.
