# VAIXLNS Language Repair Engineering Fabric v1

## Objective

Create a family of specialist "repair programmers" for the languages used across VAIXLNS and its federated repositories. Each specialist must be grounded in an explicit language/toolchain adapter, pinned source revision, captured diagnostics, reproducible tests, and independent review. The fabric coordinates specialists; it does not pretend one generic agent understands every language or every custom VAIXLNS language.

## Current executable scope

`tools/language_repair_fabric.py` converts recognized compiler/linter/test output into deterministic repair work orders. Initial diagnostic formats include selected Python, Rust, TypeScript, JavaScript, Go, C/C++, and Java diagnostics.

The engine:
- pins each work order to a repository identifier and immutable-looking revision SHA;
- retains a digest of the raw diagnostic line/output;
- emits deterministic work-order IDs;
- explicitly blocks unknown/custom languages until an adapter exists;
- marks all outputs `NOT_VERIFIED`;
- never edits files, executes compiler commands, installs dependencies, calls models, or creates patches.

A parser recognizing a diagnostic is not a proof that the parser is complete or that the suggested fix is correct.

## Specialist roles to cultivate

1. **Language Maintainer** — owns grammar/toolchain adapter, versions, and compatibility fixtures.
2. **Diagnostic Analyst** — reproduces failures and separates root cause from cascading errors.
3. **Repair Proposer** — proposes the smallest patch with a rationale and affected invariants.
4. **Test Engineer** — adds a failing regression test before the patch and runs targeted plus relevant full suites.
5. **Adversarial Reviewer** — searches for regressions, security effects, hidden behavior changes, and overfitting.
6. **Evidence Steward** — binds source revision, tool versions, commands, outputs, patch digest, and review receipt.
7. **Integration Architect** — checks cross-language/API/schema compatibility and preserves system identity.

The same agent must not be the sole author, verifier, and approver of a repair.

## Required repair protocol

```text
PIN SOURCE REVISION
  -> CAPTURE TOOLCHAIN + RAW DIAGNOSTICS
  -> PARSE THROUGH VERSIONED LANGUAGE ADAPTER
  -> CLUSTER DUPLICATES / TRACE DEPENDENCIES
  -> FORM ROOT-CAUSE HYPOTHESES WITH CONFIDENCE + COUNTEREVIDENCE
  -> CREATE MINIMAL PATCH PROPOSAL
  -> APPLY ONLY IN A SANDBOX AFTER EXPLICIT AUTHORIZATION
  -> RUN FAILING TEST FIRST, THEN TARGETED REGRESSION, THEN RELEVANT FULL SUITE
  -> RUN SECURITY / COMPATIBILITY / PERFORMANCE GUARDS AS APPLICABLE
  -> INDEPENDENT REVIEW AND REPRODUCTION
  -> ISSUE EVIDENCE RECEIPT
  -> PROPOSE, NEVER AUTOMATICALLY PERFORM, CANONICAL PROMOTION
```

## Adapter contract for system-specific languages

A custom language is not treated as Python/Rust/TypeScript by analogy. Before triage can become actionable, its adapter must specify:
- language ID and version/grammar revision;
- source file identity and encoding;
- diagnostic grammar with positive and negative fixtures;
- compiler/interpreter invocation contract (not executed by this v1);
- source-location normalization;
- deterministic parser tests;
- known unsupported cases and confidence limits;
- compatible test runner and reproduction procedure.

Custom-language output is preserved as a hashed evidence item and held in `BLOCKED_UNKNOWN_LANGUAGE` until the adapter is registered and tested.

## Safety and authority

- No arbitrary shell or network execution.
- No automatic edits, commits, merges, deployments, or canonical writes.
- Repository write permissions are outside this module.
- No source or idea is deleted as part of diagnosis or deduplication.
- `VERIFIED` is forbidden without an independent reproducible evidence chain.
- Canonical authority remains `project.genome::v1.0.0`, `Ω0_GENESIS_CORE`, and `Ω.000`.

## Roadmap

1. Add schema validation for every emitted work order and fixtures per language/tool version.
2. Inventory the actual languages and DSLs present in pinned VAIXLNS/VLNS/VX/NEXNET revisions before claiming coverage.
3. Add read-only CI artifact ingestion and test-result correlation.
4. Add sandboxed patch execution behind explicit capability grants and resource limits.
5. Add independent test/review agents with a cross-check matrix and adversarial mutation tests.
6. Measure precision, recall, false-fix rate, regression rate, and mean time to verified repair.
7. Add distributed worker queues only after load, durability, and consistency tests justify them.

## Status

SPECIFIED + initial diagnostic triage implementation. Focused tests must pass on the exact PR head. This is not yet an autonomous self-repair system, a full language implementation, or a production deployment.
