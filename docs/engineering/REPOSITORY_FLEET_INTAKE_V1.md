# VAIXLNS Repository Fleet Intake v1

Status: IMPLEMENTED AS AN ISOLATED SOURCE CANDIDATE; CI REQUIRED; NOT VERIFIED UNTIL THE RUN COMPLETES.

## Purpose
Create a safe, repeatable local mirror of explicitly selected public repositories owned by the configured GitHub owner. This complements the existing Repository Genome, Global Research Runtime, NAXLNS analyzer, and Repository Pulse; it does not replace them.

## Modes
- Default: plan-only. Reads public GitHub repository metadata and emits a deterministic, digest-bound plan.
- Execute: requires both `--execute` and `VX_REPOSITORY_INTAKE_NETWORK_ENABLED=1`.
- Execution uses `git clone --mirror --no-hardlinks` into a separate local directory. It does not check out files, install dependencies, run candidate code, or write to remote repositories.
- Existing local mirrors are marked `EXISTS_NOT_MODIFIED`; no fetch, reset, prune, overwrite, or deletion is performed.
- Failed partial clones are preserved for inspection and are never automatically removed.
- Private repositories are skipped. This v1 does not accept credentials or access private repositories.

## Default core allowlist
VAIXLNS, VAIXLNS-unified, NEXENT, VX-runtime, vx-agents-fabric, vx-agents-system, NAXLNS, VX50_COMPLETE_BUILD, vaixlns-core, vaixlns-csd-kernel, VAIXLNS-Intent-to-Reality, vx-financial-kernel.

The default batch cap is 20 repositories and the default aggregate metadata size budget is 20,480 MB. Larger fleet imports must be explicitly split into reviewed batches. Archived repositories remain eligible but are labeled.

## Local verification
`python -m unittest discover -s tests -p 'test_repository_fleet_intake.py' -v`

## Explicit non-claims
This utility does not prove source correctness, license compatibility, runtime compatibility, complete LFS payload retrieval, or live integration. It records the declared repository license metadata for later legal review. It never modifies `project.genome` or `Ω.000`.
