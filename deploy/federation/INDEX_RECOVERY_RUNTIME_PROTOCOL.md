# VAIXLNS Index Recovery & Runtime Protocol v1.0

## Purpose

This protocol defines the server-side mechanism for reconstructing the VAIXLNS federation index from authoritative evidence and then starting only the runtime surfaces that pass deterministic admission.

The server is an **Index Recovery Engine + Runtime Admission Engine**, not a blind process launcher.

## Canonical Authority

- Golden Source: `project.genome::v1.0.0`
- Authority Anchor: `Ω0_GENESIS_CORE`
- Master Registry: `Ω.000`
- Federation authority: `VAIXLNS`

## Recovery Pipeline

```text
GitHub / Evidence Sources
        ↓
Deterministic Retrieval
        ↓
Source Revision + Hash Capture
        ↓
Schema / Identity Extraction
        ↓
Ω.000 Index Reconstruction
        ↓
Cross-System Reconciliation
        ↓
Admission Verification
        ↓
Dependency Resolution
        ↓
Startup
        ↓
Health + Tests
        ↓
Execution Evidence
        ↓
Runtime Registry / Ledger
```

## Four-System Runtime Boundary

| System | Repository surface | Role | Admission |
|---|---|---|---|
| VAIXLNS | `fisallllll280-code/VAIXLNS` | Control plane / canonical registry / recovery | Required |
| VLNS | `fisallllll280-code/NAXLNS` | Knowledge-discovery | Identity evidence required |
| VX | `fisallllll280-code/VX-runtime`, `VX50_COMPLETE_BUILD` | Execution runtime | Entrypoint evidence required |
| NEXNET | `fisallllll280-code/NEXENT` | Discovery network | Identity evidence required |

Repository identity MUST NOT be treated as system identity without evidence.

## Deterministic Recovery Rules

1. Retrieve the configured source revision; never use an implicit moving revision for a recovery record.
2. Capture source revision, content hashes, retrieval timestamp, and retrieval result.
3. Parse only declared schemas and recognized registry/index artifacts.
4. Preserve historical records; do not overwrite unknown or conflicting records.
5. Reconcile identity, role, dependency, and authority relationships.
6. Assign one of:
   - `VERIFIED`
   - `SPECIFIED`
   - `PARTIAL`
   - `MISSING`
   - `CONFLICT`
   - `PROPOSAL`
7. Runtime admission is blocked for a component whose required evidence is absent or contradictory.
8. A successful recovery does not imply successful runtime startup.
9. A successful startup does not imply verification of the system's semantic claims.
10. Every runtime transition writes an evidence record.

## Runtime State Machine

```text
DISCOVERED
   ↓
RETRIEVED
   ↓
RECONSTRUCTED
   ↓
RECONCILED
   ├── CONFLICT → BLOCKED
   ├── MISSING  → BLOCKED
   └── READY
        ↓
     ADMITTED
        ↓
     STARTING
        ↓
   HEALTH_CHECK
   ├── FAIL → BLOCKED
   └── PASS
        ↓
      TESTING
   ├── FAIL → BLOCKED
   └── PASS
        ↓
     RUNNING
        ↓
   OBSERVED / EVIDENCED
```

## Required Evidence Record

Each recovered or started component MUST produce an evidence record containing:

```yaml
system_id: string
repository: string
source_revision: string
content_hash: string
retrieval_timestamp: string
reconstruction_id: string
verification_state: VERIFIED|SPECIFIED|PARTIAL|MISSING|CONFLICT|PROPOSAL
dependency_resolution: PASS|FAIL|PENDING
startup_result: PASS|FAIL|PENDING
health_result: PASS|FAIL|PENDING
test_result: PASS|FAIL|PENDING
execution_evidence: string|null
previous_state: string|null
transition_reason: string
```

## Recovery Invariants

- No evidence → no `VERIFIED`.
- No deterministic source → no canonical reconstruction.
- No dependency resolution → no startup.
- No health result → no `RUNNING`.
- No test result → no verified execution.
- Conflicting identities are preserved and surfaced, never silently merged.
- Recovery is idempotent: the same source revision and inputs MUST produce the same reconstructed index.
- Runtime state is derived from evidence, not from README claims.

## Server Responsibilities

The server implementation should expose these logical operations:

- `recover_index`
- `inspect_recovery`
- `reconcile_federation`
- `admit_system`
- `start_system`
- `health_system`
- `run_system_tests`
- `capture_execution_evidence`
- `replay_recovery`

The concrete transport (HTTP/CLI/worker) is implementation-specific and MUST NOT change the protocol semantics.

ARC-X is the semantic compilation and reconstruction layer above these operations. It may prepare retrieval, EIR, proof obligations, and reconstruction artifacts, while admission and canonical authority remain governed by VAIXLNS.

## Current Status

This document is a **SPECIFICATION**. It defines the deterministic recovery and admission contract. It does not by itself prove that a production server has executed the protocol.
