# Four-System Unification Execution v1

**State:** SPECIFIED; awaiting GitHub Actions and review evidence  
**Authority:** `project.genome` / `Ω0_GENESIS_CORE`  
**Master index:** `Ω.000`  
**Change policy:** additive-only; no source repository is renamed, deleted, or merged by this change.

## Objective

Create one inspectable federation view for the four independent system identities—VAIXLNS, VLNS, VX, and NEXNET—without conflating system identity with GitHub repository identity.

## Baseline observed

- `project.genome` identifies `fisallllll280-code/VAIXLNS` as VAIXLNS's canonical repository and declares `Ω.000` as the master index.
- `docs/indexes/FOUR_SYSTEM_RECONCILIATION_V1.md` records VLNS ↔ NAXLNS and NEXNET ↔ NEXENT as unresolved identity mappings.
- VX is represented by multiple repository surfaces, including `VX-runtime` and `VX50_COMPLETE_BUILD`; a repository name or specification does not prove a live runtime.
- NEXENT has its own repository and implementation evidence, but that alone does not prove it is the same identity as NEXNET.

These are repository-snapshot observations. Recheck them against immutable commits before an admission decision.

## What this change adds

1. `registry/federation/four_system_unification.v1.json`: a non-canonical, additive federation manifest.
2. `scripts/validate_four_system_federation.py`: deterministic standard-library structural and policy checks.
3. `tests/test_four_system_federation.py`: regression tests for system identity separation, canonical pointers, preservation policy, and unresolved mappings.
4. `.github/workflows/four-system-federation.yml`: CI execution of the validator and focused regression suite.
5. This runbook, defining the admission path and limits.

## Required integration sequence

1. Pin the source commit for every repository surface.
2. Inventory each surface's contracts, schemas, entrypoints, dependency manifests, test commands, workflows, licenses, and generated artifacts.
3. Extract system identity separately from repository name; preserve historical IDs and aliases as lineage records.
4. Build relationship edges only when supported: `same_as`, `implements`, `derived_from`, `supersedes`, `depends_on`, and `verified_by`.
5. Run each repository's own tests on its own pinned revision before testing cross-system adapters.
6. Test contract/schema compatibility in a sandbox and record exact workflow URLs, commit SHAs, outcomes, and artifact digests.
7. Keep unresolved identity mappings at HOLD. Do not merge source histories or mutate canonical registries as a shortcut.
8. Propose any Ω.000 registration as a separate reviewed change, with evidence references. Do not modify `project.genome` or Ω.000 in this initial slice.

## Status semantics

- `SPECIFIED`: contract or plan exists.
- `IMPLEMENTED`: code exists; not necessarily validated.
- `PARTIAL`: only a subset is implemented or required evidence is absent.
- `VERIFIED`: only after reproducible tests and independent evidence support the exact claim.
- `UNVERIFIED`: identity mapping remains unresolved.

Passing this manifest validator proves only that these structural invariants hold. It does not prove system identity, source completeness, runtime availability, production readiness, or the correctness of any remote repository.

## Acceptance criteria for the next stage

- Repository and system inventories are pinned to immutable commits.
- Original ideas, files, history, and provenance are preserved.
- Identity conflicts are explicit and block admission.
- Cross-system contracts have compatibility tests.
- CI evidence is linked to exact commit revisions.
- No claim is promoted to `VERIFIED` based solely on a README, generated plan, or successful manifest check.
