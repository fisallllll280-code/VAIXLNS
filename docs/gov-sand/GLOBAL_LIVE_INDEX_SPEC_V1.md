# VAIXLNS Global Live Index — specification

Status: PROPOSED (not live production).

## Purpose
Display independently verifiable evidence of what each AI subsystem actually performed, not just what documents claim. Support Arabic/English briefing for approved officials without privileged data exposure.

## Canonical architecture
VAIXLNS = registry, provenance, governance; NEXENT = discovery; VAIXLNS-unified = candidate execution surface; VX = agent/runtime interfaces; GOV/SAND = opt-in citizen service. Do not erase historical lineage or merge these entities silently.

## Typed event contract
Each event: event_id, system_id, capability_id, source_revision, UTC timestamp, action, result (PROPOSED/BUILT/TESTED/VERIFIED/DEPLOYED), evidence_uri, evidence_sha256, actor_role, reviewer, visibility (PUBLIC/RESTRICTED), expiry_date. No self-attestation qualifies as verified.

## Security and official displays
Public brief shows aggregate work and approved evidence only. Agency-specific view requires authenticated access and per-partner disclosure agreement. Do not disclose military records, personal loan/court files, secrets, or unverified partnership claims.

## Display
- System inventory and owning repository
- Historical lineage graph
- Verification timeline showing action and source
- Pilot eligibility and compliance gates
- AI agent performance snapshots only from reproducible benchmarks
- Funding allocation forecasts separate from confirmed financing
- One-click sanitized bilingual executive brief

## Activation roadmap
1. Schema, fixtures, validation CLI and automated CI (synthetic data).
2. Read-only static dashboard generated from validation output.
3. Authorized integration adapters with signed events and role-based access.
4. Official pilot, subject to agreements, cyber and privacy assessment.

## Failure rules
Never label a system operational based on a README; do not assert ministry endorsement or available banking APIs; no auto-reporting to government without authorization.
