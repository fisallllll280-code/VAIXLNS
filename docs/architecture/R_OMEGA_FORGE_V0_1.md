# R-Ω Forge — Evidence-First Engineering Engine v0.1

**Status:** PROPOSAL / IMPLEMENTATION SCAFFOLD — not a live multi-model agent or production orchestrator.
**Authority:** `project.genome::v1.0.0`; master index `Ω.000`.
**Integration scope:** VAIXLNS, VLNS, VX, NEXNET.
**Branch:** `feat/r-omega-forge-evidence-engine-20261015`.

## Purpose

R-Ω Forge is a proposed evidence-gated engineering loop that discovers what exists, recovers index views without modifying canonical sources, researches alternatives, compares model outputs under a common rubric, simulates changes in isolation, and only then prepares a human-reviewable integration proposal.

It builds on the existing `scripts/build_zero_loss_index.py`, `scripts/recover_zero_loss_index.py`, and `registry/federation/four-system-interface-registry.v1.json`. It must not duplicate or replace those authorities.

## Design principles

1. **Retrieve before inventing:** inspect pinned repository evidence and preserve original artifacts and lineage.
2. **Evidence over assertions:** each claim is bound to a source, revision, method, digest, timestamp, and verifier state.
3. **Proposal is not execution:** model-generated plans remain proposals until tests and independent review pass.
4. **Fail closed:** unknown identities, absent transports, missing receipts, and conflicting contracts block activation.
5. **Simulation before reality:** changes run against fixtures/sandboxes first; no production writes or network probes in the initial engine.
6. **Canonical immutability:** never write to `project.genome` or `Ω.000`; all outputs are derived artifacts.
7. **Human authority:** merges, secrets, external service activation, and production deployment require a separate human-approved gate.

## Engine pipeline

`R Retrieve → R Restore → Research → Design → Simulate → Verify → Integrate → Monitor`

- **Retrieve/Restore:** call existing index tools; inspect all five output artifacts, coverage gaps, unresolved ID ranges, duplicates and dangling references.
- **Research:** collect source-backed findings from official docs, papers, repository history, and benchmarks. Keep date, URL, quotation/provenance, applicability, and confidence separate.
- **Model comparison:** adapters implement a common interface; run identical tasks/rubrics on available models. Record model/version, prompt, input digest, output digest, latency, cost if actually measured, and evaluator. No hard-coded leaderboard or fabricated scores.
- **Design:** create multiple alternatives (conservative repair, compatible extension, clean-room prototype), each with assumptions, evidence, risks, cost and rollback.
- **Simulate:** evaluate contracts and failure scenarios against fixtures, including missing identity, wrong revision, malformed receipt, unavailable dependency, hash drift, and partial recovery.
- **Verify:** unit/property/contract tests, reproducibility checks, security review, independent receipt validation, and regression checks.
- **Integrate:** produce a patch/PR candidate only. Human approval required before merge; separate approval required for production.
- **Monitor:** track recovery coverage, verified interface edges, test pass ratio, unresolved proof debt, regressions, reproducibility, and cost/latency where measured.

## Operating modes

| Mode | Output | Gate |
|---|---|---|
| `DISCOVER` | source/repository inventory | pinned source revisions |
| `RESTORE` | derived index + coverage report | canonical hashes unchanged |
| `RESEARCH` | source-backed evidence cards | source and date recorded |
| `COMPARE` | common-rubric model comparison | identical task/rubric; no missing score imputation |
| `DESIGN` | ranked alternatives and ADR | assumptions and trade-offs explicit |
| `SIMULATE` | scenario outcomes | isolated fixtures only |
| `VERIFY` | tests + revision-bound receipt | independent validation |
| `INTEGRATE` | patch/PR proposal | human review |
| `MONITOR` | progress and proof-debt trend | provenance-backed measures |

## Evidence object

Minimum fields: `evidence_id`, `claim`, `source_uri_or_path`, `source_revision`, `method`, `observed_at`, `sha256`, `status`, `limitations`, `verifier`.

Recommended states: `PROPOSAL`, `SPECIFIED`, `PARTIAL`, `PENDING_VERIFICATION`, `VERIFIED`, `CONFLICT`, `BLOCKED`. Only a verifier may mark an evidence item verified; a model cannot self-attest its own result.

## Initial implementation in this branch

`tools/r_omega_forge.py` is a **read-only local preflight scaffold**. It validates the four-system registry, summarizes all six edges, optionally reads existing recovery outputs, calculates source digests, and writes a JSON report. It does not call LLM APIs, crawl the web, activate endpoints, edit canonical records, or claim live integration. Those require separately configured adapters, credentials, authorization, tests and review.

## Benchmark and research strategy

- Software engineering tasks: prefer fresh, independently verifiable issue sets; do not treat a single benchmark score as general intelligence. OpenAI's 2026 note says SWE-bench Verified is increasingly contaminated and recommends SWE-bench Pro for frontier coding evaluation: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
- Model comparison: use a fixed task set, blind/randomized outputs where feasible, repeated runs for stochastic tasks, explicit graders, held-out regression cases, and cost/latency measured from actual runs. See https://developers.openai.com/api/docs/guides/model-optimization
- Provenance: for built artifacts, consider GitHub artifact attestations and verify them before consuming outputs: https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations
- Research claims must include publication date, primary source, independent corroboration where practical, and a distinction between published result and our own replication.

## Progress metrics (definitions, not current results)

- **Index coverage:** recovered atomic records / eligible records discovered; report unknown denominator explicitly.
- **Unresolved proof debt:** count of claims or edges awaiting evidence, grouped by severity.
- **Interface readiness:** count of edges at each status out of six; never conflate specified with connected.
- **Reproducibility:** matching normalized artifact digests across repeated runs on identical pinned inputs.
- **Regression rate:** failed previously passing cases / previously passing cases rerun.
- **Research freshness:** age of source evidence and percentage of critical claims with current primary sources.
- **Model utility:** task success under a fixed rubric, with uncertainty and measured cost/latency; no synthetic score if runs were not performed.

## Acceptance gates

1. Existing index builder/recovery tests pass.
2. Registry validator rejects false `LIVE_VERIFIED` when transport is not configured.
3. Forge report is deterministic except explicitly time-varying metadata.
4. Canonical files remain byte-for-byte unchanged.
5. Every one of six edges is represented, including blocked/unknown edges.
6. Recovery gaps remain visible; `PASS_WITH_DECLARED_GAPS` is not full recovery.
7. No merge/deployment automation bypasses human approval.

## Known gaps

- No real model adapters or automatic external research connector in this scaffold.
- No live runtime endpoints are configured in the registry.
- No claim of full historical index recovery until item-level source coverage is established.
- The code has not been run in a checkout by this authoring action; CI and local execution must establish its status.
