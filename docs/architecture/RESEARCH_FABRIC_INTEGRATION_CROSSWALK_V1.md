# Research Fabric Integration Crosswalk v1

**Status:** SPECIFIED / integration review required  
**Canonical identity:** `project.genome::v1.0.0`  
**Master index:** `Ω.000` at `registry/omega/omega-000-master-index.json`

## Critical discovery

The current Ω.000 record for `VAIXLNS.RESEARCH.DECISION.FABRIC.001` points to an existing provider-neutral research implementation in `fisallllll280-code/VAIXLNS-unified`:

- `innovation_control/research_fabric.py`
- `tests/test_research_fabric.py`
- `config/research-decision-bundle.schema.json`
- `docs/INNOVATION_RESEARCH_DECISION_FABRIC_V1.md`

The main VAIXLNS repository also contains the innovation operation index generator and validator. Therefore, **do not create a second competing research runtime or a parallel master index**. The files in this pull request add a record format, validation gate, and workspace guidance; they are not a replacement for the existing research-decision fabric.

## Responsibility split

| Component | Responsibility | Integration rule |
|---|---|---|
| `project.genome` | Project identity and canonical source | Read-only for this work |
| `Ω.000` | Master system/capability index | No automatic mutation |
| `VAIXLNS-unified/innovation_control/research_fabric.py` | Existing research planning, source provenance, counterevidence, lineage, engineering completeness, decision bundle | Candidate runtime to extend after tests and interface review |
| `VAIXLNS/tools/build_innovation_operation_index.py` | Deterministic innovation catalog/projection | Reuse; do not replace |
| `schemas/research-comparison-record.schema.json` | Durable per-question research record | Map to the existing bundle only through a versioned adapter |
| `scripts/validate_research_records.py` | Fail-closed structural and evidence-state check | A pre-admission check, not a scientific truth oracle |
| ARC-X | Claim/evidence/authority/execution separation | Independent admission boundary |
| VX | Task execution, replay, and execution evidence | Execute only authorized task packets |

## Required integration sequence

1. Pin reviewed SHAs for the main and unified repositories, the existing fabric implementation, its schema, tests, and the innovation index generator.
2. Run existing research-fabric tests and the new record-validator tests in their own repository contexts. Capture CI run IDs and results.
3. Write a versioned adapter from the existing research bundle to the new record schema. Preserve source IDs, content hashes, claim stances, failed query lanes, uncertainty, and open questions.
4. Route discovery, novelty, counterevidence, contradiction, implementation evidence, and failure analysis through distinct query lanes. Provider adapters must report actual results; no provider success may be fabricated.
5. Add mathematical, computational, physical, and systems-engineering comparison profiles with explicit metrics, baselines, units, assumptions, and reproducibility metadata.
6. Connect admitted outcomes to VX task packets with acceptance tests, required authority, rollback plan, and evidence references.
7. Generate a supplementary cross-reference for Ω.000 review. Do not automatically change Ω.000 or claim canonical promotion.
8. Promote only after independent review, reproducible CI, and end-to-end evidence from source query through a VX task result.

## Required adapter invariants

- Bundle and record hashes must be deterministic over canonical serialization.
- A failed or missing required search lane remains visible and blocks claims of comprehensive research.
- Duplicate/near-duplicate candidates link to prior native IDs; do not synthesize historical IDs.
- A source URL, model answer, or citation alone is not proof that a claim is correct.
- `VERIFIED` requires reproducible evidence and accepted independent review.
- No research output grants itself authority to write canonical files, merge a pull request, publish externally, or execute high-impact actions.

## Repository creation note

The connected GitHub toolset used for this change exposes file, branch, and pull-request operations, but no repository-creation operation. This work is therefore staged in a dedicated feature branch and draft PR within the existing canonical repository rather than falsely claiming a separate GitHub repository was created. A standalone repository can be created later through an authorized GitHub repository-creation action, then linked as a subordinate research workspace without moving or replacing canonical sources.
