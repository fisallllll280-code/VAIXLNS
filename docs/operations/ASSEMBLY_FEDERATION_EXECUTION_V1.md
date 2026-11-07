# VAIXLNS — Assembly Federation Execution V1

Status: **PROPOSED / READ-ONLY PREFLIGHT** (not a production deployment).

This change introduces eight non-destructive assembly groups (G01–G08), a machine-readable registry, a deterministic validator, adversarial regression tests and a scheduled GitHub Actions preflight. Repository names are inventory references, **not evidence of running integrations**. Existing histories, ownership, canonical authority and system identities remain separate.

## Pipeline

Discover source → preserve immutable revision/lineage → classify assembly → reconcile identity → check contracts/dependencies/licensing → sandbox build/tests → independent evidence/provenance → governance admission → authorized deployment → health monitoring/rollback.

The current implementation performs **only local manifest validation**. It does not fetch external repository sources, create branches in other repositories, merge code, provision cloud resources, or publish. The six-hour schedule is a best-effort GitHub Actions trigger, not an always-on service guarantee.

## Ω∞ archive boundary

The previously reported 74 files, 2,897 line references, 20 candidate terms and 41 sections are recorded as **user-reported, NOT_REPRODUCED**. The ZIP/source archive and SHA-256 manifest were not attached to this change. Do not claim PASS or complete recovery until source files are available and hashes are independently recomputed. The 0001–2750 atomic recovery remains OPEN.

## Admission requirements

- G02 remains IDENTITY_HOLD until VLNS/NAXLNS and NEXNET/NEXENT identity evidence is reviewed.
- No destructive merge, no silent source overwrite and no auto-publish.
- Independent reproducible tests and exact revision-bound evidence are required for VERIFIED.
- Deployment must be separately authorized with scoped credentials and rollback.

## Run locally

```bash
python scripts/validate_assembly_federation.py
python -m unittest discover -s tests -p 'test_assembly_federation.py' -v
```
