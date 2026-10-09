# VAIXLNS Tools

This directory contains canonical tool specifications. Tool specifications are contracts and evidence boundaries; they are not implementation claims.

## ARC-X Ω

ARC-X is the Epistemic Reality Compiler: the repository/evidence reconstruction and architecture-compilation boundary of VAIXLNS.

- [Canonical ARC-X Specification](ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md)
- Registry record: `../../registry/tools/arc-x.yaml`

### Current evidence state

- Canonical owner: VAIXLNS
- Specification: SPECIFIED
- Production implementation: NOT PROVEN
- Self-authority: prohibited

ARC-X composes existing recovery, registry, NEXENT, VV, VX, evidence, replay, and governance surfaces without replacing their authority boundaries.


## VA Genesis Operational Engine

- [Operational Engine v1](VA_GENESIS_OPERATIONAL_ENGINE_V1.md)
- Implementation prototype: `../../va/`
- Registry record: `../../registry/tools/va-genesis.yaml`
- Contract tests: `../../tests/test_va_genesis.py`

Current state: IMPLEMENTED-PROTOTYPE / PARTIAL. Static structural verification does not imply runtime verification or production admission.

## Agent Action-Control Assurance v1

- [Specification and implementation boundary](AGENT_ACTION_CONTROL_ASSURANCE_V1.md)
- Registry record: `../../registry/tools/agent-action-assurance.yaml`
- Reference implementation: [vaixlns-nexent-vx PR #1](https://github.com/fisallllll280-code/vaixlns-nexent-vx/pull/1)
- CI evidence: [VX Agent Action Assurance](https://github.com/fisallllll280-code/vaixlns-nexent-vx/actions/runs/37916624473)

Current state: **PARTIAL**. The feature-branch reference passed 14 tests, 5,000 randomized transition sequences, and three targeted mutation canaries. Production integration remains unproven. The in-memory idempotency store, target adapter, isolated audit/readback/tripwire services, concurrency tests, formal model checking, and independent security review remain blockers. Passing reference tests does not authorize a production or canonical promotion.

