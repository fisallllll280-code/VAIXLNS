# VX ONE System Loader — Federation Contract v1

**Status:** PROPOSED / CONTRACT ONLY  
**Canonical authority:** VAIXLNS  
**Protected sources:** `project.genome` and `Ω.000` are unchanged and out of scope for this change.

## Responsibility

VAIXLNS owns the canonical meaning of system identity, source provenance, governance, allowed lifecycle transitions, evidence classification, and admission requirements. It does not implement a second installer or boot manager.

The executable candidate currently lives in the isolated `VAIXLNS-unified` branch `feat/vx-one-system-loader-v1-20261031`, PR #71. The shared manifest contract is `schemas/vx-system-manifest.v1.schema.json` in that candidate.

## Required lifecycle

`DISCOVER → IDENTIFY → SCAN → COMPATIBILITY_CHECK → VERIFY_SOURCE → VERIFY_HASH → VERIFY_SIGNATURE → HUMAN_APPROVAL → STAGE → BOOT_OBSERVATION → POST_BOOT_VERIFY`

## Required invariants

- Unknown or ambiguous system identity is quarantined.
- A repository manifest is a declaration, not proof that an artifact exists or is authentic.
- SHA-256 verifies content equality, not publisher identity.
- Signature verification must use independently pinned and revocable trust roots.
- Secure Boot and TPM Measured Boot are distinct controls and must not be conflated.
- No silent Secure Boot disablement, firmware-key enrollment, TPM reset, partitioning, disk formatting, or reboot.
- Installation and destructive device operations require explicit target-specific approval.
- No claim of BOOTED or VERIFIED without device-observed evidence.

## Evidence states

Use `PROPOSED`, `SPECIFIED`, `IMPLEMENTED`, `RUNNING`, `OBSERVED`, and `VERIFIED` distinctly. Missing access is `NOT_OBSERVED`, not proof of absence.

## Scope

This contract adds no production downloader, installer, firmware adapter, device integration, or canonical registry write. It preserves the no-loss rule and does not modify `project.genome` or `Ω.000`.
