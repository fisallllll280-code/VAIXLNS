# Ω-RAC Executable v1.1

This directory is the executable closure of the Ω-RAC Canonical Specification v1.1.

## Scope

Ω-RAC computes assurance state; it does not mutate runtime state or issue governance decisions.

Implemented primitives:
- deterministic canonical input hashing;
- assurance reports with engine/policy/environment identity;
- unknown-budget quarantine;
- dependency closure and revalidation frontier;
- circular/recursive assurance rejection;
- unobservable obligation detection.

## Determinism boundary

Bit-identical reports require the same canonical tuple:

Claim + Evidence + Dependency Graph + Unknown Vector + Tolerance Policy +
Engine Version + Policy Version + Environment Fingerprint.

## Non-claims

Passing these tests does **not** prove the whole VAIXLNS system. The benchmark is an executable smoke/fixture layer for the implemented Ω-RAC core.
