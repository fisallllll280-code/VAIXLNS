# VAIXLNS — Repository Merge Matrix v1

Snapshot basis: GitHub evidence inspected on 2026-09-27.

| Repository | Current evidence | Recommended treatment | Merge target |
|---|---|---|---|
| VAIXLNS | Canonical architecture, recovery, registry and federation docs | KEEP CANONICAL | none |
| VAIXLNS-unified | Executable integrated runtime surface, tests and CI | KEEP + CONSOLIDATE RUNTIME | runtime root |
| NEXENT | Independent discovery, search and synthesis surface | KEEP SPECIALIZED | none |
| vaixlns-core | Current tree is documentation-focused despite README implementation claims | SELECTIVE CODE MERGE ONLY AFTER RECONCILIATION | VAIXLNS-unified |
| VX-runtime | Runtime contracts/specification; no executable runtime source observed in root tree | DOC-MERGE / SPECIALIZED-KEEP | VAIXLNS-unified docs |
| VAIXLNS-Intent-to-Reality | Intent pipeline documentation; current root contains docs rather than runtime source | DOC/SELECTIVE MERGE AFTER EVIDENCE | integration surface |
| vaixlns-csd-kernel | Specialized VAIXLNS_ROOT.lns kernel plus docs | SPECIALIZED-KEEP | none |
| VX50_COMPLETE_BUILD | Incomplete build surface; root is nearly empty outside docs | QUARANTINE / RECOVERY | later VX integration |
| VAIXLNS-Naming-Constitution-v1.0 | Constitutional support documentation | SYNC CANONICAL ARTIFACT | VAIXLNS constitution docs |
| VAIXLNS_OPERATIONAL_ASSURANCE.md | Assurance artifact repository | DOC-MERGE WHEN DEFAULT-BRANCH EVIDENCE IS AVAILABLE | VAIXLNS assurance |
| VAIXLNS- | Historical/unstable boundary | QUARANTINE | none |
| unrelated or uncategorized repositories | Relationship not yet proven | TOUCH NOTHING | none |

## Merge order

1. Preserve source SHA or tag.
2. Reconcile path and capability inventory.
3. Selectively import only proven unique implementation.
4. Run tests and integration checks.
5. Update federation and lineage records.
6. Keep the source repository visible as specialized or historical until stability is demonstrated.
7. Consider archival or read-only status only after verification.

The current repository evidence does not justify a blanket merge of all related repositories.
