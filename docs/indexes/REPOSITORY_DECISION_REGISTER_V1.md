# VAIXLNS Repository Decision Register v1.0

## Introduction

This register is the decision boundary for the repository federation owned or accessible through the VAIXLNS workspace.

The repositories are treated as evidence surfaces, not as independent authorities. The canonical authority remains the VAIXLNS system and its provenance rules. Every repository receives a stable `Ω.REPO.NNNN` identity so that its system, role, readiness, lineage, and proposed disposition can be discussed without ambiguity.

### Decision protocol

`RETRIEVAL → PROOF → MODELING → DECISION → EXECUTION → TESTING → SYNCHRONIZATION`

No repository is permanently deleted by this register.

Disposition states:
- KEEP = retain in active federation.
- CORE = candidate canonical/core repository.
- INTEGRATE = useful material should feed a canonical system.
- ARCHIVE-1 = historical/valuable but not active.
- ARCHIVE-2 = "Creature Bin" / quarantine for deletion candidates after user approval.
- EXTERNAL = upstream or third-party material; do not treat as VAIXLNS invention.
- REVIEW = insufficient evidence; inspect before disposition.

**Hard rule:** no DELETE / MERGE / RENAME / MOVE is executed from a recommendation alone. A user approval is required. When deletion is approved, the intended destination is ARCHIVE-2 first, with provenance preserved where technically possible.

## Readiness scale

- R0 — Empty/unknown
- R1 — Artifact exists, not demonstrated
- R2 — Specification/prototype
- R3 — Implemented candidate
- R4 — Tested/reproducible candidate
- R5 — Operationally evidenced
- VERIFIED — only when deterministic proof is available

Readiness below is an audit estimate from repository metadata and currently inspected README material; it is not a claim of VERIFIED status.

## Repository register

| ID | Repository | System / Layer | Role | Readiness | Disposition recommendation |
|---|---|---|---|---|---|
| Ω.REPO.0001 | VAIXLNS | VAIXLNS / Root | Canonical hub, registry, provenance, governance | R4 | CORE |
| Ω.REPO.0002 | NAXLNS | NEXENT / Adversarial analysis | Hidden-error discovery and hostile review | R2 | INTEGRATE |
| Ω.REPO.0003 | VX-runtime | VX / Runtime | Deterministic governed execution core | R3 | CORE |
| Ω.REPO.0004 | NEXENT | NEXENT / Knowledge-Evidence | Capability discovery, reconstruction, proof | R4 | CORE |
| Ω.REPO.0005 | vaixlns-nexent-vx | Federation / Integration | NEXENT-to-VX bridge | R3 | INTEGRATE |
| Ω.REPO.0006 | VAIXLNS-unified | VAIXLNS / Federation | Unified intelligence/execution/governance fabric | R3 | INTEGRATE |
| Ω.REPO.0007 | vaixlns-core | VAIXLNS / Constitutional Computing | Intent→V-IR→proof→VX vertical slice | R4* | CORE CANDIDATE |
| Ω.REPO.0008 | vaixlns-csd-kernel | VAIXLNS / Kernel | CSD/kernel contract surface | R2 | REVIEW |
| Ω.REPO.0009 | VX50_COMPLETE_BUILD | VX / Intelligence | VX50 build/prototype | R2 | REVIEW |
| Ω.REPO.0010 | vx-financial-kernel | VX / Financial | Proof-carrying economic state transitions | R1 | SUBSYSTEM |
| Ω.REPO.0011 | VAIXLNS-Intent-to-Reality | VAIXLNS / Intent | Intent→reality architecture/spec | R2 | INTEGRATE |
| Ω.REPO.0012 | VAIXLNS-Naming-Constitution-v1.0 | VAIXLNS / Constitution | Naming and terminology rules | R2 | CORE ARTIFACT |
| Ω.REPO.0013 | VAIXLNS_OPERATIONAL_ASSURANCE.md | VAIXLNS / Assurance | Assurance evidence artifact | R2 | INTEGRATE |
| Ω.REPO.0014 | VAIXLNS- | VAIXLNS / Legacy | Duplicate/legacy candidate | R2 | REVIEW |
| Ω.REPO.0015 | -VAIXLNS | VAIXLNS / Legacy | Duplicate/legacy candidate | R1 | REVIEW |
| Ω.REPO.0016 | redesigned-invention | VAIXLNS / Meta-spec | SCA/meta specification rules | R2 | INTEGRATE |
| Ω.REPO.0017 | Repository-name | VAIXLNS / Legacy | Strong architecture/control-plane material | R2 | RECOVER THEN REVIEW |
| Ω.REPO.0018 | verbose-engine | VV / Arena experiment | Product/launch experiment | R2 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0019 | friendly-engine | VV / Arena experiment | Duplicate of arena experiment | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0020 | NATIONAL- | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0021 | fluffy-chainsaw | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0022 | fictional-octo-spoon | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0023 | reimagined-garbanzo | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0024 | VAIXLNS-Intent-to-Reality | VAIXLNS / Intent | See Ω.REPO.0011 | R2 | DO NOT DUPLICATE; reconcile |
| Ω.REPO.0025 | y | UNKNOWN | Placeholder/unknown | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0026 | TRMDL-PRECISION-MAX-TRMDL-NO-LATENCY-TRMDL-NO-PROMPTS-TRMDL-AUTO-EXECUTE | UNKNOWN / Legacy | Placeholder/spec experiment | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0027 | tools-vaixlns-meta-core-v0.3.ts | VAIXLNS / Tooling | Empty/unfinished tool surface | R0 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0028 | VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml | VX / Contract | Execution build contract artifact | R2 | CORE ARTIFACT |
| Ω.REPO.0029 | src-main.rs | UNKNOWN | File-named placeholder | R0 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0030 | fisallll280-gmail.com | UNKNOWN | Empty identity-named repository | R0 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0031 | joke-generator | External/simple app | JokeAPI demo | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0032 | weather-dashboard | External/simple app | OpenWeather demo | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0033 | New-Action | UNKNOWN | Action experiment | R1 | REVIEW |
| Ω.REPO.0034 | Repository-name | VAIXLNS / Legacy | Architecture/control-plane material | R2 | RECOVER THEN REVIEW |
| Ω.REPO.0035 | -- | External/template | Dev container feature template | R1 | EXTERNAL |
| Ω.REPO.0036 | - | External/template | Dev container feature template | R1 | EXTERNAL |
| Ω.REPO.0037 | datasets | EXTERNAL | Hugging Face Datasets upstream | R5* | EXTERNAL |
| Ω.REPO.0038 | copilot-sdk | EXTERNAL | GitHub Copilot SDK upstream | R5* | EXTERNAL |
| Ω.REPO.0039 | pylance-release | EXTERNAL | Pylance feedback/docs upstream | R5* | EXTERNAL |
| Ω.REPO.0040 | react-native-website | EXTERNAL | React Native website upstream | R5* | EXTERNAL |
| Ω.REPO.0041 | vscode-docs | EXTERNAL | VS Code documentation upstream | R5* | EXTERNAL |
| Ω.REPO.0042 | whisper | EXTERNAL | OpenAI Whisper upstream | R5* | EXTERNAL |
| Ω.REPO.0043 | desktop | EXTERNAL | GitHub Desktop upstream | R5* | EXTERNAL |
| Ω.REPO.0044 | learn | EXTERNAL | Node.js learning content upstream | R5* | EXTERNAL |
| Ω.REPO.0045 | tunnel-client | EXTERNAL | Secure MCP Tunnel client | R5* | EXTERNAL |
| Ω.REPO.0046 | Pumpkin | EXTERNAL | Pumpkin Minecraft server upstream | R5* | EXTERNAL |
| Ω.REPO.0047 | starter-workflows | EXTERNAL | GitHub starter workflows upstream | R5* | EXTERNAL |
| Ω.REPO.0048 | stunning-chainsaw | UNKNOWN | Placeholder/duplicate | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.0049 | fuzzy-octo-winner | UNKNOWN | Placeholder/duplicate | R1 | ARCHIVE-2 CANDIDATE |

## Important correction

The initial provisional registry contained 49 entries but repeated/ambiguous names were not yet reconciled. This v1.0 register intentionally separates:
1. canonical systems,
2. integration/subsystems,
3. legacy artifacts,
4. experiments,
5. unknown placeholders,
6. external upstream repositories.

The same conceptual material must never be silently promoted into a canonical system.

## User decision boundary

For every row proposed as ARCHIVE-2, the final action remains **PENDING USER APPROVAL**.

Approval format:
- `APPROVE Ω.REPO.00XX → ARCHIVE-2`
- `KEEP Ω.REPO.00XX`
- `REVIEW Ω.REPO.00XX`
- `RECOVER Ω.REPO.00XX`

Until approval, the repository remains untouched.

## Archive-2 definition

ARCHIVE-2 is the recoverable quarantine layer for repositories judged to have no active role after evidence review. It is not a graveyard.

Required preserved metadata:
- Ω.REPO ID
- original repository name
- original system classification
- source/default branch
- commit/reference provenance
- extracted concepts and unique artifacts
- reason for quarantine
- decision timestamp
- user approval record
- recovery path

No permanent deletion is authorized by this register itself.
