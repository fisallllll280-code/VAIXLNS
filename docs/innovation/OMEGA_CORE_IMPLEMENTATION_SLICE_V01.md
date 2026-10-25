# Ω-Core Innovation Gates — first executable slice

Status: IMPLEMENTED IN ISOLATED BRANCH / CI NOT YET VERIFIED.

## Scope
This adds a standard-library reference implementation for Capability Registry gap analysis,
Ω-CGI input preparation, conservative Ω-RAC evidence fusion, and a governance eligibility gate.
It does **not** create a production service, signed permissions, attestations, an event bus,
persistence, automated repository changes, or broad four-system federation.

## Run tests
```sh
python -m unittest discover -s tests -p 'test_omega_core_innovation.py' -v
```

## Ownership and integration
Canonical owner: VAIXLNS. VX is the only governed execution mediator.
Existing innovation indices and original/derived lineage must remain untouched.
No implicit VLNS=NAXLNS or NEXNET=NEXENT identity mapping.
The existing Ω-RAC, registries, and test harness must be assessed before expansion.
Experiment permits are isolated only; production eligibility is NOT a signed permit.

## Design invariants
- verified subset of available
- gap categories do not conflate absent and unverified
- repeated evidence cannot increase independent roots
- unverified reports do not count as independent tests
- unknown dependencies are excluded
- tests and policy approval required for production eligibility
- safe fail-closed behavior on missing scope and unknown actions

## Unfinished before production
- graph-level circular lineage detection and correlated cross-root datasets
- real proof verification and cryptographic signatures / revocation
- policy-as-code provider, permissions, policy snapshots and audit log
- durable event outbox, replay, CAS, schema migration, telemetry
- full registry reconciliation / source-to-test evidence mapping
- security testing, G0, ordered T01–T15 suites and CI evidence
- user-approved merge and deployment
