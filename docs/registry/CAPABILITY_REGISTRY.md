# VAIXLNS Ω∞ — Capability Registry

Capabilities are not identical to repositories. All entries are unverified *execution-wise* until code, tests and runtime evidence have been reviewed.

## Gate states
SPEC_ONLY -> CONTRACTED -> IMPLEMENTED -> UNIT_TESTED -> INTEGRATION_TESTED -> RUNTIME_VERIFIED -> REPLAY_VERIFIED -> CANONICAL -> COMMERCIAL_READY -> REVENUE_VERIFIED.

Canonical status also requires explicitly recorded governance authorization. Commercial states apply only when relevant.

```yaml
capability_id: CAP-0001
name: Canonical source and lineage registry
domain: recovery
spec_location: docs/registry/SOURCE_REGISTRY.md
implementation_location: null
tests: []
runtime_evidence: []
dependencies: []
risks: [GAP-0001, GAP-0002]
current_state: SPEC_ONLY
next_required_evidence: Reproducible source extractor plus verification tests.
```

| ID | Capability | Related source(s) | Evidence-based state | Next evidence |
|---|---|---|---|---|
| CAP-0001 | Source / lineage registry | SRC-0001 | SPEC_ONLY | Extractor + integrity check |
| CAP-0002 | Canonical identity and ownership resolution | SRC-0001, SRC-0002, SRC-0003 | SPEC_ONLY | Contract map + ADR |
| CAP-0003 | VX deterministic execution conformance | SRC-0005 | SPEC_ONLY | Code/path review, tests, replay |
| CAP-0004 | NEXENT architecture search integration | SRC-0006, SRC-0007 | SPEC_ONLY | Adapter contract + integration test |
| CAP-0005 | Cross-repository verification gate | SRC-0001, SRC-0002 | SPEC_ONLY | CI logs at pinned SHAs |
| CAP-0006 | Agent lifecycle / swarm governance | SRC-0011, SRC-0012 | SPEC_ONLY | Authority + sandbox tests |
| CAP-0007 | Operational readiness and recovery | SRC-0001, SRC-0005 | SPEC_ONLY | Failure/recovery/replay test |

Note: SPEC_ONLY here denotes **not verified by this registry-bootstrap review**, not a determination that a linked repository lacks implementation.

## Minimum evidence to promote
Record: commit SHA, commands, exit codes, CI run URLs, test outputs, environment fingerprint, verifier, contract version, scope, approval and regression risks.
Do not infer CANONICAL from green CI alone.
