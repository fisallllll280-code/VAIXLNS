# VAIXLNS Automatic File Intake & Library v1

**State:** Implementation proposal / read-only evidence automation. **Not canonical admission.**

## Purpose
Automatically inventory files submitted to `intake/inbox/`, preserve their source names and SHA-256, classify likely destination, and produce reviewable content-addressed library metadata without automatically rewriting the canonical project or any other repository.

## Source routing
- Indexes → VAIXLNS / docs/indexes/intake
- Innovations → VAIXLNS / docs/innovation/intake
- Model registries → VAIXLNS / registry/models/intake
- Agents/minds → VAIXLNS / docs/agents/intake
- NEXENT research → NEXENT / docs/research/intake
- VX kernel/runtime → VX-runtime / docs/intake
- Proof and evidence → VAIXLNS / registry/evidence/intake
- Archive → VAIXLNS / archive/source/intake
- Unknown → UNCLASSIFIED / review; no destination

An identified destination is a **proposal**, not an actual cross-repository write or promotion.

## Workflows
After merging this change, a push to main touching `intake/inbox/**` triggers `.github/workflows/auto-intake.yml`. PRs modifying the intake or its implementation also trigger tests. A periodic six-hour check and manual dispatch are supported. The workflow has `contents: read` only and stores routing manifests as GitHub Actions artifacts. It may run the existing `scripts/build_zero_loss_index.py` generator read-only.

Generated artifacts include:
- `build/auto-intake/routing-manifest.v1.json`: original path, SHA-256, proposed repository/path, disposition, safety flags.
- `build/auto-intake/library-index.v1.jsonl`: source-by-source intake records.
- existing `build/zero-loss-index/**` outputs if the builder is present.

For exact-byte **local staging** after explicit review:
```bash
python tools/auto_intake.py --root . --inbox intake/inbox --out build/auto-intake --include-payloads
```
This creates `build/auto-intake/library/objects/<digest-prefix>/<sha256>` and `build/auto-intake/proposals/<repo>/<suggested-path>`. The workflow deliberately does **not** upload these raw payloads or commit them to canonical paths.

## Invariants
1. Original uploaded file is never rewritten or deleted by classifier.
2. Identical byte hashes share one object but source identities remain separate.
3. Source material is never executed.
4. No automated `IMPLEMENTED`, `VERIFIED` or `ADMITTED` status.
5. Secret-like files, shortcuts and binaries are blocked or held; binary documents require human inspection.
6. No cross-repository writes without a separate authorized app/token and a reviewed PR.
7. Repository presence and artifact production are not live model runtime evidence.

## Security boundary
VAIXLNS is a public GitHub repository. Do not submit credentials or confidential files to public `intake/inbox`. The secret scanner is heuristic; it is not DLP and cannot detect private content embedded in PDF/ZIP/DOCX. Use a private intake service with identity, antivirus, content policy, encryption and audit for confidential sources.

## File Library integration boundary
This mechanism creates a **VAIXLNS library index**, not a write integration into ChatGPT File Library. Chat uploads are not automatically mirrored to GitHub. Desktop folders, Drive and chat uploads require separately authorized connectors or forwarders.

## Source of truth
- `registry/omega/omega-000-master-index.json`
- `registry/indexes/zero-loss-index-taxonomy.v1.json`
- `scripts/build_zero_loss_index.py`
- `registry/repository-orchestration/UNIVERSAL_ADMISSION_GATE_V1.md`

## Local verification
```bash
python -m unittest discover -s tests -p 'test_auto_intake.py' -v
python tools/auto_intake.py --root . --inbox intake/inbox --out build/auto-intake
```
The actual GitHub workflow and its result must be inspected independently after approval/merge. No tests are marked PASS without execution evidence.
