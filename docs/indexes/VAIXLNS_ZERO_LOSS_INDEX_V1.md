# VAIXLNS ZERO-LOSS INDEX V1

**Index ID:** VAIXLNS.ZERO_LOSS_INDEX  
**State:** SPECIFIED taxonomy / IMPLEMENTED deterministic repository builder  
**Canonical source:** project.genome::v1.0.0  
**Master index:** Ω.000 (registry/omega/omega-000-master-index.json)

## Objective

One consolidated indexing fabric must preserve source identity, content digests, locations, historical identifiers, entity candidates, terminology, contracts, authority, events, state, dependencies, relations, lineage, canonical references, implementation, repositories, artifacts, tests, evidence, proof, operations, failure/recovery, security, observability, simulation, evolution, and cross-references.

The taxonomy is machine-readable at registry/indexes/zero-loss-index-taxonomy.v1.json. It defines the 28 index views 00 through 27. The builder emits a consolidated view index and source-bound JSONL records rather than maintaining 28 independently edited lists that can drift apart.

## Build and verify

From the repository root:

    python -m unittest discover -s tests -p 'test_zero_loss_index.py' -v
    python scripts/build_zero_loss_index.py --root . --output-dir build/zero-loss-index
    python scripts/build_zero_loss_index.py --root . --output-dir build/zero-loss-index --verify-only

Output bundle:

| Artifact | Purpose |
|---|---|
| zero-loss-index.v1.json | One canonical navigation manifest containing all 28 populated views, their record/source references, transition gates and integrity hashes. |
| zero-loss-source-index.v1.json | Exact repository file inventory with path, repository revision, byte size, media type and SHA-256. |
| zero-loss-atomic-records.v1.jsonl | Stable source records, Markdown sections/list items, JSON entities and terminology candidates. |
| zero-loss-coverage.v1.json | Coverage counts, opaque source inventory, duplicate byte hashes, connector boundaries and legacy gaps. |
| zero-loss-cross-reference.v1.json | Direct textual/Markdown source-path references with source and target identity. |

The GitHub Actions workflow runs the tests, builds the bundle, verifies the generated hashes, and uploads the artifacts. The workflow is read-only with respect to repository contents; generated artifacts are not silently committed back into canonical source.

## The atomic record

schemas/zero-loss-atomic-record.schema.json defines the record contract, including UID, source ID/location/digest, legacy and canonical IDs, name/aliases, type/family/domain/origin/meaning, status, parent/children, lineage, supersession, dependencies, capabilities, contracts, authority, state, events, execution, evidence, proof, implementation, tests, failure, recovery, version, lifecycle and evolution.

Unknown fields stay null or empty; extracted but not classified material stays UNRESOLVED. A source-reported status is retained separately as source_claimed_status. Extracting a claim is not proof that the claim is true.

## Loss prevention and state transitions

- Every source file is inventoried and SHA-256 hashed. Files which are binary or cannot be decoded as UTF-8 remain in the source index; content parsing is separately marked pending.
- Every atomic record refers to a source ID, repository-relative location, source digest and lineage edge.
- Original inputs are read-only. Identical byte hashes produce duplicate-candidate groups; no source, row, identifier or artifact is removed or merged.
- Explicit source-path references are labelled SOURCE_PATH_REFERENCE; they do not automatically become dependencies, aliases or lineage.
- Automatic extraction creates SOURCE and ATOMIC records only. It never assigns CANONICAL, IMPLEMENTED or VERIFIED.
- A canonical transition needs a source-grounded canonical ID and explicit authority evidence. Implementation needs artifacts and test evidence. Verification needs reproducible results and a separate proof record.
- An unobserved historical ID is represented in a compressed unresolved-gap ledger, not as a fabricated historical record.

The repository mentions a historical range around 0001–2750 and 40+ families. This is not an item-by-item source manifest. The gap ledger therefore labels its range approximate and explicitly states that an unseen ID is only an unresolved candidate gap, not proof of a missing original entry.

## Scope limits

The repository checkout is the only source surface scanned by this build. It does not automatically import conversation history, ChatGPT Library uploads, unmaterialized PDFs, remote GitHub repositories, or non-text diagram semantics. The taxonomy records each missing adapter and its status. Add a source-specific, read-only adapter and tests before changing those statuses.

A successful build proves inventory and referential integrity for that exact source revision. It does not prove that all project history was supplied, that all 2,750 historical items have been recovered, or that source claims are canonical, implemented or verified.
