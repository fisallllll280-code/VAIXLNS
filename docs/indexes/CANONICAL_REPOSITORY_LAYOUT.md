# VAIXLNS — Canonical Repository Layout

## Target structure

```text
VAIXLNS/
├── docs/
│   ├── canonical/       # canonical architecture maps
│   ├── indexes/         # recovery, innovation, repository, decision indexes
│   ├── recovery/        # provenance and recovery audits
│   ├── innovation/      # innovation catalogs
│   └── integration/     # NEXENT and federation boundaries
├── registry/
│   ├── *.json           # machine-readable manifests
│   └── atomic-system-registry/
├── schemas/
├── templates/
└── archive/
    └── source/          # preserved source corpus when publication is appropriate
```

## Ownership

`VAIXLNS` owns canonical meaning of the architecture, registry/lineage, governance boundaries and documentation.

`NEXENT` owns discovery, architecture search, synthesis and research proposals.

Runtime repositories own implementation; they do not redefine canonical authority by code presence alone.
