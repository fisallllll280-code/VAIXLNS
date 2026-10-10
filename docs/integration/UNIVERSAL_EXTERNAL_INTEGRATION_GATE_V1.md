# VAIXLNS — Universal External Integration Gate v1

**Scope:** every model, API, server, tool, connector, repository, or data
source that crosses into the VAIXLNS execution boundary.

## Mandatory lifecycle

```text
DISCOVER
  ↓
QUARANTINE
  ↓
IDENTITY + CONTRACT
  ↓
SANDBOX
  ↓
FUNCTIONAL TEST
  ↓
FAILURE / RECOVERY
  ↓
REPLAY
  ↓
INDEPENDENT VERIFICATION
  ↓
PROOF FRESHNESS
  ↓
CAUSAL IMPACT BUDGET
  ↓
EXPLICIT AUTHORITY
  ↓
ADMISSION
  ↓
RUNTIME
  ↓
CONTINUOUS REVALIDATION
```

No external integration is trusted because it is reachable, popular, known,
or already used elsewhere.

## Identity binding

An admission is bound to:
- integration identity
- endpoint
- capability set
- contract version
- dependency fingerprint
- environment fingerprint
- owner
- proof-package digest

Any material change invalidates the admission and returns the integration to
quarantine/reverification.

## Same innovation gate

External integrations reuse the same control semantics as innovations:
**SPEC → SANDBOX → TEST → EVIDENCE → FALSIFICATION → 3-way independent
verification → REPLAY → FRESH PROOF → ADMISSIBLE → explicit authority**.

The gate never converts ADMISSIBLE into CANONICAL automatically.

## Model-specific minimum controls

For external AI models, the proof package must cover:
- explicit capability allowlist
- data/prompt boundary
- output schema validation
- provenance/evidence capture
- egress/network restrictions
- resource and rate budget
- tool access policy
- version/model identity pinning
- failure/recovery behavior

## Runtime-server/API minimum controls

For external servers/APIs/connectors/tools:
- endpoint allowlist
- identity/authentication
- contract compatibility
- timeout/retry/circuit-breaker behavior
- data-classification boundary
- failure/recovery behavior
- replay or deterministic request/response evidence where applicable
- revocation path

## Non-regression

No README, registry entry, integration URL, or successful connectivity check
is operational proof. Runtime admission requires reproducible evidence.
