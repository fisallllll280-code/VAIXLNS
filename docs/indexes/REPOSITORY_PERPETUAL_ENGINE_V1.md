# VAIXLNS Repository Perpetual Engine v1

**State:** CANONICAL / OPERATIONAL DESIGN  
**Snapshot:** 2026-09-25

## Purpose

Turn the GitHub federation from a passive collection of repositories into a governed execution surface for runtime operation, engineering development, innovation incubation, verification, evidence, repository creation and continuous synchronization with the VAIXLNS Canon.

## Core loop

~~~text
CANON
  ↓
REPOSITORY MANIFEST
  ↓
DISCOVER → CLASSIFY → GAP DETECT
  ↓
PLAN
  ├─ existing repository → inspect / test / develop
  └─ missing official repository → create from contract
  ↓
SEED
  ↓
BUILD → TEST → VERIFY
  ↓
EVIDENCE
  ↓
REGISTRY UPDATE
  ↓
NEXT PULSE
~~~

A pulse is an execution cycle. A pulse MUST be deterministic from the current manifest, repository inventory, evidence and policy.

## Repository classes

| Class | Function | Example |
|---|---|---|
| CANONICAL | architecture, lineage, registry, governance | VAIXLNS |
| DISCOVERY | search, synthesis, research, innovation discovery | NEXENT |
| RUNTIME | executable system surfaces | VAIXLNS-unified |
| CORE | focused implementation kernels | vaixlns-core |
| SPECIALIZED | narrow kernels/contracts/tools | vaixlns-csd-kernel |
| BUILD | developer-facing build surfaces | VX50_COMPLETE_BUILD |
| ASSURANCE | evidence, conformance, operational assurance | VAIXLNS_OPERATIONAL_ASSURANCE.md |
| FACTORY | repository and system generation | proposed official family |
| LAB | experimental / innovation isolation | proposed official family |

## Perpetual operation policy

The engine is allowed to:

1. inventory accessible repositories;
2. compare them with the canonical repository manifest;
3. identify missing official repository surfaces;
4. create a missing repository only when the manifest marks auto_create: true and an administrative GitHub token is available;
5. seed new repositories with the canonical repository contract;
6. run verification/build workflows;
7. record evidence and lifecycle state;
8. keep proposals separate from canonical systems.

The engine MUST NOT:

- silently overwrite an unrelated repository;
- infer that a README proves implementation;
- merge historical repositories into canonical ones without lineage;
- promote an innovation from proposal to implementation without evidence;
- create unbounded repositories from free-form generated text.

## Continuous innovation lane

~~~text
NEXENT / Research
      ↓
Innovation Record
      ↓
Canonical fit check
      ↓
Factory candidate
      ↓
Isolated LAB repository
      ↓
Prototype
      ↓
Tests + evidence
      ↓
Conformance review
      ↓
Adoption / archive
~~~

This preserves the existing anti-duplication rule: overlapping capabilities become derived capability records rather than new top-level systems.

## Repository contract

Each official repository should expose, at minimum:

~~~text
README.md
VAIXLNS_REPOSITORY_CONTRACT.md
.github/workflows/
docs/
tests/              (when executable)
src/                (when executable)
registry/            (when registry-bearing)
~~~

The contract must declare: System ID, Family, Owner / authority boundary, Repository role, lifecycle state, input/output boundary, dependencies, verification command, evidence location, canonical lineage and innovation relationship.

## State vocabulary

Use the existing evidence discipline:

~~~text
VERIFIED
SPECIFIED
PARTIAL
MISSING
CONFLICT
PROPOSAL
~~~

## Safety and bounded autonomy

The perpetual engine is self-directing inside explicit boundaries, not unbounded. Repository creation is an administrative mutation and therefore requires a predeclared manifest entry and a token with permission to create repositories. Development remains evidence-driven.

## Source of truth

VAIXLNS remains the canonical architecture/registry authority. NEXENT remains the discovery/research authority. Runtime repositories implement contracts; code presence does not redefine canonical meaning.