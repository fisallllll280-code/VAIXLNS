# VAIXLNS Operational Completeness V1

## Objective

Move VAIXLNS from repository declarations to an evidence-producing operational surface.

## Implemented Plane

The first fully executable lane is the PAPER Treasury lane:

OBSERVE -> PROPOSE -> SIMULATE -> RISK_CHECK -> AUTHORIZE -> PAPER_EXECUTE -> RECONCILE -> PROVE

Implementation:

- treasury/paper_treasury.py — deterministic state machine.
- treasury/__main__.py — executable entrypoint.
- tests/test_paper_treasury.py — conformance tests.
- scripts/treasury_admission_probe.py — machine-readable admission proof.
- registry/treasury/TREASURY_SYSTEM_MANIFEST_V1.json — canonical machine manifest.
- .github/workflows/vaixlns-treasury-conformance.yml — push, pull-request, manual, and scheduled execution.

## Operational Contract

A transaction cannot move to execution unless:

1. the policy version matches,
2. the asset and wallets are permitted,
3. the amount is within policy,
4. the source has sufficient paper balance,
5. risk checks pass,
6. dual authorization is present when required.

Execution mutates only synthetic balances. The execution reference explicitly records real_value_moved=false.

## Evidence Contract

Each reconciled transaction contains:

- event identifier,
- policy version,
- input state hash,
- simulation result,
- risk result,
- authorization evidence,
- execution reference,
- reconciliation result,
- evidence hash.

The full evidence bundle also contains an event-stream hash and current state hash.

## Continuous Operation

The GitHub workflow is configured for recurring execution every 15 minutes in addition to push, pull-request, and manual triggers.

A scheduled workflow configuration is not itself proof of uninterrupted runtime. Operational proof is produced by successful workflow runs and their evidence artifacts.

## Next Expansion Boundary

The paper lane is the safe executable base for future controlled adapters. Any real-value adapter must be independently admitted and must preserve separation between observation, recommendation, authorization, signing, execution, and reconciliation.

Real financial movement remains disabled in this implementation.
