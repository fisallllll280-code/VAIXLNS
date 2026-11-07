# VX Ω Genesis — Sovereign Knowledge-to-Innovation Engine
Status: PROPOSED / NOT IMPLEMENTED / NOT VERIFIED
Date: 2026-10-25
Authority: VAIXLNS; orchestration: VX; research adapter: NEXENT subject to verified contracts.

## Purpose
Unify existing recovery, indexing, agent orchestration, scientific research, simulation, engineering and proof gates. No fifth sovereign system and no duplicate runtime.

## Source anchors (verify exact identity and revision before implementation)
- docs/indexes/INNOVATION_MASTER_INDEX.md
- docs/indexes/REPOSITORY_PERPETUAL_ENGINE_V1.md
- docs/indexes/ENGINEERING_DECISION_REGISTER.md
- docs/indexes/README.md
- docs/architecture/VAIXLNS_SYSTEM_CONTEXT_CLOSURE_V1.md
- docs/integration/ARC_X_FEDERATED_ENGINEERING_RUNTIME_BRIDGE_V1.md
- scripts/arcx_vx_bridge.py
- registry/innovation-operation-index.v1.json

## Mandatory pipeline
Source inventory -> immutable provenance -> identity reconciliation -> capability gap -> causal impact graph -> independent alternatives -> simulation -> test/assurance -> VX decision -> isolated patch -> human review -> approved release -> evidence-linked index update.

## Core contracts
Each proposal: proposal_id, origin_path, origin_commit, original_or_derived, source_sha256, normalized_digest, historical_ids, claim, assumptions, dependencies, risk, alternatives, test_plan, evidence_refs, reviewer, decision, status.
Statuses must remain separate: RECOVERED, CANONICAL, PROPOSED, IMPLEMENTED, VERIFIED. Evidence sufficiency, permission, confidence, and execution disposition are orthogonal fields.
A proposed result must never silently promote to VERIFIED.

## Gates
G0: repo baseline, access, protected-file hashes, isolated environment, CI credentials readiness; HOLD on any uncertainty.
G1: bounded inventory and provenance, including NOT_OBSERVED vs MISSING.
G2: no duplicate identity or authority, VX sole execution bridge.
G3: provider adapters with least privilege and zero SAR spend.
G4: reproducible baseline, simulation, counterfactuals and benchmarks.
G5: independent evidence review; fail closed on contradictory or dependent evidence.
G6: release approval, CI and change-control. Never merge/publish automatically.

## Ordered VX test sequence
T01–T05 -> T06–T10 -> T15 -> T11–T14; record exact test command, repository, commit, environment, logs, artifacts and reviewer. No tests are claimed executed by this proposal.

## Phased implementation
P0: reconcile existing source files and index identities; produce dependency/test map.
P1: read-only provenance graph, gap discovery and full-text search.
P2: causal impact analyzer with false-positive/false-negative evaluation.
P3: provider-neutral multi-mind router, bounded concurrency, isolation, cost ceiling 0 SAR.
P4: hypothesis forge and scientific/engineering simulation; deterministic seeds and independent replay.
P5: isolated patch generator, repair candidates, test selection and evidence receipts.
P6: controlled evolution proposals, human approval, immutable audit trail and recovery drill.

## Acceptance metrics (targets, not results)
100% of admitted changes have traceable source+commit+evidence; 0 protected-file mutations; 0 unauthorized merges/releases; 0 unapproved external spend. Benchmark 10x speed as hypothesis only, with throughput, p95 latency, recall, accuracy and zero-loss regression controls.

## Constraints
Do not edit project.genome or Ω.000. Do not auto-merge, publish, spend, or turn a draft into canonical policy. Historical index 0001–2750 is not presumed fully recovered. Existing scripts and contracts must be reused before any new component is added.
