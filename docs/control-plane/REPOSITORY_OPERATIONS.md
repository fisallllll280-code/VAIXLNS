# Repository Operations Control Plane

## Scope

This document defines the complete governed operation path for the VAIXLNS repository federation.

```
DISCOVER
  ↓
CLASSIFY
  ↓
INDEX
  ↓
PLAN
  ↓
GENERATE / MODIFY
  ↓
TEST
  ↓
REVIEW
  ↓
PROVE
  ↓
PROPOSE PR
  ↓
MERGE GATE
  ↓
OBSERVE
  ↓
RECOVER
```

## Federated repositories

- VAIXLNS — canonical governance and federation registry
- NEXENT — discovery, architecture search, research and provider coordination
- VAIXLNS-unified — executable projection
- vaixlns-core — core reference
- vaixlns-csd-kernel — specialized kernel
- VAIXLNS-Intent-to-Reality — intent boundary
- VX-runtime — runtime surface
- VX50_COMPLETE_BUILD — build surface

## Required controls

Every automated mutation MUST carry:

- target repository
- target ref
- operation
- actor/provider
- authority = NONE for external AI workers
- plan/artifact identifier
- test result
- evidence
- review/approval state
- recovery path

## Safety boundary

The Fable repository is an external reference. It can inform an agent worker but cannot silently alter canonical policy, permissions, credentials, branch protection, or governance.

## Completion criteria

A repository operation is complete only when:

1. files are changed through a traceable commit/PR;
2. relevant automated checks pass;
3. review state is recorded;
4. generated artifacts are reproducible;
5. rollback/recovery is defined;
6. canonical registries are updated where applicable.
