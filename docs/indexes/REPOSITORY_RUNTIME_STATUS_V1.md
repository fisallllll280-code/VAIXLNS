# Repository Runtime Status v1

Snapshot: 2026-10-03

This is an evidence report, not a claim of successful local execution.

| Repository | Source observed | Tests observed | CI observed in tree | State |
|---|---:|---:|---:|---|
| VAIXLNS | Canonical docs/registry | No runtime tests | No runtime CI required at this surface | CANONICAL DOC/REGISTRY SURFACE |
| NAXLNS | Specification / Python repository content | Not independently executed in this audit | Not independently verified in this audit | VLNS CANDIDATE / IDENTITY UNVERIFIED |
| VAIXLNS-unified | Yes | Yes | Yes | PARTIAL / EXECUTABLE SURFACE |
| vaixlns-core | No executable source established in current evidence | No executable tests established | No | SPECIFICATION / RECONCILIATION NEEDED |
| vaixlns-csd-kernel | DSL only | No | No | SPECIFIED |
| VX-runtime | Runtime specification, no implementation established | No | No | VX SPECIFICATION / CONTRACT SURFACE |
| VX50_COMPLETE_BUILD | Historical/build surface, no runtime implementation established | No | No | HISTORICAL / INCOMPLETE |
| VAIXLNS-Intent-to-Reality | Specification / workspace | No executable runtime established | No | INCOMPLETE / RECOVERY |
| VAIXLNS-Naming-Constitution-v1.0 | Naming/governance artifact | No | No | CONSTITUTIONAL SUPPORT |
| VAIXLNS_OPERATIONAL_ASSURANCE.md | Assurance artifact | No | No | ASSURANCE ARTIFACT |
| VAIXLNS- | Historical / unstable boundary | No | No | QUARANTINED |
| NEXENT | Python + Rust source | Yes | Yes | IMPLEMENTED DISCOVERY BASELINE / NEXNET IDENTITY UNVERIFIED |

## Four-system interpretation

- VAIXLNS: canonical control plane and recovery/index authority.
- VLNS: NAXLNS is the current repository surface candidate; identity requires explicit evidence.
- VX: VX-runtime + VX50_COMPLETE_BUILD form a multi-repository execution surface; the inspected VX-runtime repository is currently specification-first.
- NEXNET: NEXENT is an implemented discovery/research surface; identity equivalence to NEXNET remains unverified.

## Execution rule

A runnable claim requires:

entrypoint + dependency resolution + execution + test + reproducible evidence

No repository is VERIFIED from README language alone.

## 2026-10-07 Stage runtime addition

The canonical VAIXLNS repository now contains a Stage reference runtime boundary for one VX instance:

- `VX-STAGE-001` golden scenario;
- signed request conformance;
- authority-aware routing;
- controlled failure isolation;
- recovery and re-routing;
- machine-readable Stage evidence.

This is an IMPLEMENTED reference/conformance surface, not proof of production deployment. Production status still requires deployment infrastructure and sustained operational evidence.
