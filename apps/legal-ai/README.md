# VAIXLNS Legal AI — MVP

## Scope
Single mobile-responsive Arabic interface at `apps/legal-ai/index.html`. Target customers: independent lawyers, law firms, and bank legal departments. This is an offline demo, **not** a commercial or regulatory compliant product.

## Screens
- Overview: state and route to dedicated workflows
- Lawyers: local keyword presence check for sample contract terms
- Banks: local keyword presence check for sample policies/contracts
- Offers: illustrative plans and seat estimate, **no checkout**
- Evidence: ephemeral client-side event list and JSON export
- Integrations: explicit unavailable integration indicators

## Run locally
Open `apps/legal-ai/index.html` in a browser. No dependencies, API calls or credentials required.

## Manual acceptance checklist (NOT_RUN; execute before promotion)
1. On a mobile viewport, open each of the six sections; navigation remains usable.
2. On Lawyers, submit empty and nonempty input and verify corresponding local warning.
3. On Banks, submit illustrative text and verify keyword-only outcomes, not regulatory claims.
4. On Offers, test 1, 5 and 10000 users and reject negative and noninteger values.
5. Export event JSON and inspect timestamps, type, and `DEMO_ONLY` statuses.
6. Review browser network: no user content sent to a server.
7. Test keyboard navigation and screen-reader labels; record issues.
8. Run lint/security review and CI once an automated test harness exists.

## Next implementation gates
G1: Authentication, tenant separation, RBAC and audit storage.
G2: Controlled, versioned Saudi legal source corpus with retrieval citations.
G3: VX adapter with identity, permissions and fail-closed tool registry.
G4: Evaluation harness for legal accuracy, citation validity, refusal, data isolation and threat testing.
G5: Paid pilots and pricing validation. Payment processing remains disabled until approved.
G6: Bank-specific compliance and security review before processing any real bank data.

## Operating invariants
- No CLAIMED_VERIFIED without real test evidence and CI run reference.
- No main merge, release, or external spend without explicit approval.
- Do not modify `project.genome` or `Ω.000`.
- Never represent this demo as official Saudi legal advice or as an integration with Ministry of Justice or a bank.
