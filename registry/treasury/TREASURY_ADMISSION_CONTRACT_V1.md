# Treasury Admission Contract V1

A treasury or wallet adapter may enter VAIXLNS only when its behavior is explicit, bounded, testable, observable, and attributable.

## Mandatory Gates

- Identity
- Contract
- Source
- Build
- Execution
- Tests
- Security
- Performance
- Provenance
- Recovery
- Evidence
- Financial authorization boundary

## Required Failure Behavior

Any missing authorization, stale state, failed reconciliation, policy violation, anomalous transaction, or unverifiable execution must prevent or halt the affected action.

## Separation of Duties

Observation, recommendation, authorization, signing, execution, and reconciliation are separate capabilities.

No single autonomous component may silently combine all authority for real-value movement.

## Statuses

PROPOSED -> SIMULATED -> TESTED -> VERIFIED -> AUTHORIZED -> CONTROLLED -> PRODUCTION

Any regression can demote a component to QUARANTINED or BLOCKED.
