# GOV CONNECT — Proposed case orchestration architecture (not a connected government system)
Status: DESIGN / 2026-10-27
Principle: citizen-initiated case, purpose-specific consent, least privilege, review, audited referrals. NO unauthorized APIs or scraping.

## Components
1. Intake portal: accessible Arabic UX, synthetic cases for demo, identity verification only with authorized provider.
2. Case workflow: finite states DRAFT -> CONSENTED -> VALIDATED -> HUMAN_REVIEW -> READY_FOR_REFERRAL -> SUBMITTED_BY_AUTHORIZED_CHANNEL -> RESPONSE_RECORDED -> CLOSED; explicit REJECTED/WITHDRAWN; no silent auto-send.
3. Consent vault: granular purposes, expiry, withdrawal, access log; legal basis review including cases where consent is not sole legal basis.
4. Evidence passport: document hashes, issuer, date, expiry, provenance, versioning, redacted exports; no actual citizens' records in repo.
5. Rules registry: per-agency **verified** rules; versioned policies with citations and validity dates. Proposed rules remain PENDING.
6. Integration gateway: per-partner adapter, allowlist, mutual authentication, encryption in transit, retries/idempotency, data minimization, audit; DISABLED until signed agreements and credentials are provisioned.
7. Military service desk: case-level opt-in and trained human reviewer. No unsolicited employer/command notification.
8. Rights/deadlines: reminders and official links; no court/stay or waiver decisions.
9. Observability: case timeline, SLA alerts, appeal evidence, aggregate stats and access audits.
10. Security boundary: segregate civilian, military-benefits and bank-finance datasets; implement RBAC/ABAC and no cross-purpose joins.

## Candidate interfaces — no connection currently
- Defence/اعتزاز: pilot referral/partner onboarding after approved agreement.
- SDAIA GSB: government interoperability possible only via eligible, authorized participating entities.
- Bank/finance: consent-driven sharing via licensed routes and banking partner; no deposits, lending, collections, auto debits.
- Justice: official case navigation only; no automated enforcement status claims.
- Benefits/housing/education/health: navigators from publicly verified rules first; APIs later if approved.
- User upload: synthetic demo only until legal/privacy/security gate passes.

## MVP deliverables
Single-case timeline, role-separated reviewer, read-only synthetic rules, proof receipts, case export and withdrawal action; no financial or court integration.

## Core safety gates
Deny by default; case is never submitted from AI output alone; external transmission requires authorized operator, purpose/legal basis, per-destination agreement, validated data classification, recorded human approval, expiry check and receipt. Non-production flags may not be overridden by user interface.
