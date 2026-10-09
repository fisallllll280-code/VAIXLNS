# ARC-X Ω Runtime Bootstrap v1

**Implementation slice:** deterministic repository retrieval, SHA-256 source manifest, EIR generation, integrity verification, and deterministic replay.
**Evidence state:** implementation code added; GitHub Actions result is the execution proof boundary.
**Semantic verification:** NOT CLAIMED.
**Canonical admission:** NOT REQUESTED; ARC-X cannot self-authorize.

## Start locally

Requirements: Python 3.10+ and Git. No third-party Python packages are required.

```bash
python scripts/arc_x_runtime.py reconstruct --root . --output .arcx
python scripts/arc_x_runtime.py verify --root . --output .arcx
python scripts/arc_x_runtime.py replay --root . --output .arcx
python scripts/arc_x_runtime.py inspect --output .arcx
```

To require an exact source commit:

```bash
python scripts/arc_x_runtime.py reconstruct --root . --output .arcx --revision "$(git rev-parse HEAD)"
```

## Outputs

- `source.receipt.json`: pinned Git revision, timestamp, sorted source manifest, per-file SHA-256, and aggregate content hash.
- `repository.model.json`: repository inventory and evidence-backed surface counts.
- `eir.json`: identity observation, file-surface observations, open identity gaps, and explicit authority/verification boundaries.
- `reconstruction.record.json`: stable reconstruction ID, EIR digest, and non-promoted evidence state.
- `verification.report.json`: integrity/reconstruction checks produced by `verify` or `replay`.

The scanner excludes Git metadata, generated/cache directories, symlinks, and common private-key/environment-secret files. It hashes file contents but does not copy file contents into the evidence bundle. Review the exclusion rules before using this as a compliance inventory.

## State and safety contract

The runtime reports `PARTIAL` for the reconstruction record. Passing receipt and replay checks proves only the integrity of the captured source inventory and EIR reconstruction. It does not prove application semantics, operational health, formal correctness, or production deployment.

It always keeps `authority_decision=PENDING`, `self_authority=false`, and `canonical_write_permitted=false`. No automated changes to `project.genome`, Ω.000, or canonical admission records occur.

A clean and successful CI run is required before classifying this slice as `VERIFIED` under the project's evidence model. Production status requires separately governed deployment and operational evidence.
