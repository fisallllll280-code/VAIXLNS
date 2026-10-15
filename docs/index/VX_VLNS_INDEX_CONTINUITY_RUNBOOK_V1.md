# VX / VLNS Index Continuity Runbook v1

Status: REFERENCE REGISTERED — snapshot capture and restore verification are still pending.
Canonical authority: `project.genome::v1.0.0` → `Ω.000`.
Derived manifest: `registry/indexes/vx-vlns-continuity-manifest.v1.json`.

## Objective

Give the master-index workflow a durable, traceable reference to VX and VLNS so source history, revisions, evidence, and gaps are tracked instead of being silently lost. This runbook does not copy, rewrite, or promote canonical data.

## What is registered now

- **VX**: references to `fisallllll280-code/VX50_COMPLETE_BUILD` and `fisallllll280-code/VX-runtime`.
- **VLNS**: references to `fisallllll280-code/NAXLNS` and `fisallllll280-code/NEXENT`, with an explicit warning that NEXENT's VLNS specification is not proof of a standalone VLNS runtime.
- Required checkpoint fields, per-file SHA-256 hashes, immutable snapshot receipt, and restore-test gates.
- Unknown mappings and uncollected artifacts remain pending; no missing source is represented as an empty or complete copy.

## Snapshot protocol

For each source repository:

1. Pin and record the exact repository URL and full commit SHA. Never use a moving branch name as the only identity.
2. Capture the complete file inventory, including hidden files and submodule declarations. Record inaccessible paths, Git LFS pointers, submodules, generated files, and ignored files separately.
3. Preserve source bytes in a **derived, immutable snapshot location**. Do not overwrite the source repository or canonical index.
4. Compute SHA-256 for every captured file and a digest for the inventory/receipt. Record tool version, UTC timestamp, exit code, and snapshot location.
5. Verify each stored file against its recorded digest. Any mismatch is a hard failure.
6. Restore the snapshot into a clean temporary checkout and compare inventory and hashes. Mark the checkpoint PASS only after this restore test succeeds.
7. Append a new checkpoint for every later revision. Do not overwrite historical checkpoints; supersede them with a new record.

## Existing recovery workflow

From a pinned checkout of VAIXLNS, run the existing recovery workflow to rebuild and verify the derived zero-loss index bundle:

```bash
python -m unittest discover -s tests -p 'test_zero_loss_index.py' -v
python scripts/recover_zero_loss_index.py --root . --output-dir build/zero-loss-index
python scripts/omega_arena_audit.py --output build/omega-arena/audit-receipt.json
python -m unittest tests.test_omega_arena_audit -v
```

Retain the complete console logs and generated receipts. Inspect the recovery receipt and coverage report; a successful command is not proof of complete historical coverage when opaque or inaccessible sources remain.

## Stop conditions

Stop and report BLOCKED when repository identity is ambiguous, a pinned revision cannot be retrieved, an artifact or submodule is missing, a hash mismatches, a command fails, or a restore test differs. Do not silently repair source data, infer repository mappings, or weaken a validation gate.

## Current status and non-claims

- The continuity manifest is committed as a **derived reference manifest** on the Ω-Arena pull-request branch.
- Full VX/VLNS repository snapshots have **not** been captured by this change.
- Snapshot receipts, per-file hashes, and restore-test evidence remain pending.
- VLNS identity remains unverified; references do not prove that VX/VLNS runtimes are online or connected.
- The canonical `project.genome` and `Ω.000` files were not modified by this manifest addition.
