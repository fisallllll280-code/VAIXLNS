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

| ID | Repository | System / Layer | Role | Readiness | Recommendation |
|---|---|---|---|---|---|
| Ω.REPO.001 | VAIXLNS | VAIXLNS / Root | Canonical hub, registry, provenance, governance | R4 | CORE |
| Ω.REPO.002 | NEXENT | NEXENT / Knowledge-Evidence | Capability discovery, reconstruction, proof | R4 | CORE |
| Ω.REPO.003 | VX-runtime | VX / Runtime | Deterministic governed execution core | R3 | CORE |
| Ω.REPO.004 | vaixlns-nexent-vx | Federation / Integration | NEXENT-to-VX bridge | R3 | INTEGRATE |
| Ω.REPO.005 | VAIXLNS-unified | VAIXLNS / Federation | Unified intelligence/execution/governance fabric | R3 | INTEGRATE |
| Ω.REPO.006 | vaixlns-core | VAIXLNS / Constitutional Computing | Intent→V-IR→proof→VX vertical slice | R4* | CORE CANDIDATE |
| Ω.REPO.007 | vaixlns-csd-kernel | VAIXLNS / Kernel | CSD/kernel contract surface | R2 | REVIEW |
| Ω.REPO.008 | VX50_COMPLETE_BUILD | VX / Intelligence | VX50 build/prototype | R2 | REVIEW |
| Ω.REPO.009 | vx-financial-kernel | VX / Financial | Proof-carrying economic state transitions | R1 | SUBSYSTEM |
| Ω.REPO.010 | VAIXLNS-Intent-to-Reality | VAIXLNS / Intent | Intent→reality architecture/spec | R2 | INTEGRATE |
| Ω.REPO.011 | VAIXLNS-Naming-Constitution-v1.0 | VAIXLNS / Constitution | Naming and terminology rules | R2 | CORE ARTIFACT |
| Ω.REPO.012 | VAIXLNS_OPERATIONAL_ASSURANCE.md | VAIXLNS / Assurance | Assurance evidence artifact | R2 | INTEGRATE |
| Ω.REPO.013 | NAXLNS | NEXENT / Adversarial | Hostile analysis and hidden-error discovery | R2 | INTEGRATE |
| Ω.REPO.014 | redesigned-invention | VAIXLNS / Meta-spec | SCA/meta specification rules | R2 | INTEGRATE |
| Ω.REPO.015 | Repository-name | VAIXLNS / Legacy | Architecture/control-plane material | R2 | RECOVER THEN REVIEW |
| Ω.REPO.016 | VAIXLNS- | VAIXLNS / Legacy | Duplicate/legacy candidate | R2 | REVIEW |
| Ω.REPO.017 | -VAIXLNS | VAIXLNS / Legacy | Duplicate/legacy candidate | R1 | REVIEW |
| Ω.REPO.018 | tools-vaixlns-meta-core-v0.3.ts | VAIXLNS / Tooling | Empty/unfinished tool surface | R0 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.019 | VX_EXECUTION_BUILD_CONTRACT_V0_1.yaml | VX / Contract | Execution build contract artifact | R2 | CORE ARTIFACT |
| Ω.REPO.020 | datasets | EXTERNAL | Hugging Face Datasets upstream | R5* | EXTERNAL |
| Ω.REPO.021 | copilot-sdk | EXTERNAL | GitHub Copilot SDK upstream | R5* | EXTERNAL |
| Ω.REPO.022 | pylance-release | EXTERNAL | Pylance feedback/docs upstream | R5* | EXTERNAL |
| Ω.REPO.023 | react-native-website | EXTERNAL | React Native website upstream | R5* | EXTERNAL |
| Ω.REPO.024 | vscode-docs | EXTERNAL | VS Code documentation upstream | R5* | EXTERNAL |
| Ω.REPO.025 | whisper | EXTERNAL | OpenAI Whisper upstream | R5* | EXTERNAL |
| Ω.REPO.026 | desktop | EXTERNAL | GitHub Desktop upstream | R5* | EXTERNAL |
| Ω.REPO.027 | learn | EXTERNAL | Node.js learning content upstream | R5* | EXTERNAL |
| Ω.REPO.028 | tunnel-client | EXTERNAL | Secure MCP Tunnel client | R5* | EXTERNAL |
| Ω.REPO.029 | Pumpkin | EXTERNAL | Pumpkin Minecraft server upstream | R5* | EXTERNAL |
| Ω.REPO.030 | starter-workflows | EXTERNAL | GitHub starter workflows upstream | R5* | EXTERNAL |
| Ω.REPO.031 | - | EXTERNAL/TEMPLATE | Dev Container Features template | R1 | EXTERNAL |
| Ω.REPO.032 | -- | EXTERNAL/TEMPLATE | Dev Container Features template | R1 | EXTERNAL |
| Ω.REPO.033 | verbose-engine | VV / Arena experiment | Product/launch experiment | R2 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.034 | friendly-engine | VV / Arena experiment | Near-duplicate arena experiment | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.035 | NATIONAL- | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.036 | fluffy-chainsaw | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.037 | fictional-octo-spoon | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.038 | reimagined-garbanzo | VV / Arena experiment | Duplicate/experimental | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.039 | VAIXLNS-Intent-to-Reality | VAIXLNS / Intent | Duplicate of Ω.REPO.0010; reconcile lineage | R2 | RECONCILE |
| Ω.REPO.040 | y | UNKNOWN | Placeholder/unknown | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.041 | TRMDL-PRECISION-MAX-TRMDL-NO-LATENCY-TRMDL-NO-PROMPTS-TRMDL-AUTO-EXECUTE | UNKNOWN / Legacy | Placeholder/spec experiment | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.042 | fisallll280-gmail.com | UNKNOWN | Empty identity-named repository | R0 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.043 | joke-generator | EXPERIMENT | JokeAPI demo | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.044 | weather-dashboard | EXPERIMENT | OpenWeather demo | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.045 | New-Action | UNKNOWN | Action experiment | R1 | REVIEW |
| Ω.REPO.046 | src-main.rs | UNKNOWN | File-named placeholder | R0 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.047 | stunning-chainsaw | UNKNOWN | Placeholder/duplicate | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.048 | fuzzy-octo-winner | UNKNOWN | Placeholder/duplicate | R1 | ARCHIVE-2 CANDIDATE |
| Ω.REPO.049 | legendary-octo-fiesta | UNKNOWN/Research | Vision/innovation note; inspect before disposition | R1 | REVIEW |

## Duplicate / reconciliation flags

- **Ω.REPO.0010** and **Ω.REPO.0039** share the same repository name. They must be treated as a single identity only after repository metadata/ID comparison confirms whether they are actually distinct GitHub repositories; no merge or deletion is authorized yet.
- Several repositories contain copied or repeated VV Arena launch text. Their concepts must be extracted before any Archive-2 decision.
- External repositories are not counted as VAIXLNS inventions merely because they exist under the account.

## Archive-2 decision boundary

ARCHIVE-2 = recoverable quarantine, not permanent deletion.

A repository becomes an ARCHIVE-2 action only after:
1. unique knowledge is extracted;
2. lineage/provenance is recorded;
3. dependencies are checked;
4. no active canonical role remains;
5. the user explicitly approves the action.

Approval syntax:
- `APPROVE Ω.REPO.00XX → ARCHIVE-2`
- `KEEP Ω.REPO.00XX`
- `REVIEW Ω.REPO.00XX`
- `RECOVER Ω.REPO.00XX`

**No permanent deletion is authorized by this register.**
