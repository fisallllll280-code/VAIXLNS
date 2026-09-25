# VAIXLNS — Canonical Project Hub

This repository is the canonical architecture, registry, recovery, provenance, and documentation root for the VAIXLNS federated project.

## Navigation

- [Master index navigation](docs/indexes/README.md)
- [Master recovery status](docs/indexes/MASTER_RECOVERY_STATUS.md)
- [Archive source index](docs/indexes/ARCHIVE_SOURCE_INDEX.md)
- [Innovation master index](docs/indexes/INNOVATION_MASTER_INDEX.md)
- [Repository federation index](docs/indexes/REPOSITORY_FEDERATION_INDEX.md)
- [Engineering decision register](docs/indexes/ENGINEERING_DECISION_REGISTER.md)
- [Canonical repository layout](docs/indexes/CANONICAL_REPOSITORY_LAYOUT.md)
- [Canonical V6 architecture](docs/canonical/CANONICAL_MASTER_ARCHITECTURE_V6.md)
- [Recovery audit](docs/recovery/VAIXLNS_MASTER_RECOVERY_AUDIT.md)

## Canonical boundary

```text
NEXENT
DISCOVER → DESIGN → SEARCH → SIMULATE → PROPOSE
                      │
                      ▼
VAIXLNS
CANONICALIZE → GOVERN → VERIFY → ADOPT → OPERATE
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
  VAIXLNS-unified  vaixlns-core  CSD / INTENT / VX
```

Historical names and variants remain preserved through provenance and lineage. A proposal is not treated as implemented merely because it appears in an architectural document.
