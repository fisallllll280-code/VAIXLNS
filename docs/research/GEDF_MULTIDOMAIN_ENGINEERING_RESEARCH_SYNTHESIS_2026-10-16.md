# GEDF Research Synthesis — Computational Engineering and Research-to-Code (2026-10-16)

**Scope:** two completed Undermind deep searches, covering 268 multidisciplinary engineering papers and 214 research-to-code/formal-assurance papers. Summaries below are based on abstracts and metadata unless a full text is separately reviewed. These are literature findings, not validation of VAIXLNS itself.

## Executive conclusion

The literature does not support betting on one universal autonomous synthesizer. The stronger engineering pattern is a **pipeline of typed composition, independent verification/validation, uncertainty quantification, reproducible provenance, and evidence-gated execution**. Agentic systems can produce runnable code, but code execution and passing weak tests do not establish that an implementation faithfully reproduces a paper or that a simulation describes physical reality.

## Research-supported architecture

1. **Typed architecture graph:** model components, interfaces, units, assumptions, constraints, and guarantees as versioned graph objects. Use graph-based MDAO and composition patterns to explore architectures; retain alternatives and their provenance [Hel12, Gen19, Gra19].
2. **Hard constraints before optimization:** dimensional inconsistency, unsafe physical states, missing authority, licensing conflicts, and unbounded resource requests are gates—not penalties that a performance score can offset.
3. **Verification before validation:** verify code and numerical solution behavior separately from validating a model against independent observations. Manufactured solutions, mesh/step refinement, residual checks, and invariants test solver correctness; experiments and held-out observations address model validity [Roa02, Obe04, Roy11].
4. **Uncertainty is typed:** keep numerical error, input uncertainty, parameter uncertainty, stochastic variability, and model-form uncertainty separate. A converged solver may still solve the wrong model [Roy11, Rie20].
5. **Reproducible provenance:** pin inputs, code revision, dependency locks, solver/runtime, parameters, random seeds, environment, raw outputs, and verifier reports. AiiDA and in-toto provide established patterns for workflow provenance and software supply-chain attestations [Hub20, Tor19].
6. **Research-to-code semantic alignment:** compile paper claims into atomic requirements and link each requirement to source passages, implementation locations, tests, and counterexamples. Keep abstract-only evidence distinct from full-text review and executed reproduction [Sta25, Hu26e, Bau26c].
7. **Independent verification:** the implementer cannot be the only verifier. Strengthen test suites with mutation/adversarial tests and evaluate whether tests detect plausible wrong implementations, not only whether the happy path passes [Yu26b].
8. **Multi-agent coordination is conditional:** specialist roles can help on decomposable tasks, but additional agents can increase overhead or propagate errors. Measure the value of each specialist against a single-agent or non-agent baseline before scaling.

## Selected literature

- [Roy11] Roy & Oberkampf, *A comprehensive framework for verification, validation, and uncertainty quantification in scientific computing*, 2011. DOI: 10.1016/J.CMA.2011.03.016.
- [Obe04] Oberkampf, Trucano & Hirsch, *Verification, Validation, and Predictive Capability in Computational Engineering and Physics*, 2004. DOI: 10.1115/1.1767847.
- [Roa02] Roache, *Code Verification by the Method of Manufactured Solutions*, 2002. DOI: 10.1115/1.1436090.
- [Gra19] Gray et al., *OpenMDAO: an open-source framework for multidisciplinary design, analysis, and optimization*, 2019. DOI: 10.1007/s00158-019-02211-z.
- [Hub20] Huber et al., *AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and data provenance*, 2020. DOI: 10.1038/s41597-020-00638-4.
- [Tor19] Torres-Arias et al., *in-toto: Providing farm-to-table guarantees for bits and bytes*, 2019. Source link: https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias.
- [Sta25] Starace et al., *PaperBench: Evaluating AI's Ability to Replicate AI Research*, 2025. DOI: 10.48550/arXiv.2504.01848.
- [Hu26e] Hu et al., *SA-Bench: Evaluating Semantic Alignment in LLM-Based Paper Reproduction*, 2026. Source link: https://arxiv.org/abs/2608.24252.
- [Bau26c] Baumgärtner & Gurevych, *SciCoQA: Quality Assurance for Scientific Paper-Code Alignment*, 2026. DOI: 10.48550/arXiv.2601.12910.
- [Yu26b] Yu et al., *SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates on Test-based Benchmark*, 2026. DOI: 10.48550/arXiv.2603.00520.

## Benchmarks and measurable acceptance criteria

### Scientific computing
- Manufactured-solution or analytic-reference agreement where available.
- Step/mesh refinement and observed convergence order.
- Dimensional consistency and invariant violation rate.
- Error, conditioning, sensitivity, and uncertainty calibration.
- Out-of-domain detection and held-out experimental discrepancy.
- Reproducibility across repeated runs and supported hardware/software environments.

### Software and paper reproduction
- Claim-to-source traceability and citation correctness.
- Requirement-to-code and requirement-to-test coverage.
- Reproduction success on pinned repositories and environments.
- Mutation-test kill rate, false pass rate, regression escape rate.
- Independent verifier agreement and unresolved discrepancy count.
- Runtime, compute cost, and time-to-evidence.

### System synthesis
- Hard-constraint feasibility rate.
- Pareto hypervolume and expensive-evaluation count on shared benchmark problems.
- Integration conformance, failure isolation, replay success, and recovery correctness.
- Candidate novelty only after prior-art recall review and human adjudication.
- No automatic canonical promotion from scores, agent votes, or a green CI run alone.

PaperBench, SA-Bench, SciCoQA, SWE-Bench variants, and standard MDAO problems measure different things; no one benchmark is a sufficient proxy for a trustworthy engineering factory.

## Recommended implementation order for VAIXLNS

**M0 — Source truth:** retain pinned revisions, exact excerpts, citation IDs, source class, retrieval timestamp, and content digests; unresolved access remains explicit.

**M1 — Research capsule:** turn source material into atomic claims, assumptions, counterevidence, and falsifiable hypotheses. This is the narrow runtime bridge implemented in the GEDF Research Pipeline PR.

**M2 — VCRE contract:** bind each hypothesis to typed math/computation/software/physics contracts, units, validity domain, resource budgets, solver tolerances, invariants, and proof obligations.

**M3 — Candidate synthesis:** generate multiple candidates in isolated branches; preserve parents, alternatives, and negative results; rank only comparable objectives with explicit units and evidence states.

**M4 — Sandboxed execution:** add versioned adapters for tests, symbolic tools, numerical solvers, benchmarks, and engineering tools. Each adapter must declare capabilities, schema, permissions, timeout, idempotency, license, environment, and failure semantics.

**M5 — Independent falsification:** separate builder and verifier, include mutation/adversarial tests, replay from pinned inputs, and block on unresolved critical discrepancies.

**M6 — Governed adoption:** create a proposed Ω.000 delta with evidence receipts, source lineage, limitations, rollback plan, and reviewer decision. The factory must never write canonical records directly.

## Unresolved questions

- Which research/tool adapters are actually authorized and connected in the target environment?
- What benchmark suite best represents the user's first engineering domain and customer value?
- Which full texts must be retrieved to verify the most consequential claims?
- What are the baseline quality, latency, compute budget, and false-positive rates?
- What independent proof/checking tools and numerical solvers can be installed and legally used?

## Boundaries

This synthesis does not claim a new physical law, globally unprecedented invention, complete archive recovery, live provider connectivity, or production deployment. A novel system claim requires a documented prior-art search, a working prototype, independent tests, benchmark comparison, and review.
