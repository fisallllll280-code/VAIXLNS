# AI Agent Provider Fabric

## Canonical placement

External AI providers are **workers behind an adapter**, not owners of VAIXLNS authority.

```text
NEXENT
  ↓
Agent Task Contract
  ↓
Provider Adapter
  ↓
Model Worker
  ↓
Artifact + Evidence
  ↓
Test / Verify / Proof
  ↓
Governance Gate
  ↓
VAIXLNS Adoption
```

## Anthropic / Fable lane

The supplied reference URL is `https://claude-fable-5.md`.

The exact markdown file was not embedded into the repository because the URL was not retrievable through the current connector path. The integration therefore stores only a provider contract and public model identifiers, not the contents of a possibly unstable or private prompt file.

Configured model identifiers:

- `claude-fable-5`
- `claude-fable-5-1` (newer Fable 5.1 model identifier)

Intended role:

- repository analysis
- architecture engineering
- code generation and refactoring
- test generation
- research and long-horizon engineering work

The provider has **no canonical authority**. It must return artifacts/evidence to the NEXENT/VAIXLNS pipeline for verification and governance.

## Contract

```text
DISCOVER → UNDERSTAND → PLAN → MODIFY → TEST → REVIEW → PROVE → GOVERN → COMMIT → OBSERVE → RECOVER
```

The contract is provider-neutral so another model can replace Fable without changing VAIXLNS semantics.


## External Fable repository

Upstream reference: `A3S-Lab/claude-fable-5`.

The repository contains `claude-fable-5.md`, but the file is treated as **external reference data**. It is never promoted automatically into VAIXLNS policy, permissions, credentials, or execution authority.

Control actions must pass through the Fable Control Plane and repository governance gates.

Source: https://github.com/A3S-Lab/claude-fable-5
