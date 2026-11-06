# Sovereign Meta-Kernel v1

Status: SPECIFIED + IMPLEMENTED IN REPOSITORY; NOT YET CI-VERIFIED.

## Purpose

The Meta-Kernel evaluates whether a proposed state transition satisfies a declared set of constitutional, authority, evidence, simulation, test, and rollback requirements. It is a policy decision function, not an execution engine.

## Decision contract

Input: a JSON-compatible transition package containing:

- `schema_version`
- `before`: entity ID, constitution digest, and lineage ID
- `change`: change ID, changed fields, requested actions, simulation proof, test proof, rollback plan reference
- `authority`: approval state, approver ID, and externally verified signature flag
- `evidence`: source reference, SHA-256 digest, and verification state
- `policy`: immutable fields, authorized approvers, evidence minimum, and proof requirements

Output: deterministic decision record with sorted error codes, input digest, and decision digest.

## Decisions

- `REJECTED`: one or more mandatory checks failed.
- `ELIGIBLE_FOR_SEPARATE_APPROVAL`: the package satisfies this evaluator's declared checks. This is not permission to execute or merge.

## Invariants

1. Entity identity, lineage, and constitution digest are immutable by default.
2. Self-promotion and privileged actions (canonical writes, production deploys, financial transfers, credential issuance) cannot be authorized by this evaluator.
3. Evidence must identify a source, carry a SHA-256-shaped digest, and be marked verified. The evaluator checks shape and declared status; it does not independently retrieve or authenticate the source.
4. Simulation and test evidence are required by default.
5. A rollback plan reference is required.
6. Decisions are deterministic for identical JSON inputs.

## Trust boundary and limitations

- `signature_verified` is an upstream assertion, not cryptographic verification performed here.
- The authorized-approver list is input policy, not a protected root of trust. Production deployments must load policy from an independently protected authority store.
- SHA-256 digests provide integrity references, not proof that the referenced claim is true.
- This module does not enforce OS sandboxing, network isolation, deployment permissions, or filesystem immutability.
- It does not mutate `project.genome`, change canonical status, deploy services, or execute requested actions.
- The decision digest is an integrity checksum, not a digital signature or tamper-proof append-only log.

## Required production extensions

1. Bind policy to a signed, versioned canonical policy bundle.
2. Verify signatures against pinned keys and revocation policy.
3. Resolve evidence references and validate provenance independently.
4. Persist decisions in append-only, externally anchored event storage.
5. Enforce privileged operations in a separate runtime authorization gateway.
6. Add mutation, replay, key-rotation, revocation, and adversarial test suites.
7. Connect ARC-X proof obligations and closed-workspace attestations without treating their manifests as OS enforcement.

## Example lifecycle

`PROPOSED -> EVIDENCE_COLLECTED -> SIMULATED -> TESTED -> POLICY_EVALUATED -> SEPARATE_AUTHORIZATION -> EXECUTION -> POSTCONDITION_VERIFIED`

Any failed mandatory stage transitions to `REJECTED` or `QUARANTINED`. No stage may silently promote itself to `VERIFIED`.
