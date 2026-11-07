# Ω-SYMBOL × DISPOSITION — Engineering and Innovation Index v1

**Status:** IMPLEMENTED (two source manifests and one read-only validator); test execution and runtime integration **NOT_RUN**.  
**Canonical owner:** VAIXLNS. **Execution gate:** VX. **Index lineage:** ZERO-LOSS 00–27 and Ω.000 (reference only; untouched).  
**Baseline main SHA:** `433969a43b604563e22b70b8cb88223aff539fad` (2026-10-25 inspection).

## Why this extension is not another competing master index

Reuse `registry/indexes/zero-loss-index-taxonomy.v1.json` and `scripts/build_zero_loss_index.py`. The 28 views remain the primary deterministic source-based projection. This change adds exactly two **specialized registers**:

- `registry/indexes/symbol-semantic-index.v1.json`: stable `omega.symbol.*` concept identifiers, Arabic/English display labels, Unicode glyphs, and NO authority from glyphs.
- `registry/indexes/disposition-quarantine.v1.json`: a review and exclusion decision ledger for unnecessary, conflicting, deprecated, broken, redundant, or superseded items. No object is deleted by its inclusion here.

The active view derives from accepted source identities and lifecycle events. The exclusion register is **not** a replacement source of truth, and it does not erase original `SOURCE` or `ATOMIC` records. Add cross-references in existing views, not a second historical index.

## Research → design → innovation → implementation pipeline

`SOURCE → PROVENANCE → CAPABILITY GAP → FORMULATION → DESIGN → CONTRACT → SIMULATION → IMPLEMENTATION → TEST → PROOF → ADMISSION → EVOLUTION`

At each step, inspect missing or redundant components as engineering opportunities, not immediately as garbage. An unsupported claim of redundancy remains `REVIEW`.

## Disposition state and semantics

| State | Meaning | Allowed effect |
|---|---|---|
| REVIEW | identity or dependency unresolved | inspect, link, annotate |
| QUARANTINE_CANDIDATE | possible redundancy or unused tool | require recovery/dependency audit |
| RETIRED_APPROVED | formally reviewed with snapshot, dependency proof and approval | may be excluded from derived **active** projection, never source-deleted by this tool |

Candidate actions: `RECONCILE`, `REPAIR`, `REPLACE`, `CONSOLIDATE`, `ARCHIVE_2_REVIEW`, `RETAIN`. All require evidence.

**Proof obligations for any exclusion:** immutable source and hash, unique-knowledge recovery, dependency audit PASS, tests and reproducible behavior assessment, reviewed decision, explicit approval, rollback snapshot, source/target linkage and affected indexes. A passing validator checks presence and consistency of selected fields; it does not independently prove reviewer authenticity or runtime operation.

Protected original paths `project.genome`, `registry/omega/omega-000-master-index.json`, `registry/`, `docs/indexes/`, `schemas/`, `archive/` and `docs/recovery/` must not be removed by this pipeline.

**No silent deletion.** The validator has **no delete, rename, move, commit, merge or deploy code**. A separate, specifically approved change would be required to remove any expendable active implementation path; never use a mass-delete workflow.

## Initial observed findings (not deletion authorizations)

1. **Ω.DISPOSITION.0001:** `Ω.REPO.010` and `Ω.REPO.039` repeat the `VAIXLNS-Intent-to-Reality` label in `REPOSITORY_DECISION_REGISTER_V1.md`. They are *identity-reconciliation candidates*, not necessarily two repositories.
2. **Ω.DISPOSITION.0002:** `tools-vaixlns-meta-core-v0.3.ts` appears as an R0 historical tooling/archive candidate in the decision register. Repository content was **not** inspected.
3. **Ω.DISPOSITION.0003:** `friendly-engine` appears as a near-duplicate VV Arena experiment in the decision register. Unique capabilities were **not** established.

These evidence references are pinned to the baseline **Git blob SHA-1**, which is distinct from source SHA-256. Future source revisions must refresh evidence and re-review decisions.

## Unicode semantics / VV / VX

Unicode and CLDR data importers are **not** implemented. The initial symbolic entries are proposed visual mappings only; they are not a complete Unicode list. When importing official data later, pin source version, locale, SHA-256 and license; validate Unicode extended grapheme clusters and platform fallbacks, including RTL and accessibility. No symbol is a command. Displaying ✅ cannot independently set `VERIFIED`: an independent VX assurance record is mandatory.

Architecture assignment:
- VAIXLNS owns canonical identity, admission policies, data governance, historic lineage.
- VX alone authorizes and executes requests under explicit permissions.
- VV displays semantic labels, evidence links and reviewed decisions.
- NEXENT proposes research and innovation candidates; their identity remains distinct.
- VLNS naming/integration is an architectural adapter scope, not assumed to be a standalone accessible repository.

## Commands and evidence

```bash
python scripts/validate_symbol_disposition.py --root .
python -m unittest discover -s tests -p 'test_symbol_disposition.py' -v
python scripts/build_zero_loss_index.py --root . --output-dir build/zero-loss-index
python scripts/build_zero_loss_index.py --root . --output-dir build/zero-loss-index --verify-only
```

The validator exits nonzero if missing source/authority fields, malformed references, changed evidence Git-blob SHA, unjustified exclusion, deletion flag, protected exclusion, symbol collision or visual privilege escalation is observed. `--report build/disposition/audit.json` creates a **derived** report only.

The first two commands are specific to this change. The latter pair remains the existing master zero-loss workflow; no claim of their execution in this branch until recorded logs and receipts exist. CI and further end-to-end VX tests are separate gates.

## Required next engineering changes

1. Connect the read-only disposition audit as a parallel, non-mutating CI check.
2. Link retired dispositions into the 28 existing generated views as annotations, without rewriting history.
3. Add repository-specific provenance and dependency reachability before any active exclusion.
4. Implement separately tested Unicode/CLDR importer with pinned file hashes and licenses.
5. Verify VV display and VX assurance receipts; only then consider admission to canonical Ω.

**Release rule:** isolated branch; no changes to `project.genome` or `Ω.000`; no merge, publishing, permanent deletion or promoted VERIFIED status from this document.
