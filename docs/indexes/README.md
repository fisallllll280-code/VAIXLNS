# VAIXLNS — Master Index Navigation

**Snapshot:** 2026-09-25

## Ground-truth rules

1. Historical material is preserved; similar names are not silently deleted.
2. `RECOVERED`, `CANONICAL`, `PROPOSED`, `IMPLEMENTED`, and `VERIFIED` are distinct states.
3. The project corpus describes a historical Master Index spanning approximately `0001–2750` across `40+` families, but the current corpus does not expose every legacy row item-by-item. This package therefore does not claim complete 2750-record extraction.

## Index set

- `MASTER_RECOVERY_STATUS.md` — current corpus and federation coverage.
- `ARCHIVE_SOURCE_INDEX.md` — supplied project sources, hashes, classifications.
- `INNOVATION_MASTER_INDEX.md` — innovation catalog with canonical placement.
- `../innovation/INNOVATION_OPERATION_INDEX.md` — generated detailed innovation descriptions, operation steps, inputs/outputs, admission gates, failure modes, source lineage, and status disagreements.
- `../../registry/innovation-operation-index.v1.json` — machine-readable generated innovation operation index; regenerate with `python tools/build_innovation_operation_index.py`.
- `REPOSITORY_FEDERATION_INDEX.md` — all 40 currently visible owned repositories and their role.
- `ENGINEERING_DECISION_REGISTER.md` — concise architecture rationale; not private chain-of-thought.
- `CANONICAL_REPOSITORY_LAYOUT.md` — target structure and ownership boundaries.
- `REPOSITORY_PERPETUAL_ENGINE_V1.md` — continuous repository creation, development, verification and innovation loop.

- `../architecture/VAIXLNS_SYSTEM_CONTEXT_CLOSURE_V1.md` — 2026-10-07 consolidated architecture context for index memory, VX cognitive federation, agent minds, Ω-Patterns, prediction/recovery, data/tools/developers, Ω-Arena, security, and treasury integration.
- ../architecture/VAIXLNS_SYSTEM_MEMORY_INDEX_AND_LANGUAGE_FABRIC_V1.md — governed system memory, source lineage, Ω.000 synchronization, historical preservation, and typed engineering-language processing.
- ../integration/ARC_X_FEDERATED_ENGINEERING_RUNTIME_BRIDGE_V1.md — ARC-X to VX engineering task routing for mathematics, numerical computing, software and physics simulation; remains SPECIFIED until runtime evidence closes the gates.
- ../../schemas/vaixlns-system-memory-record.schema.json — machine-readable provenance-preserving memory-record contract.
- ../../schemas/arcx-vx-engineering-task.schema.json — typed task envelope for controlled engineering compute.
- ../../scripts/arcx_vx_bridge.py — explicit fail-closed client for a configured VX engineering endpoint; receipt acknowledgement is not proof or admission.
- ../../tests/test_arcx_vx_bridge.py — unit tests for preflight, receipt validation, and endpoint safety (test execution remains to be verified).


- `../strategy/SAUDI_FIRST_INNOVATION_PROGRAM_V1.md` — Saudi-first engineering offers, founder-financed launch capital, sources-and-uses ledger, and 30-day reserve rule.
- `../../registry/capital_lock_policy.v1.json` — machine-readable proposed capital policy; not technically enforced until separately evidenced.
- `../../registry/saudi_innovation_launch.v1.json` — launch status, offer targets, partner-slot status, and acceptance gates.

- `../tools/LEGACY_ARCHIVE_RESEARCH_TOOLCHAIN_V1.md` — implemented archive extraction/search core, zero-loss provenance rules, exact-repeat reporting, similarity review, and JSONL export. Live adapters and full 0001–2750 recovery remain pending.

- VAIXLNS_ZERO_LOSS_INDEX_V1.md — unified 28-view zero-loss index contract, atomic record rules, and build/verify commands.
- ../../registry/indexes/zero-loss-index-taxonomy.v1.json — machine-readable definitions of all 28 index views and transition gates.
- The generated five-file export is built by scripts/build_zero_loss_index.py; a read-only GitHub Actions workflow verifies and uploads the artifact without silently rewriting canonical sources.

- [VAIXLNS Global Research System V1](../research/VAIXLNS_GLOBAL_RESEARCH_SYSTEM_V1.md) — provenance-first research architecture, evidence gates, source strategy, metrics and staged delivery.
