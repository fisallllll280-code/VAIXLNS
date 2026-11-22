# VX MicroEvolution Engine Ω — Deep Innovation Portfolio

**Status:** IDEA CATALOG + DETERMINISTIC SCREENING IMPLEMENTATION; all ideas remain proposals.  
**Scope:** complements, rather than replaces, ARC-X Bounded Adaptive Evolution Planner, Ω Memory–Task–Innovation Kernel, innovation registry, and VX tool-control policy.

## Design principle

The goal is not to invent the largest number of ideas. It is to discover the smallest reversible experiment that can falsify a useful engineering hypothesis, produce independent evidence, and preserve future options. The five-year horizon is managed through scenarios, triggers, periodic re-evaluation, and longitudinal reports—not deterministic prediction.

## New portfolio engine

- `registry/vx-microevolution-ideas.v1.json`: 18 explicit hypotheses, each with a minimum experiment, measurable success metric, kill criteria, dependencies, horizon, multi-dimensional screening scores, and an unassessed novelty state.
- `scripts/vx_microevolution_ideas.py`: deterministic catalog evaluator, dependency validation, stable topological ordering, cycle/missing-dependency detection, digest binding, and explainable benefit/burden vectors.
- `tests/test_vx_microevolution_ideas.py`: checks that malformed, duplicate, cyclic, dependency-incomplete, or falsely novelty-claimed proposals fail closed.
- The existing scanner remains read-only and separate. The evaluator does not perform external research, execute experiments, approve proposals, or write canonical registries.

## Portfolio themes

1. **Proof before claims:** evidence graph, runtime reality diff, stale-evidence expiry, independent verifier rotation.
2. **Smallest useful experiment:** counterfactual micro-patch lab, reproducibility capsule, synthetic fault cases.
3. **Longitudinal resilience:** temporal architecture drift, dependency end-of-life, option value, five-year scenarios.
4. **Decision quality:** Pareto frontier, mutation blast radius, reviewer attention queue, semantic duplicate/conflict detection.
5. **Learning without unsafe autonomy:** failure lineage, capability/boundary genome, budgeted research loop with hard stopping rules.

## Operating model

```text
OBSERVE
  -> INVENTORY + HASH
  -> GENERATE HYPOTHESES
  -> CHECK DUPLICATES / DEPENDENCIES
  -> SCORE MULTIPLE DIMENSIONS
  -> SELECT A MINIMUM EXPERIMENT
  -> REPLAY BASELINE AND CANDIDATE
  -> INDEPENDENT VERIFICATION
  -> HUMAN / GOVERNED DECISION
  -> AUTHORIZED ADOPTION
  -> MONITOR OUTCOME AND ROLLBACK SIGNALS
  -> UPDATE LONGITUDINAL LEDGER
```

Each arrow is a gate, not a claim that the whole chain is already automated. The current portfolio evaluator implements catalog validation and screening only.

## Lifecycle and evidence rules

- `PROPOSED`: a hypothesis exists; no novelty or implementation claim.
- `RESEARCHING`: prior art, source claims, or dependencies are being investigated.
- `EXPERIMENT_READY`: baseline, environment, success metric, kill criteria, and rollback plan are specified.
- `EXPERIMENTED`: raw results are attached; not yet independently verified.
- `VERIFIED`: an independent verifier reproduced the defined result under the declared scope.
- `REJECTED`: preserve the reason and evidence; do not erase the lineage.
- `SUPERSEDED`: link to the successor and preserve why the older proposal was replaced.

Novelty stays `UNASSESSED` until documented prior-art research is performed. A high screening score is not a scientific claim. Simulation is not production proof. CI success is not evidence that an external service is live.

## Scoring discipline

The evaluator exposes benefit and burden vectors rather than hiding every trade-off in one number. Its `screening_delta` is a coarse triage aid only. Before decisions with material impact, use a calibrated measurement contract and Pareto analysis; keep uncertainty and evidence gaps visible. Never compare scores across domains until scales and data quality are justified.

## Five-year horizon

- **0–90 days:** validate evidence links, baseline/replay discipline, dependency inventories, and explicit kill criteria.
- **3–12 months:** add labelled drift history, verifier independence checks, stale-evidence policies, and repeatable benchmark fixtures.
- **Year 1–3:** introduce scenario triggers, runtime reality adapters, compatibility fixtures, and calibrated blast-radius estimates.
- **Year 3–5:** use accumulated outcomes to revise hypotheses, detect recurring failure patterns, and prioritize architecture options that lower migration cost.
- **Every cycle:** record assumptions, source revisions, owners, evidence timestamps, uncertainty, costs, and decision rationale. Keep reports in an explicitly managed archive; default CI artifact retention is not a five-year archive.

## Safety invariants

No self-granted authority; no automatic canonical promotion; no protected-branch merge; no production mutation; no external side effects from this evaluator; no fabricated runtime observations; no novelty claim without prior-art review; no irreversible action without separate policy, independent review, and explicit authorization. Budget exhaustion, missing evidence, unknown dependency, or verifier failure must stop the cycle and preserve the record.

## Run

```bash
python scripts/vx_microevolution_ideas.py --catalog registry/vx-microevolution-ideas.v1.json --output build/microevolution/idea-evaluation.json
python -m unittest tests.test_vx_microevolution_ideas -v
```
