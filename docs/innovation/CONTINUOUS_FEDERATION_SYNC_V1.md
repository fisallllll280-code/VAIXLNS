# VAIXLNS Ω — Continuous Federation Sync & Innovation Admission Pipeline v1

**State:** REVIEW / IMPLEMENTATION-CANDIDATE. Tests and CI must be inspected. NOT ADMITTED. No claim that all accounts, cloud services or model runtimes are connected.

## Architecture and data flow

    Five allowlisted public GitHub repositories
        ↓ read-only, pinned baseline SHA + HEAD SHA
    Continuous Federation Sync
        ├── federation-sync.v1.json          (source observation)
        ├── all-changes.v1.jsonl              (all changed paths with action)
        ├── innovation-intake-queue.v1.json   (review-only innovation candidates)
        └── sync-receipt.v1.json              (projection SHA-256 checks)
        ↓
    Existing Zero-Loss Index + Innovation Operation Index
        ↓
    GitHub CI evidence → Independent review → Optional authorized promotion

## Sources and ownership

| Source | Scope | Interpretation |
|---|---|---|
| VAIXLNS | Public metadata only | Canonical control-plane |
| VAIXLNS-unified | Public metadata only | Execution/research runtime projection |
| VX-runtime | Public metadata only | Runtime and SCCK |
| NEXENT | Public metadata only | Independent research/discovery |
| vx-agents-fabric | Public metadata only | Agent support |
| NAXLNS | Excluded (private) | Requires explicit private access; not equated to VLNS |
| Zapier, Drive, ChatGPT accounts | Not connected | Require authorized external adapters |

The system reuses rather than replaces scripts/build_zero_loss_index.py, scripts/capture_pinned_repo_snapshots.py, tools/build_innovation_operation_index.py, tools/validate_innovation_operation_index.py, scripts/federation_integrity_gate.py, and the continuity manifest. It does not edit project.genome or Ω.000.

## Running and testing

Offline deterministic regression:

    python -m unittest discover -s tests -p 'test_continuous_federation_sync.py' -v

Live public metadata observation:

    python scripts/continuous_federation_sync.py --strict --config registry/federation/continuous-sync-sources.v1.json --out build/federation-sync

The GitHub workflow also checks the Innovation Operation Index, existing Zero-Loss tests and federation integrity, then uploads a source-bound evidence artifact. After merge, the scheduled workflow runs daily at 04:31 UTC, and workflow_dispatch is available. A PR uses read-only permissions and runs no trusted-source checkout of third-party pull-request code.

## Trust and evidence

An observed Git blob SHA is a Git object identifier, NOT the source's SHA-256 raw content digest. This engine does not download or move the actual source bytes. Full source-byte capture, LFS and submodule verification, recovery/restore remain the responsibility of the existing pinned snapshot tool.

An innovation filename creates REVIEW_REQUIRED only; it cannot establish originality, formal proof, live execution, approved publisher, verified model response, or canonical promotion. The CI receipt does not grant authority. GitHub API errors, private sources, incomplete compares, rate limits, and truncated trees remain explicit blockers.

The recorded historic quantities 408/28/2750 are claims under separate reconciliation; no synthetic legacy IDs are created. VLNS/NAXLNS and NEXNET/NEXENT identities remain separate until positively established.

## Integration stages still blocked

External Zapier and Google accounts, personal ChatGPT File Library, private GitHub repositories, signed SCCK production execution, iOS deployment, all-branch history, live model serving, repository merges and canonical registry writes require separate authorized implementations and evidence. Do not claim the project is production-complete from this CI.

## Sources

- GitHub secure workflow guidance: https://docs.github.com/en/actions/reference/security/secure-use
- GitHub repository dispatch: https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event
- Zapier Webhooks: https://help.zapier.com/hc/en-us/articles/8496288690317-Trigger-Zaps-from-webhooks
