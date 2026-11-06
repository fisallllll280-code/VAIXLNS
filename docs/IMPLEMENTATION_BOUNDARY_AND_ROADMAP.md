# VAIXLNS Engineering Closure Matrix — Knowledge Genome Slice

This matrix prevents the new scanner from replacing existing authority, evidence, runtime, or recovery components.

| Engineering capability | Existing project surface | This slice | State / next gate |
|---|---|---|---|
| Canonical source and authority | `project.genome`, `Ω.000`, `Ω0_GENESIS_CORE` | Read-only alignment | Existing authority retained; no canonical registry mutation |
| Repository identity and disposition | `docs/indexes/REPOSITORY_DECISION_REGISTER_V1.md`, `registry/repository_registry.v1.json` | Uses caller-supplied stable repository identity | Existing identity catalogs must be reconciled before any write-back |
| Repository snapshot capture | `scripts/capture_repository_snapshots.py` | Complementary file-level fingerprint inventory | Not a replacement for complete Git snapshots/archive bundles |
| Architecture / reconstruction boundary | `docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md` | Emits file-level source observations for ARC-X input | Adapter contract and Ω.000 registration remain separate changes |
| Content integrity | SHA-256 in this probe; SFC innovation concept exists in the catalog | Exact byte hashes and deterministic report fingerprint | Does not implement the full semantic fingerprint canonicalizer |
| Claims, uncertainty and epistemic boundaries | NEXENT `nexent/epistemic_kernel.py` | Never asserts meaning from filenames or hashes | NEXENT remains the claim/evidence boundary; no changes to that repository |
| Runtime execution and replay | `VX-runtime` | No runtime commands are invoked | Execution stays behind VX policy and admission gates |
| Research, novelty and counterevidence | VAIXLNS-unified `innovation_control/research_fabric.py` and its tests | Reports exact byte duplicates only | Semantic novelty must use lineage/catalog checks and counterevidence; byte equality is not novelty proof |
| Local relationship graph | Relative Markdown links | Resolves valid local references, records broken/out-of-root links | Language-aware imports and remote links are not implemented |
| Change and recovery analysis | Existing recovery/snapshot tools | Diff against an optional baseline; missing records are preserved | No delete/archive/move/merge behavior is permitted |
| Contradiction detection | No matching executable engine identified by the focused preliminary search | Explicitly out of scope | Requires a separate claim-level contradiction model and adjudication tests |
| Security | Existing admission, external-integration and repository controls | Excludes common credential-like paths and skips symlinks | Not a secret scanner, malware scanner, permission auditor, or supply-chain scanner |
| Reproducibility | New unit tests + schema-validated, fingerprinted output | Deterministic on the same effective file snapshot and options | Release evidence must be run on a clean, pinned checkout in CI |

## Required continuation order

1. Land and run this slice in a branch; save CI run URL, commit SHA, and report fingerprint.
2. Inspect the existing repository contract and provenance/evidence schemas, then add an adapter rather than a parallel registry.
3. Compare the file-level records with the canonical repository decision register and current Ω.000 graph in read-only mode; emit conflicts instead of resolving authority automatically.
4. Add remote GitHub pagination only through a dedicated provider adapter with rate limits, commit pinning, retries, permission boundaries, and captured source responses.
5. Add syntax-aware extractors by language, keeping all extracted statements source-bound and non-authoritative by default.
6. Integrate claim-level checks with NEXENT, research/novelty checks with the existing research fabric, and execution only through VX admitted contracts.
7. Add contradiction adjudication, adversarial mutation, independent verifiers, replay, and recovery proof gates before any promotion to `VERIFIED` or `CANONICAL`.
8. Update Ω.000 only through a separate authority-controlled admission change after the evidence bundle is complete.

## Completion definition

The repository-cleanup effort is not complete when a list exists. It is complete only when each candidate has (a) stable identity and lineage, (b) source-bound inventory, (c) explicit status and uncertainty, (d) duplicate/conflict analysis, (e) verified dependency and authority edges, (f) reproducible tests/evidence, and (g) an explicit user disposition decision for destructive or identity-changing actions.
