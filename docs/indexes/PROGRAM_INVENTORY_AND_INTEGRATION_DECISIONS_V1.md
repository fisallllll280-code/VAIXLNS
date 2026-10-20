# VAIXLNS Program Inventory and Integration Decisions v0.1

Date: 2026-10-21. Review only, no main merge or canonical changes.

## Inventory counts from the repository recovery audit

| Index | Count | Interpretation |
|---|---:|---|
| Innovation Master Index | 97 | Indexed innovation names, not running programs |
| Innovation Operation Index | 177 | Review records, not unique deployed programs |
| Records requiring review | 174 | Pending source-by-source review |
| UNKNOWN | 66 | Unresolved evidence state |
| Conflicts | 2 | Require reconciliation |
| Evidence-linked records | 22 | Not proof of live operation |
| Index views | 28 | Search views, not apps |
| Historical range | approx. 0001-2750 | Not fully recovered |

## System capabilities and integration choices

| System | Definition | Indexed contribution | Evidence | Decision |
|---|---|---|---|---|
| VAIXLNS | Canonical authority and registry | Omega constitution, truth/meaning/derivation, Nexus | Canonical documents and validators | Preserve independent owner |
| VX-runtime | Policy-governed execution/replay | Event ledger, capability checks and deterministic replay | Runtime CI passed PR 18 | Integrate via contracts, no repository merge |
| VAIXLNS-unified | Innovation engineering assembly | Invention, self discovery, research control, architecture arena | Four CI workflows passed PR 65 | Review components for bounded adoption |
| NEXENT | Discovery and candidate evolution | System graph, DSL, controlled evolution | Source and specs; live bridge not checked | Keep independent, bridge proposals |
| ARC-X | Evidence reconstruction | Claim/evidence separation, proof obligations | Specifications and reference code | Bridge after live endpoint verification |
| VV/VCRE | Independent verification and simulation | Verification plans, computational modeling | Reference implementation and historical tests | Integrate as separate verification role |
| VLNS/NAXLNS | Semantic and engineering boundaries | Historical identity candidates | Equivalence unverified | Hold merge |
| NEXNET/NEXENT | Federation identity | Historical identity candidates | Equivalence unverified | Hold merge |
| Omega infinity / Psi | Governance of evolution | Architecture recursion, constitutional optimization | Proposal only | No automatic execution promotion |

## Integration and merge gates

1. Protect project.genome and registry/omega/omega-000-master-index.json.
2. Pin source commits, record ownership and evidence before adoption.
3. Execute VX T01-T05, T06-T10, T15, T11-T14 in that order.
4. Require independent proof for NEXENT -> ARC-X -> VV -> VAIXLNS authority -> VX.
5. Preserve divergent history. Selectively recover capabilities, never wholesale-merge unrelated repositories.
6. Attribute inventions to documented source commits; no originality claim solely from an index title.
7. No main merge, production publication or spending without owner approval.

## References

- [Innovation master](INNOVATION_MASTER_INDEX.md)
- [Recovery delivery audit](../recovery/VAIXLNS_UNIFIED_INNOVATION_DELIVERY_MAP_2026-10-10.md)
- [Architecture](../canonical/CANONICAL_MASTER_ARCHITECTURE_V6.md)
- [System evolution cards](SYSTEM_EVOLUTION_STATUS_CARDS_V1.md)
- [Ordered repositories](ORDERED_REPOSITORY_INDEX_AR.md)
