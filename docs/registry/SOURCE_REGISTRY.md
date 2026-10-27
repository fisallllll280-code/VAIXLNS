# VAIXLNS Ω∞ — Source Registry

Status: PARTIAL / UNVERIFIED. This is a bootstrap record, not a claim of complete recovery.

## Principles
- Preserve historical sources and their provenance; never silently collapse two sources.
- Every claim must reference an identifiable source. Unknown or inaccessible source = UNVERIFIED.
- Source retrieval status is distinct from source truth/verification.
- Never publish private source content, credentials, or customer information in this public repository.

## Source schema
```yaml
source_id: SRC-0001
type: repo # conversation | file | repo | url | image | pdf | decision
title: VAIXLNS
date: null # first seen, ISO-8601 only when supported
origin: https://github.com/fisallllll280-code/VAIXLNS
retrieval_status: PARTIAL # RECOVERED | PARTIAL | MISSING | CONFLICTING
verification_status: UNVERIFIED # UNVERIFIED | VERIFIED
linked_items: [CAP-0001]
evidence: GitHub repository metadata, accessed 2026-10-27
notes: Registry bootstrap; tree and tests not fully audited.
```

## Initial source inventory (2026-10-27)
| ID | Repository | Retrieval | Verification |
|---|---|---|---|
| SRC-0001 | [VAIXLNS](https://github.com/fisallllll280-code/VAIXLNS) | PARTIAL | UNVERIFIED |
| SRC-0002 | [VAIXLNS-unified](https://github.com/fisallllll280-code/VAIXLNS-unified) | PARTIAL | UNVERIFIED |
| SRC-0003 | [vaixlns-core](https://github.com/fisallllll280-code/vaixlns-core) | PARTIAL | UNVERIFIED |
| SRC-0004 | [vaixlns-csd-kernel](https://github.com/fisallllll280-code/vaixlns-csd-kernel) | PARTIAL | UNVERIFIED |
| SRC-0005 | [VX-runtime](https://github.com/fisallllll280-code/VX-runtime) | PARTIAL | UNVERIFIED |
| SRC-0006 | [NEXENT](https://github.com/fisallllll280-code/NEXENT) | PARTIAL | UNVERIFIED |
| SRC-0007 | [vaixlns-nexent-vx](https://github.com/fisallllll280-code/vaixlns-nexent-vx) | PARTIAL | UNVERIFIED |
| SRC-0008 | [VX50_COMPLETE_BUILD](https://github.com/fisallllll280-code/VX50_COMPLETE_BUILD) | PARTIAL | UNVERIFIED |
| SRC-0009 | [vx-financial-kernel](https://github.com/fisallllll280-code/vx-financial-kernel) | PARTIAL | UNVERIFIED |
| SRC-0010 | [NAXLNS](https://github.com/fisallllll280-code/NAXLNS) | PARTIAL | UNVERIFIED |
| SRC-0011 | [vx-agents-fabric](https://github.com/fisallllll280-code/vx-agents-fabric) | PARTIAL | UNVERIFIED |
| SRC-0012 | [vx-agents-system](https://github.com/fisallllll280-code/vx-agents-system) | PARTIAL | UNVERIFIED |

Private repositories are listed by name only; permissions and content must remain protected.

## Recovery queue
- Index each source at an immutable commit SHA and record visibility/access controls.
- Recover uploaded text, screenshots and historical discussions into a PRIVATE evidence store, recording stable identifiers without copying confidential data here.
- Build source-to-item and item-to-source links.
- Never assert 2,750 positions correspond to 2,750 verified implementations.
