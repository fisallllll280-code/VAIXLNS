# VX Source Discovery and Engineering Research Operating Contract v0.1

**Status:** PROPOSED orchestration + bounded extractor implemented in VX-runtime feature branch. Not a complete historical recovery or live cross-repository federation.

## Scope and authority

VAIXLNS remains the canonical owner of `project.genome`, `Ω0_GENESIS_CORE`, and `Ω.000`. VX is tasked with read-only discovery, source indexing, task routing and evidence receipts. VX never grants itself authority to modify original indexes, adopt identities, merge repositories, publish or spend.

## Family research inventory

| Group | Labels requiring source-specific classification | Evidence rule |
|---|---|---|
| Canonical foundational | VA, V, VV, VX, XV | Consult Global Fabric and historical genome; names are not proof of live services |
| Requested variants | NX, XN, NA, AN | Search exact token in pinned repository sources; preserve unresolved lineage |
| Wider branches | AV, AX, XA, VN, NV, VLNS, NEXNET, NEXENT | Link by contracts, not lexical equality |
| Other recovered systems | SUF, GXL, MAL, AGL, CVL, NET, SEC, ECO, RES, EDU, OPS, INF, APP, FUT | Keep original IDs and source attribution |

## Initial executable extractor

Existing branch implementation:
- VX-runtime `tools/vx_federation_index_discovery.py`
- VX-runtime `tests/test_vx_federation_index_discovery.py`

CLI from VX-runtime repository root, with local checked-out permitted source trees:

```sh
python tools/vx_federation_index_discovery.py \
  --source VAIXLNS=../VAIXLNS \
  --source NEXENT=../NEXENT \
  --source VAIXLNS-unified=../VAIXLNS-unified \
  --out build/vx-discovery/families.json
python -m pytest -q tests/test_vx_federation_index_discovery.py
```

The tool observes **text references**, storing repository + relative path + content SHA-256. It does NOT assert a matching acronym is a system, innovation, live integration, inventor, or identity equivalence. Missing repositories yield an explicit error, rather than silent success. The bounded extractor is not the existing 28-view zero-loss index builder.

## Reuse, rather than fork, the canonical indexer

Run `VAIXLNS/scripts/build_zero_loss_index.py` on a pinned VAIXLNS checkout to generate the five-file source-bound zero-loss bundle (28 views). Keep originals immutable. VX may ingest that derived export by approved adapter; external repository contents require separate read-only adapters, source SHA records, identity checks, coverage reports, de-duplication candidates and explicit failed-source receipts.

## Proposed governed development and engineering-research cycle

1. DISCOVER source sets: pinned repositories, permitted historical archives, code/tests, research papers, engineering standards, approved external model outputs, lab/simulation observations.
2. PROVENANCE: capture source URI, revision, publisher/license when applicable, byte digest, time, access policy, and reliability limits.
3. CLASSIFY: family/role/claim/unknown/contradiction with explicit uncertainty; never infer execution status from README text.
4. RESEARCH: generate alternate hypotheses, review prior art and independent sources; classify novel claim as UNVERIFIED until evaluated.
5. ENGINEER: NEXENT/XV propose architectures and constrained experiments; ARC-X structures evidence, VCRE simulates, VV independently challenges.
6. ADMIT: VAIXLNS authority checks policy and proof before VX receives an execution lease.
7. EXECUTE: VX isolated branch/sandbox, captured dependency versions, zero external spend unless separately approved.
8. VERIFY: run stage-gated T01–T05 → T06–T10 → T15 → T11–T14; negative/tamper/recovery/replay tests required.
9. RECORD: append source-linked evidence and propose index delta for owner review; no autonomous canonical write.
10. COMPARE: before/after performance, correctness, security, reproducibility, and rollback.

## Acceptance and open gaps

The initial extractor covers only text files reachable in configured local checkouts. It does not fetch GitHub automatically, search live scientific databases, parse PDF figures, solve identity conflicts, or recover all historical 0001–2750 rows. Follow-on adapters must have permission boundaries, connector-specific tests and signed/source-pinned receipts. An extractor unit-test pass does not prove cross-system connectivity.

## References

- [Master Index Navigation](../indexes/README.md)
- [Zero-Loss Index](../indexes/VAIXLNS_ZERO_LOSS_INDEX_V1.md)
- [Canonical System Map](../canonical/REPOSITORY_SYSTEM_MAP_V1.md)
- [Omega Global Fabric](../omega/VAIXLNS_GLOBAL_FABRIC.md)
- [Research-to-Engineering Control](../architecture/VAIXLNS_ENGINEERING_MIND_AND_REPOSITORY_CONTINUITY_FABRIC_V1.md)
