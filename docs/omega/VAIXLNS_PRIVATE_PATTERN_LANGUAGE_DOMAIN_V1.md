# VAIXLNS Pattern-Bound Private Language Domain V1

**Status:** IMPLEMENTED / CONFORMANCE PENDING
**Canonical context:** project.genome::v1.0.0 / Ω0_GENESIS_CORE / Ω.000

## Boundary

A private language is a component of a Pattern Genome, not a component of the general VX runtime.

The Pattern Genome stores only an opaque binding, provenance, security policy, capability interface, and a hash of the private language genome. The language source itself remains in an external secret domain.

## Pattern structure

The model is:

```
Pattern
├── Identity
├── Intent
├── Architecture
├── Behavior
├── Agents
├── Tools
├── Security
├── Verification
├── Failure / Recovery
└── Private Language Genome
    ├── Syntax
    ├── Semantics
    ├── Grammar
    ├── Transformation
    ├── Security
    └── Verification
```

The six dimensions are represented as preserved fabric metadata. The source is not stored in Git, not exposed through the runtime, and not exposed to agents.

## Runtime boundary

VX and other consumers call a narrow capability interface:

```
PATTERN_REQUEST
→ AUTHORITY CHECK
→ PRIVATE PATTERN DOMAIN
→ CAPABILITY RESULT
→ VX
```

The consumer does not receive the private language source.

## Transfer / sale

A sale is a governed state transition, not an uncontrolled deletion:

```
ACTIVE
→ SEALED
→ TRANSFERRED
→ LOCKED / REVOKED
```

The agent executes the deprovisioning operation, but the agent cannot issue its own authority. The original provenance and hashes remain available to the authoritative domain.

The delivered artifact contains the pattern and the preserved language fabric metadata, but **does not contain the private language source**.

## Security invariants

- Private language source is never persisted in the VAIXLNS repository.
- Pattern consumers receive capability results, not language source.
- Agents cannot export or reconstruct the source through this boundary.
- Agents cannot self-authorize deprovisioning.
- Auto-repair cannot grant language authority.
- Revocation removes delivery access while preserving provenance.

## Evidence boundary

IMPLEMENTED means the reference code and tests exist. CONFORMANCE/VERIFIED requires successful reproducible execution and retained CI evidence.
