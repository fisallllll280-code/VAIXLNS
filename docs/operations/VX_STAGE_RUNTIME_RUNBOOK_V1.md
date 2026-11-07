# VX Stage Runtime Runbook V1

**Status:** SPECIFIED / OPERATIONAL BASELINE
**Scope:** one isolated VX stage instance behind the VX Federation Gate
**Reference command:** `python scripts/vx_stage_runtime.py stage-run --output stage-evidence.json`

## Objective

Validate the staged lifecycle before multiplying VX instances:

`identity → lease/health → signed request → authority-aware route → execution → evidence → failure isolation → recovery → re-route`

## Prerequisites

- Python 3.11+
- an approved repository revision
- isolated Stage environment
- runtime configuration supplied by the deployment environment
- no customer or deployment credentials committed to source control

## Golden Stage Run

Run:

`python scripts/vx_stage_runtime.py stage-run --output stage-evidence.json`

Acceptance:

- one VX stage instance registers;
- heartbeat establishes ACTIVE state;
- request authentication validates;
- capability and authority route succeeds;
- controlled isolation blocks routing;
- recovery restores authorized routing;
- evidence JSON is emitted.

## Runtime operations

### Start
Start the Stage instance with the approved configuration and register it through the Federation Gate.

### Health
Heartbeat/lease state is observed before privileged routing.

### Routing
A route is accepted only when capability and authority both match.

### Isolation
Unexpected behavior changes the instance to ISOLATED and blocks privileged routing.

### Recovery
Recover only from an approved revision and re-run the golden scenario.

## Credential handling

Deployment credentials belong to the Stage secret store or workload identity system. The repository contains only interfaces and conformance fixtures.

The default signing material in the reference harness is for deterministic tests only.

## Rollback

Rollback to the last revision that passed the canonical control gates and Stage acceptance suite. Preserve the failed evidence and reference the rollback revision.

## Production promotion

Stage evidence is not production evidence.

Promotion additionally requires real deployment evidence for workload identity, channel protection, credential rotation, durable telemetry, resource limits, sustained load, dependency failure behavior, independent security assessment, and approved rollback.

## Evidence

Link every Stage run to:

- commit/revision;
- Stage configuration identifier;
- run identifier;
- instance identifier;
- route decisions;
- isolation/recovery events;
- provenance hashes;
- verification disposition.
