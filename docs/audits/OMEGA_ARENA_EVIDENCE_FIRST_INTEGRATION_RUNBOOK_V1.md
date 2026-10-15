# Ω-Arena Evidence-First Integration Runbook v1

Status: SPECIFIED — execution evidence required before any VERIFIED claim.
Scope: VAIXLNS, VLNS, VX, NEXNET.
Base: main after PR #122. This branch is isolated; no merge or production activation is authorized.

## 1. Mission

Turn the existing Zero-Loss Index Recovery and four-system interface registry into a repeatable, evidence-producing audit workflow. Preserve all source artifacts and lineage. Never equate a repository name, manifest entry, passing CI fixture, or declared endpoint with a live system.

## 2. Canonical invariants

- `project.genome::v1.0.0` remains the canonical source.
- `Ω.000` remains the master index; do not rewrite or promote canonical records in this workflow.
- Recovery outputs and receipts are derived artifacts, separate from canonical sources.
- Each evidence item binds to repository, commit SHA, command, timestamp, exit code, and artifact digest.
- Unknown identity, absent endpoint, missing credentials, and incomplete extraction remain explicit blockers.
- No production writes, external probes, secret discovery, merges, or deployments are performed by this audit.

## 3. Execution sequence

### A — Pin and inspect
1. Record repository URL, base/head commit SHAs, working tree status, Python version, and available dependencies.
2. Confirm the required scripts, tests, canonical files, and registry files exist at the pinned revision.
3. Hash `project.genome` and `registry/omega/omega-000-master-index.json` before running any build.

### B — Recover the index
1. Run the existing zero-loss-index unit tests.
2. Run `python scripts/recover_zero_loss_index.py --root . --output-dir build/zero-loss-index`.
3. Preserve the full stdout/stderr and recovery receipt.
4. Verify the five expected artifacts and every SHA-256 listed in the receipt.
5. Inspect coverage for opaque sources, unresolved candidate ID ranges, missing IDs, duplicates, and dangling cross-references.
6. Re-hash canonical files and require exact equality with the pre-run hashes.

Acceptance: all commands exit successfully, all expected artifacts exist, hashes verify, canonical hashes are unchanged, and every remaining coverage gap is explicitly enumerated. A successful build with gaps is `PASS_WITH_DECLARED_GAPS`, never complete recovery.

### C — Reconcile identities and interfaces
For each of VAIXLNS, VLNS, VX, and NEXNET, capture:
- claimed system identity separately from repository identity;
- authoritative source for the mapping;
- pinned repository revision and versioned input/output contract;
- entrypoint/dependency/startup evidence, if available;
- endpoint source and authorization evidence, if explicitly configured;
- health/behavior test result, timeout/retry/idempotency policy;
- revision-bound receipt and independent verifier result.

Do not infer an endpoint. The current registry marks transports as `NOT_CONFIGURED`; absent explicit configuration, perform offline contract checks only.

### D — Six interface edges
Check all six edges declared in `registry/federation/four-system-interface-registry.v1.json`:
- VAIXLNS ↔ VLNS
- VAIXLNS ↔ VX
- VAIXLNS ↔ NEXNET
- VLNS ↔ VX
- VLNS ↔ NEXNET
- VX ↔ NEXNET

For each edge, emit one status: `LIVE_VERIFIED`, `SPECIFIED_NOT_CONNECTED`, `IDENTITY_UNVERIFIED`, `CONTRACT_PENDING`, `TEST_PENDING`, `BLOCKED`, or `CONFLICT`. `LIVE_VERIFIED` requires successful authorized behavior tests against the declared revision and an independently checked receipt; static JSON validation alone cannot satisfy it.

### E — Final report
Produce a machine-readable report and human-readable summary containing:
- source commit SHA and tool versions;
- before/after canonical SHA-256 values;
- test commands, exit codes, and evidence paths;
- recovery receipt and artifact digests;
- record counts, duplicates, dangling links, opaque sources, unresolved ID ranges;
- a six-edge status matrix;
- blockers, owner/action, and retest conditions;
- explicit non-claims: no live integration unless proved, no full historic recovery unless item-level coverage is complete, no production deployment.

## 4. Required negative tests

- Missing system identity cannot be admitted.
- Repository presence cannot imply a live endpoint.
- Invalid/mismatched schema digest blocks the edge.
- Evidence for a different commit cannot verify the current revision.
- Failed tests or absent receipts cannot yield `LIVE_VERIFIED`.
- Opaque source material is counted as pending, not silently dropped.
- Re-running against identical pinned inputs produces identical derived artifact content, excluding explicitly time-varying receipt metadata.
- Canonical source files remain byte-for-byte unchanged.

## 5. Stop conditions

Stop and report `BLOCKED` if a required script/file is missing, dependencies cannot be resolved, canonical hashes change, a receipt is malformed, expected artifacts are missing, or a test fails. Do not auto-repair canonical sources or weaken tests to obtain a pass.

## 6. Delivery status

This document defines the next execution gate; it is not itself execution evidence. Until the run is performed in a pinned checkout and receipts are reviewed, overall status remains `PENDING_VERIFICATION`.
