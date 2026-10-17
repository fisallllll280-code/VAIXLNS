# Ω Research & Comparison Fabric v1

**Status:** SPECIFIED  
**Owner:** VAIXLNS  
**Authority:** project.genome v1.0.0 / Ω0_GENESIS_CORE  
**Master-index policy:** supplementary projection only; do not rewrite Ω.000 automatically.

## Purpose

Provide one reproducible path from a research question to comparable evidence, engineering decisions, and traceable implementation tasks across mathematical, computational, physical, systems, and AI domains. This fabric organizes evidence; it does not declare a claim true merely because multiple models agree.

## Canonical boundaries

- `project.genome` remains the project identity source.
- `registry/omega/omega-000-master-index.json` remains the Ω.000 master index.
- This document, research records, comparison outputs, and generated indexes are subordinate artifacts.
- Preserve original sources and identifiers. Never silently replace, delete, or synthesize missing historical records.
- A research record cannot become VERIFIED without an inspectable source, a reproducible method, and a recorded verification result.
- SPECIFIED, IMPLEMENTED, VERIFIED, PARTIAL, MISSING, CONFLICT, and PROPOSAL are distinct states; documentation alone is not execution evidence.
- External model outputs are hypotheses until independently checked.

## Workflow

1. **Intake** — record question, domain, decision to inform, constraints, risk, and expected output.
2. **Freeze sources** — pin repository, commit/ref, document URL or DOI, version/date, and content hash where available.
3. **Decompose** — separate factual claims, mathematical assumptions, empirical hypotheses, implementation requirements, and value judgments.
4. **Retrieve** — search primary literature, official documentation, standards, repository history, and relevant benchmarks. Keep source provenance.
5. **Normalize** — represent each claim with units, definitions, scope, assumptions, uncertainty, and falsification conditions.
6. **Compare** — use an explicit baseline and common evaluation protocol. Do not compare incompatible units, workloads, sample sizes, or conditions as if equivalent.
7. **Challenge** — seek counterexamples, negative results, alternative explanations, dependency conflicts, and independent replications.
8. **Verify** — run executable tests, calculations, simulations, or reproductions when feasible. Record commands, environment, inputs, outputs, and limitations.
9. **Synthesize** — produce a decision matrix with evidence strength, uncertainty, costs, risks, and unresolved questions.
10. **Admit** — create implementation tasks only after acceptance criteria and ownership are explicit. Human approval is required for privileged changes, external publication, irreversible actions, or canonical-index changes.
11. **Monitor** — track whether downstream implementation outcomes support or contradict the research claim.

## Cross-domain comparison protocol

For every comparison, declare:
- research question and decision context;
- candidates and inclusion/exclusion criteria;
- baseline and version-pinned source set;
- metrics, units, measurement procedure, and expected variance;
- assumptions and environmental conditions;
- evidence independence and possible shared-source/correlation risks;
- reproducibility package (inputs, scripts, commands, seeds, environment);
- uncertainty, failure cases, and limits of generalization;
- result state and reviewer/authority.

A model leaderboard is not a substitute for a domain-specific benchmark. For physical claims, distinguish analytic derivation, simulation, laboratory measurement, and field observation. For mathematical claims, distinguish proof, proof sketch, conjecture, numerical evidence, and analogy. For computational claims, include complexity, resource consumption, correctness, and reproducibility.

## Research record lifecycle

`PROPOSED → SOURCES_PINNED → ANALYZED → CHALLENGED → REPRODUCED → REVIEWED → ADMITTED`

Records may instead transition to `PARTIAL`, `CONFLICT`, `REJECTED`, or `BLOCKED`. Never force a successful lifecycle state when evidence is absent. Revisions append a new version and preserve prior record hashes.

## Suggested repository layout

```text
research/
  README.md
  records/
    .gitkeep
  templates/
    research-record.template.json
  comparisons/
    README.md
  domains/
    mathematics.md
    computer-science.md
    physics.md
    systems-engineering.md
    ai-and-agents.md
  decisions/
    README.md
schemas/
  research-comparison-record.schema.json
scripts/
  validate_research_records.py
tests/
  test_research_record_validator.py
docs/innovation/
  OMEGA_RESEARCH_COMPARISON_FABRIC_V1.md
```

## Initial research lanes

1. **Index integrity and lineage:** stable IDs, duplicate detection, source hashes, provenance graphs, conflict preservation, and deterministic rebuilds.
2. **Formal methods:** state machines, invariants, property-based tests, model checking, proof obligations, and typed transition contracts.
3. **Distributed systems:** consensus boundaries, idempotency, retries, event ordering, partition behavior, and recovery.
4. **Mathematics and optimization:** formal derivations, sensitivity analysis, uncertainty propagation, robust and multi-objective optimization.
5. **Computational engineering:** algorithmic complexity, performance baselines, reproducible experiments, memory/CPU/GPU profiling.
6. **Physics and simulation:** dimensional analysis, model assumptions, numerical stability, uncertainty quantification, and experimental validation.
7. **AI systems:** capability-specific evaluation, independent cross-model review, prompt-injection resistance, tool authority, and evidence-grounded outputs.
8. **Security and governance:** threat models, least privilege, software supply chain, policy enforcement, auditability, and rollback testing.

## Acceptance gates

- [ ] Every record has a stable ID and source provenance.
- [ ] Every claim has an explicit epistemic status.
- [ ] Comparisons declare a baseline and comparable conditions.
- [ ] Reproduction instructions are present when the claim is reproducible.
- [ ] Missing evidence remains visible; no synthetic VERIFIED status.
- [ ] Historical source IDs and previous versions are retained.
- [ ] No automatic writes to `project.genome` or Ω.000.
- [ ] Canonical promotion requires a separate authorized review.

## Initial limitation

This fabric is a specification and repository scaffold. It does not itself connect live model providers, run physical experiments, validate every historical innovation, or prove the completeness of any index. Those require adapters, credentials, executable runs, source-specific work, and evidence artifacts.
