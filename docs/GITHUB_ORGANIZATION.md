# VAIXLNS — GitHub Organization Standard

## Purpose
Keep the GitHub estate understandable, traceable, and safe to evolve.

## Repository classes
| Class | Purpose | Naming pattern |
|---|---|---|
| Root | Canonical documentation/index | `VAIXLNS` |
| Core | Core system components | `vaixlns-*` |
| Runtime | Execution/runtime components | `VX-*` |
| Unified | Integrated system | `VAIXLNS-unified` |
| Build | Build snapshots/workspaces | `VX*_*` |
| Governance | Constitutional/naming artifacts | `VAIXLNS-*-Constitution-*` |
| Contract | Machine-readable contracts | `VX_*_CONTRACT_*` |
| Assurance | Operational assurance | `VAIXLNS_OPERATIONAL_*` |

## Branch standard
- `main`: stable/default branch.
- `development`: active integration only where already established.
- Feature work: `feature/<scope>`.
- Fixes: `fix/<scope>`.
- Releases: `release/<version>`.

Do not rename an existing default branch merely for consistency; preserve compatibility and migrate deliberately.

## Commit standard
Use:
- `feat:` new capability
- `fix:` correction
- `docs:` documentation
- `refactor:` structural change without intended behavior change
- `test:` tests
- `build:` build/dependency changes
- `chore:` maintenance

## Pull-request standard
Every non-trivial change should identify:
1. Scope
2. Affected repositories/components
3. Compatibility impact
4. Validation performed
5. Rollback/recovery path

## Safety rule
Organization means classification and traceability first. Do not delete, overwrite, or merge repositories solely to make names look cleaner.
