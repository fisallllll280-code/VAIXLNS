# Agent Action-Control Assurance v1

**Record ID:** VX.AGENT.ACTION.ASSURANCE.001  
**Status:** PARTIAL — reference implementation CI passed; production integration is not proven  
**Canonical authority:** `project.genome::v1.0.0` / `Ω0_GENESIS_CORE`  
**Owner:** VAIXLNS  
**Execution reference:** [vaixlns-nexent-vx pull request #1](https://github.com/fisallllll280-code/vaixlns-nexent-vx/pull/1)  
**CI evidence:** [VX Agent Action Assurance run 37916624473](https://github.com/fisallllll280-code/vaixlns-nexent-vx/actions/runs/37916624473)

## Purpose

Provide a fail-closed reference boundary for assessing whether an AI agent action is tied to an approved task contract, a scoped and expiring permit, a current resource version, an independently verified plan, and independent evidence of the resulting effect.

This record registers a capability candidate. It does not promote the capability to production or claim universal security.

## State contract

```text
SPECIFIED → AUTHORIZED → VERIFIED_PLAN → EXECUTING
    → EFFECT_VERIFIED → CLOSED_VERIFIED

EXECUTING → PARTIAL_EFFECT → COMPENSATING → CLOSED_FAILED
Any unresolved or conflicting effect → RECOVERY_REQUIRED
```

`CLOSED_VERIFIED` requires a verified effect and retained evidence references. `ABORTED`, `REJECTED`, `EXPIRED`, `CONFLICT`, and `RECOVERY_REQUIRED` are not successful closures. Partial effects must not be labelled as success.

## Implemented reference controls

- Signed permit bound to contract, operation, principal, resource, resource version, action scope, and expiry.
- Trusted resource-version oracle queried again immediately before execution-ticket issuance.
- Independent signed receipts for plan verification, target-side audit, readback, and tripwire events.
- Allowlisted diff paths and target-audit/readback state-hash comparison.
- Idempotency key bound to contract and operation, plus contract-digest conflict detection.
- Hash-chained transition receipts.
- Deterministic randomized invariant checks over 5,000 transition sequences.
- Three targeted mutation canaries for permit expiry, scope escalation, and resource-version TOCTOU.

## Reproducible evidence

The feature-branch GitHub Actions run reported:
- 14 reference tests passed.
- 5,000 randomized transition sequences passed.
- 3 of 3 targeted mutations were killed.
- Schema parsing and Python compilation passed.

These results apply to the reference implementation and the pinned workflow run; they do not prove safety of a connected production target.

## Production blockers

The following remain open and prevent `VERIFIED` or production status:

1. Replace the in-memory idempotency registry with a durable, atomic, concurrency-safe store.
2. Integrate a real target adapter and atomic compare-and-swap/resource-version enforcement at the actuator.
3. Deploy target-side audit, independent readback, and tripwire services with isolated keys, trusted identities, complete coverage, and retention guarantees.
4. Add crash/restart, concurrent retry, replay, and compensation-failure tests.
5. Add formal state-model checking (for example TLA+) and broader mutation testing.
6. Complete independent security review and controlled staging evidence.

## Non-promotion rule

CI success is evidence for the tests run, not authority to declare production readiness. The capability remains `PARTIAL` until the listed blockers are closed and the promotion path is explicitly reviewed under VAIXLNS governance.
