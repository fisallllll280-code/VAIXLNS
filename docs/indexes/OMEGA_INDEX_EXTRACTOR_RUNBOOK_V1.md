# Ω Index Extractor — runbook (v1)
Status: IMPLEMENTED SOURCE / RUNTIME IN REPOSITORY NOT YET VERIFIED

## Run on pinned local checkouts
```bash
python tools/omega_index_extractor.py \
  --repo ../VAIXLNS \
  --repo ../VX-runtime \
  --repo ../VAIXLNS-unified \
  --repo ../NEXENT \
  --out build/omega-extract

python -m unittest discover -s tests -p 'test_omega_index_extractor.py'
python tools/omega_unified_registry.py build build/omega-extract/extracted-records.jsonl build/omega-extract/omega-registry.sqlite
python tools/omega_unified_registry.py search build/omega-extract/omega-registry.sqlite Innovation
```

## Artifacts
- extracted-records.jsonl: one observation per file line with full Git commit, SHA-256, source location and original number when present.
- source-manifest.json: source files inspected with provenance and digests.
- coverage.json: count of scanned sources and extracted *mentions* (not validated unique inventions).
- SQLite: FTS5 searchable index built by the pre-existing omega_unified_registry.py.

## Limits and safe extension
This v1 extracts Markdown numbered items/headings and JSONL names. JSON, YAML, Python source, archives, tags, historic branches and all 28 views need specialized adapters/reconciliation. Never interpret the extractor's RECOVERED records as proven implementation. The source tree remains read-only. Keep all conflicting variants until reviewed. Run in a disposable checkout with network and credential exposure disabled. No direct change to project.genome or Ω.000; no automatic merge or release.

## Acceptance
Capture exit code, test log, pinned SHAs and generated file digests. Compare extraction to known source catalogs. Review missing coverage and suspected duplicate names manually. Zero-loss is a target, not proven from a partial source scan.
