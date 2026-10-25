# GEDF Research-to-Engineering Pipeline v1

Status: executable offline reference implementation; not a live autonomous research service. Parent: VAIXLNS / GEDF. Intended composition: GEDF → VCRE candidate assessment → VX gated execution → VV/ARC-X independent verification.

## Why this layer exists
GEDF already has a proposal and structural integrity validator. This change adds a narrow executable bridge from a source-pinned research capsule to a deterministic verification plan. It does not create a parallel master index or rewrite VCRE.

## Data contract
A capsule includes a mission ID, research question, core math/computation/software/physics domains, source receipts (HTTPS URL, source type, evidence level, retrieval time, captured-text SHA-256), source-bound claims labelled by epistemic state, and falsifiable hypotheses with alternatives and a baseline comparison.

Hashes prove captured-byte integrity, not source authenticity or claim truth. Abstract-only, full-text, inspected source code, executed tests and measured results remain distinct evidence levels.

## Deterministic output
The compiler creates an 11-stage DAG: source integrity; claim mapping; prior-art/counterevidence; mathematics; numerical stability/uncertainty; software/supply chain; physical invariants; integration conformance; sandbox test/simulation; independent falsification; human governance review. Every task is PLANNED_NOT_EXECUTED. The plan is PENDING_HUMAN_REVIEW. Optional VCRE assessment never implies proof or deployment.

## Run
```bash
python -m unittest tests.test_gedf_research_pipeline -v
python scripts/gedf_research_pipeline.py --capsule examples/gedf-research-capsule.example.json --output build/gedf/research-plan.json
```

## Current boundaries
This bridge does not fetch literature, crawl repositories, execute solvers, invoke providers, create GitHub repositories, run a sandbox, or write Ω.000. Read-only collectors, VX execution receipts, and independent VV/ARC-X verification are follow-on integration gates.

## Next integration gates
1. Connect approved read-only Undermind/GitHub collectors and preserve retrieval receipts.
2. Add Arabic/English indexing without destructive normalization.
3. Link hypotheses to VCRE candidate envelopes and domain proof obligations.
4. Add benchmark data and prior-art recall/precision metrics.
5. Bind sandbox receipts and independent verification.
6. Admit reusable outcomes only through existing GEDF/Ω.000 governance.
