# VAIXLNS Native-Language Windows Recovery Specification

**Status: PROPOSAL.** The syntax in this directory is an experimental draft, not a canonical VAIXLNS language specification. It must not be treated as executable until a parser/compiler and conformance tests exist.

## Design constraint

Describe the Windows boot/recovery system using VAIXLNS language layers rather than writing each subsystem as a conventional application in Python, C#, PowerShell, or Rust.

- **VSL** declares intent and requirements.
- **VML** declares formal models, constraints, and proof obligations.
- **VDL** declares typed facts, evidence, state, and device-profile records.
- **VOSL** declares orchestration, dependency order, capability limits, and approval gates.
- A future compiler maps these declarations into a canonical Semantic IR, then to a constrained VX runtime adapter. No direct host execution is permitted from a declaration.

The draft deliberately avoids pretending the language runtime already exists. It does not build a bootable ISO, invoke Windows tools, inspect disks, change BCD/registry settings, install drivers, or repair a machine.

## Files

- `windows-recovery.vsl`: intent and requirements.
- `recovery-model.vml`: invariants and proof obligations.
- `device-profiles.vdl`: device/recovery evidence data contracts.
- `recovery-orchestration.vosl`: gated plan and actor responsibilities.
- `conformance-gates.vsl`: compiler/runtime acceptance criteria.

## Required compiler gates

1. Parse and type-check every declaration with deterministic diagnostics.
2. Reject undeclared operations, ambient host access, unknown effects, and implicit authority.
3. Lower declarations to versioned Semantic IR with source-span provenance and content hashes.
4. Prove the generated plan is read-only unless a separately authorized policy explicitly permits a reviewed reversible action.
5. Require explicit human authorization, fresh evidence, rollback planning, and independent verification before any future mutation.
6. Preserve the distinction between PROPOSED, SPECIFIED, IMPLEMENTED, VERIFIED, AUTHORIZED, and EXECUTED.

## Canonical boundaries

No changes to `project.genome`, `Ω.000`, or canonical registries. This proposal cannot promote itself to canonical status. Syntax and semantics require review against the existing VAIXLNS language definitions before adoption.
