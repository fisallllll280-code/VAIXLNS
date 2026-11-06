# Repository Organization and X-Marked Idea Correction Register v1

- Date: 2026-10-16
- Status: INITIAL AUDIT / PROPOSED ORGANIZATION
- Scope: VAIXLNS, VAIXLNS-unified, VX-runtime, NEXENT
- Safety: additive-only; no files moved, renamed, overwritten, or deleted by this change.
- Canonical authority: `VAIXLNS/project.genome::v1.0.0`, `Ω0_GENESIS_CORE`, and `VAIXLNS/registry/omega/omega-000-master-index.json` (`Ω.000`).

## 1. Non-negotiable preservation rules

1. Preserve `project.genome` and `Ω.000` byte-for-byte unless a separately reviewed, evidence-backed canonical change is approved.
2. Never delete a legacy idea or artifact because it is marked `X`, obsolete, duplicate-looking, contradictory, or unverified.
3. Preserve the original text and lineage. Record a proposed correction in a separate entry, with rationale and evidence references.
4. No canonical promotion based on presence in Git, naming, a green UI indicator, or a model's assertion alone.
5. Use `PROPOSAL`, `SPECIFIED`, `PARTIAL`, `MISSING`, `CONFLICT`, `IMPLEMENTED`, and `VERIFIED` carefully. `VERIFIED` requires reproducible evidence for the specific claim.
6. Work on branches and submit a reviewable pull request. Do not merge or rewrite canonical history as part of this initial organization pass.

## 2. Repository responsibility map

| Repository | Intended responsibility | Boundary / current caution |
|---|---|---|
| `fisallllll280-code/VAIXLNS` | Canonical control plane, governance, `project.genome`, `Ω.000`, evidence admission and system contracts | Canonical authority stays here; protect the two source-of-truth files. |
| `fisallllll280-code/VAIXLNS-unified` | Integrated execution surface and cross-system workspace | Treat it as an execution/integration projection, not a replacement canonical source. Reconcile through contracts and evidence. |
| `fisallllll280-code/VX-runtime` | VX execution-core specification and implementation boundary | Its README explicitly says the repository currently contains the runtime specification; do not describe runtime behavior as implemented until code and executable tests establish it. |
| `fisallllll280-code/NEXENT` | Discovery, search, architecture synthesis, research and candidate generation | Keep NEXENT independent from VAIXLNS adoption authority. Candidates require simulation/verification and a separate governance decision before adoption. |

### Identity conflicts that remain open

- `NEXENT` vs `NEXNET`: do not assume they are aliases or the same system until an authoritative identity record resolves the conflict.
- `VLNS` vs `NAXLNS`: do not merge names, indexes, or responsibilities until an authoritative identity record resolves the conflict.
- A repository name, folder, README, or code-search result alone is not sufficient to settle canonical identity.

## 3. Initial correction register for known unsafe or overstated claims

These are corrections to apply wherever the corresponding claim is found. They do not imply that every instance has already been edited.

| ID | Incorrect / unsafe claim pattern | Corrected rule | Required evidence |
|---|---|---|---|
| XFIX-001 | “No contradiction found” means `APPROVED` / `APPROVED_FOR_NEXUS` | Contradiction detection and evidence admission are separate gates. Default to `PENDING_VERIFICATION`; unresolved identity, evidence or authority blockers fail closed. | Explicit claim set, counterevidence search result, independent evidence-admission result, reviewer/authority record. |
| XFIX-002 | Indexed coverage means canonical completeness | Report measured coverage against a named index/scope only. Never infer completeness of the entire project from index coverage. | Scope definition, denominator, missing-item report, reconciliation evidence. |
| XFIX-003 | An axiom or proposed invariant is a proof | Label axioms as assumptions and propositions as unproven until proof obligations are discharged. | Formal derivation or executable property tests appropriate to the claim. |
| XFIX-004 | Replay is reproducible because it ran twice | Replay requires independent Run A/Run B comparison with the same declared inputs, environment constraints, and matching expected output/evidence digests. Record nondeterministic fields explicitly. | Two run receipts, input/output hashes, environment metadata, comparison result. |
| XFIX-005 | “Generated” means an artifact exists and is valid | Bind every generated-artifact claim to an artifact path/ID, content hash, generator/version, inputs and validation result. | Artifact plus content digest and reproducible generation/validation receipt. |
| XFIX-006 | `primary-alpha-01` is operational because it is named in a design | Keep it `SPECIFIED` unless actual runtime telemetry and independent checks establish operation. | Timestamped telemetry, health/contract probe, identity and provenance. |
| XFIX-007 | Authority can create or substitute for evidence | Authority may authorize a transition; it cannot manufacture evidence or prove a claim. Keep evidence, verification/assurance, and promotion decision as separate records. | Evidence bundle, verifier result, separate promotion/decision receipt. |
| XFIX-008 | A green UI / `connected=true` establishes a live integration | UI is a projection of server-owned state. Connection, verification, authorization and task execution are separate dimensions. | Real probe result with integration identity, timestamp, config version and evidence reference. |
| XFIX-009 | Similar names or overlapping folders prove duplicate systems | Mark suspected overlap as `CONFLICT` / `PENDING_REVIEW`; preserve both and compare ownership, contracts, lineage and tests before proposing consolidation. | Side-by-side file/contract inventory and approved migration plan. |
| XFIX-010 | A specification or README proves implementation | Use `SPECIFIED` for design-only artifacts and `PARTIAL` / `IMPLEMENTED` only where code and tests support the exact claim. | Source inspection, executable tests, CI output and reproducible evidence. |

## 4. How to handle every X-marked idea

For each X marker discovered in any repository:

1. Capture the original idea verbatim and its immutable source URL/path, commit SHA and content hash where available.
2. Classify what X means in that source: rejected, failed test, unresolved concern, obsolete proposal, or merely a visual marker. Never infer its meaning from the symbol alone.
3. Create a separate correction entry with: `idea_id`, `original_text_ref`, `marker_meaning`, `claim_type`, `corrected_statement`, `rationale`, `evidence_refs`, `status`, `reviewer`, and `timestamp`.
4. Preserve the original. Use an additive correction or superseding note; do not silently edit history.
5. If the claim cannot be settled from repository evidence, mark it `CONFLICT` or `PENDING_VERIFICATION` and list the missing proof. Do not invent a correction.
6. Re-run relevant tests and check that canonical files and unrelated content are unchanged.

## 5. Organization sequence

1. Inventory repositories, branches, root paths, contracts, tests, CI and canonical references.
2. Compute and record baseline hashes for `project.genome` and `Ω.000`.
3. Build a cross-repository path/ownership map; distinguish canonical sources, implementation, specifications, evidence, research and archive.
4. Detect X markers and duplicate-looking artifacts without moving or deleting them.
5. Add corrections and proposed moves as separate, reviewable changes.
6. Validate references, tests, index consistency and baseline preservation.
7. Open a PR; do not merge until evidence and review gates pass.
8. After approved migrations only, add redirects/cross-references and re-index. Legacy material remains archived, not deleted.

## 6. Initial audit evidence

- `VAIXLNS/project.genome` was inspected on `main`; its current blob SHA was `7b8822cff6321d2b750aec030e29b928ed685940`.
- `VAIXLNS/registry/omega/omega-000-master-index.json` was inspected on `main`; its current blob SHA was `cbd3b32f7a9bf74650fdae02a8ebb0831dca84dc`.
- `VAIXLNS/docs/canonical/CANONICAL_CONTROL_PLANE_V1.md` identifies VAIXLNS as canonical and distinguishes lifecycle state from epistemic state.
- `VX-runtime/README.md` states that the repository currently contains the VX runtime specification and that implementation claims require code/tests/reproducible evidence.
- `NEXENT/README.md` defines NEXENT as a discovery/research/candidate-generation engine and keeps VAIXLNS adoption separate.
- `VAIXLNS/registry/omega/omega-000-master-index.json` already records VX as `PARTIAL` and several capabilities as `SPECIFIED`; those labels must not be upgraded without new evidence.

This is a bounded initial register, not a claim that every repository or every X marker has already been exhaustively scanned. The next pass must enumerate exact X-marked occurrences and attach per-occurrence evidence.
