# VX Autonomous Build Policy — Zero External Spend / Release Approval

Status: FOUNDER_APPROVED_POLICY; NOT TECHNICALLY ENFORCED
Date: 2026-10-20
Scope: VAIXLNS, VAIXLNS-unified, VX-runtime, NEXENT and admissible indexed capabilities.
Authority: project.genome::v1.0.0 → Ω.000. This document is a non-canonical operational policy record, not an amendment to either source.

## Approved constraints

1. Autonomous discovery, indexing, planning, coding and testing may occur only in isolated feature branches or sandbox workspaces, and only after capability identity, authorization and resource checks.
2. External spend cap: SAR 0. Any nonzero charge, paid API invocation, promotion budget, subscription, purchasing, provisioning with fees, or financial commitment requires separate explicit founder approval before action.
3. Every release requires explicit founder approval: this includes public app/site deployment, package publishing, marketplace listings and updates. No standing approval or inferred consent.
4. No automatic merge to `main`, no canonical promotion, and no changes to `project.genome` or `registry/omega/omega-000-master-index.json` without explicit approval.
5. No financial transfers, discretionary trading, custody operations, payments, paid advertisements, unsolicited outbound messaging, or production access without specifically authorized and tested controls.
6. Unregistered tools, unknown identities, missing permission proofs, missing source provenance, unverified CI, and ambiguous costs are HOLD/DENY, never assumed safe.
7. Workers cannot self-report VERIFIED. Independent tests, immutable execution/source revision receipts, reproduction and governance admission remain distinct.
8. Read-only index recovery must retain legacy IDs and source digests; unknown coverage must remain UNMAPPED or UNKNOWN. No speculative claims of complete recovery.

## Readiness observations (2026-10-20, repository source inspection)

- VAIXLNS, VAIXLNS-unified, VX-runtime and NEXENT were accessible through the installed GitHub connector, which reported repository pull/push/admin permissions. Those permissions do not prove branch protection, deployed services, environment rules, external account authority, or CI pass.
- VAIXLNS Ω.000 lists VX as PARTIAL and names VAIXLNS-unified as its canonical owner.
- The VAIXLNS master workflow orchestrator describes PLANNER DESIGN with execution authorization disabled.
- VX-runtime README describes an execution contract and explicitly says runtime implementation needs executable verification.
- Published VX stage release checklist still requires identity, authentication, routing, isolation, rollback, independent evidence and human authorization.

## Promotion gates

Gate 0: capture repository revision, capability inventory and index coverage.
Gate 1: authorization, network/tool allowlist, resource isolation and no-cost evidence.
Gate 2: bounded build on an isolated branch with no production credentials.
Gate 3: static checks, unit/integration tests, adverse-path and replay/recovery evidence.
Gate 4: independent verification and artifact/source hashes.
Gate 5: founder authorization for EACH release; verify deployment target and rollback before any publication.
Gate 6: post-release monitoring, economic metrics and reversible improvement proposals.

Default for any missing gate: HOLD. No publish, no charge, no main merge.

## Next implementation slice — not yet executed

Implement a read-only source-bound opportunity intake prototype, with candidate statuses and evidence receipts, inside the existing canonical owner after inspection of matching code. Test with synthetic fixtures and report measured results. No external APIs requiring payment, social posting, or production deployment.

## Enforcement evidence required

This policy document by itself does not block GitHub administrators, deployment credentials or external billing. Before enabling automation, separately implement and test branch and environment protections, release approval mechanism, zero-spend tool policy, budget telemetry, and workflow permissions. Record a failing negative test for unauthorized publishing and for any unknown-cost action.
