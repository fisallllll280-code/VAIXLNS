# VAIXLNS Automatic File Intake and Library v1

**Status:** staged implementation on draft PR; automatic operation needs merge, GitHub Actions authorization and successful workflow evidence.

## Lifecycle
New nonconfidential file → `intake/inbox/` → source SHA-256 and original filename → candidate category/repository/path → `library/intake` evidence → draft PR for eligible same-repository text → human review → optional promotion. Cross-repository targets are **recommendations**, not writes.

## Routing
- Indexes: `VAIXLNS/docs/indexes/intake/`
- Innovations: `VAIXLNS/docs/innovation/intake/`
- Models: `VAIXLNS/registry/models/intake/` (registries/metadata only, not weights)
- Agents: `VAIXLNS/docs/agents/intake/`
- Research: `NEXENT/docs/research/intake/` (separate PR needed)
- VX execution: `VX-runtime/docs/intake/` (separate PR needed)
- Evidence: `VAIXLNS/registry/evidence/intake/`
- Archives: `VAIXLNS/archive/source/intake/`
- Unclassified: no target; requires review.

## Automatic workflows
After merging to main:
1. `push` touching `intake/inbox/**` triggers deterministic routing, tests, Zero-Loss Index projection and evidence artifacts.
2. `pull_request` updates run tests under a read-only token, with no publication.
3. Six-hour schedule and manual dispatch regenerate evidence without writes.
4. On a trusted `push` to main, a second job stages **only nonsecret text** to content-addressed `library/objects/<prefix>/<sha256>`, writes `library/intake/auto-intake.v1.jsonl`, and opens a **draft PR** with proposed same-repository intake destinations.
5. Binary and unknown files are metadata-only or blocked; cross-repository targets are metadata-only pending an independently authorized target-repo PR.
6. The draft PR is never automatically merged or canonically admitted.

**Required GitHub setting:** under repository Settings → Actions → General → Workflow permissions, allow GitHub Actions to create pull requests; the job also needs the explicitly scoped `contents:write` and `pull-requests:write` permissions. If repository settings disallow PR creation, the reporting workflow still generates inspectable evidence but the publication job can fail; do not call the process fully active until this is verified.

## Local commands
```bash
python -m unittest discover -s tests -p "test_*intake*.py" -v
python tools/auto_intake.py --root . --inbox intake/inbox --out build/auto-intake
python tools/auto_intake.py --root . --inbox intake/inbox --out build/auto-intake --include-payloads
python tools/stage_intake_review.py --root . --inbox intake/inbox
```

First command runs safe intake tests. Second produces read-only evidence; third builds a local review object library. Fourth writes safe text into a checked-out worktree and should be used only on a separate review branch.

## Invariants and security
- **Never upload confidential files to a public inbox.** Secrets cannot be reliably detected by the heuristic scanner, particularly inside archives and PDFs.
- Never execute inbound files. Executables, keys, links and oversized items are blocked or held.
- Original source bytes and original paths are kept; identical bytes share objects, not source identities.
- Unknown/duplicate names do not override an existing unrelated object; digest names avoid collisions.
- Automatic classification is not authorization, correctness proof, capability verification, model connectivity, or system admission.
- For private data use private staging, antivirus, DLP and scoped authenticated connectors.
- GitHub Actions artifacts expire; the retained Git source and approved content-addressed library records are the durable references.

## ChatGPT File Library boundary
`library/` is the **VAIXLNS repository source library**, not ChatGPT's personal File Library. Chat uploads, desktop folders and Drive folders do not automatically emit GitHub push events; a separately authorized forwarder is needed to submit them.

## Source of truth
Respect `registry/omega/omega-000-master-index.json`, `registry/indexes/zero-loss-index-taxonomy.v1.json`, `scripts/build_zero_loss_index.py`, and `registry/repository-orchestration/UNIVERSAL_ADMISSION_GATE_V1.md`. Do not mutate the canonical index without independent verification and approval.
