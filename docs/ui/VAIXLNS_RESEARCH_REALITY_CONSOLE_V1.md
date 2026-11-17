# VAIXLNS Research-to-Reality Observatory V1

**State:** IMPLEMENTED AS A STATIC UI ARTIFACT ON AN ISOLATED FEATURE BRANCH  
**Canonical owner:** VAIXLNS  
**Feature branch:** `feat/research-reality-console-20261117`  
**Contract:** `.claude/contracts/RESEARCH_REALITY_CONSOLE_20261117.json`  
**Entry point:** `web/research-reality-console/index.html`  
**Status data:** `web/research-reality-console/research-status.json`

## 1. Purpose

The Observatory is a navigation and monitoring surface for the full VAIXLNS research-to-reality lifecycle. It is not another research engine, registry, knowledge graph, or authority plane. It projects the existing VAIXLNS Global Research System contract and a provenance-labelled Undermind workspace snapshot into one operator-facing view.

The architecture is deeper than paper search. Its nine architectural layers span semantic intent, constitutional authority, ontology/world models, epistemic evidence, mathematical/physical semantics, compiler and capability synthesis, bounded execution, reality reconciliation, and governed evolution. The 17-stage lifecycle spans:

1. Intent and falsifiable problem framing.
2. Source discovery and measurable coverage.
3. Ingestion, immutable provenance and content identity.
4. Semantic normalization and entity resolution.
5. Knowledge graph, typed relations and causal structure.
6. Contradiction, counterevidence and uncertainty.
7. Hypothesis construction and prior-art analysis.
8. Mathematical/physical formalization, units, invariants and dimensional checks.
9. Design-space exploration and capability synthesis.
10. Sandboxed simulation, multi-fidelity experiments and reproducibility.
11. Sensitivity, uncertainty and identifiability analysis.
12. Independent reproduction and verification.
13. Expected-versus-observed reality reconciliation.
14. Governance, authorization and safety gates.
15. Controlled integration with rollback.
16. Runtime observation, freshness and drift monitoring.
17. Causal memory and governed evolution.

## 2. Relationship to existing architecture

This UI is a read-only projection. It does not replace or create parallel versions of:

- `docs/research/VAIXLNS_GLOBAL_RESEARCH_SYSTEM_V1.md`
- `registry/research/global-research-system.v1.json`
- `Ω.000` or the Zero-Loss Index
- VX execution, ARC-X evidence/decision boundaries, or canonical governance.

The research pipeline and lifecycle states remain defined by the existing canonical research contract. This page visualizes them and links to research workspaces.

## 3. Current source snapshot

The refreshed JSON snapshot was collected through the explicitly selected Undermind account and workspace:

- Workspace: `VAIXLNS's workspace`
- Workspace ID: `0d9eabfb-e9d8-49fc-aab5-a0383a9110ce`
- Files: 149 at observation time
- Deep searches: 47 at observation time
- Active search in the latest snapshot:
  - `Foundations of Intent-to-Reality Computing and Governed State Evolution 2026`
- Two newly launched searches completed and are now listed under completed research context:
  - `Scientific Engine Ecosystem and VX Capability Acquisition 2026`
  - `From Scientific Hypothesis to Verified Engineering Reality`

The snapshot also links five relevant completed research threads: the two new engineering searches plus Scientific Discovery Software First; Computational Mathematics, Physics and Quantum Methods for VX Metrology; and Visual Systems Engineering / MBSE Digital Thread. The workspace also contains completed prior-art reviews on sovereign-system genesis, runtime attestation, collective intelligence and agent governance.

**Freshness warning:** these values are a point-in-time observation, not a live feed. The screen labels the source as a snapshot and does not imply that it can poll Undermind.

## 4. Data contract and refresh

`research-status.json` is intentionally separate from the HTML. It contains:
- schema version and observation timestamp;
- workspace identity and counts;
- provider connection state and explanation;
- active deep-search identifiers, states, URLs, scope and expected outputs;
- selected completed research context;
- the lifecycle projection;
- explicit assurance invariants.

To refresh the view, replace the JSON with a newly authorized snapshot generated through Undermind. The browser reads the local JSON file when served over HTTP and falls back to a clearly labelled embedded snapshot when opened directly from disk.

Do not put Undermind credentials, API keys, session cookies, or privileged provider endpoints in this page or its JSON. A future live adapter must be server-side, authenticated, least-privileged, rate-limited, auditable, and governed by the existing source-adapter and security contracts. Until such an adapter is implemented and independently verified, the provider state must remain `NOT_CONNECTED`.

## 5. UI boundaries

- The 17 lifecycle cards describe the system's intended stages; they are not stage-completion telemetry.
- The active-search cards reflect Undermind's last observed search states.
- The historical workspace counts are not current live metrics.
- The page does not launch, cancel, or mutate research jobs.
- The page does not install scientific engines, run simulations, modify repositories, approve candidates, or promote canonical state.
- Simulation, implementation, verification, and live verification remain separate evidence states.

## 6. Acceptance and verification

Focused checks are defined in `tests/test_research_reality_console.py`. Run:

```bash
python -m unittest tests.test_research_reality_console -v
```

The GitHub connector used to author this branch does not provide a local browser or repository test runner. Therefore, no local Python test execution, browser accessibility audit, or runtime integration is claimed by this change. Independent VV remains **NOT_RUN** until performed against the branch.

## 7. Next integration gates

1. Confirm the screen's information architecture and operator usefulness.
2. Implement a server-side Undermind status adapter only after API/authorization semantics are confirmed.
3. Add timestamped status events and freshness/expiry handling.
4. Add source-bound evidence and experiment receipt links.
5. Connect runtime execution and verification only through authorized VX interfaces.
6. Add independent VV review and browser/accessibility tests.
7. Keep merge, deploy, and canonical promotion as separate authorized decisions.

**Invariant:** UNKNOWN ≠ VERIFIED. A UI is not a runtime. A status snapshot is not a live connection. A research result is not an implemented capability.
