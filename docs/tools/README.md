# VAIXLNS Tools

This directory contains canonical tool specifications. Tool specifications are contracts and evidence boundaries; they are not implementation claims.

## ARC-X Ω

ARC-X is the Epistemic Reality Compiler: the repository/evidence reconstruction and architecture-compilation boundary of VAIXLNS.

- [Canonical ARC-X Specification](ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md)
- [ARC-X Runtime Bootstrap and CLI](ARC_X_RUNTIME_BOOTSTRAP_V1.md)
- Registry record: `../../registry/tools/arc-x.yaml`

### Current evidence state

- Canonical owner: VAIXLNS
- Specification: SPECIFIED
- Runtime implementation: PARTIAL (bootstrap merged into feat/windows-engineering-fabric-v1)
- Regression-test execution: PASS (6/6; run 37913717309)
- Integrity/replay conformance: PASS (run 37913717309)
- Semantic correctness: NOT CLAIMED
- Production implementation: NOT PROVEN
- Self-authority: prohibited

ARC-X composes existing recovery, registry, NEXENT, VV, VX, evidence, replay, and governance surfaces without replacing their authority boundaries.


## VA Genesis Operational Engine

- [Operational Engine v1](VA_GENESIS_OPERATIONAL_ENGINE_V1.md)
- Implementation prototype: `../../va/`
- Registry record: `../../registry/tools/va-genesis.yaml`
- Contract tests: `../../tests/test_va_genesis.py`

Current state: IMPLEMENTED-PROTOTYPE / PARTIAL. Static structural verification does not imply runtime verification or production admission.
