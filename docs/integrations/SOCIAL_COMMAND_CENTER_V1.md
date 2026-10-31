# VAIXLNS Social Command Center v1
Status: ISOLATED_BRANCH / OFFLINE_UI / NO_PROVIDER_CONNECTION / NOT_VERIFIED_FOR_PUBLISHING

## Launch
Open `web/social-command-center/index.html` locally in a browser. No build tools needed. Mobile responsive, Arabic RTL. This is a static demonstration, not deployed.

## Modules
Programs overview (labels only, not live status); channels overview (all disconnected); draft composer (clipboard only). A disabled Publish button clearly indicates no OAuth integration.

## Safe boundary
`scripts/social_publication_gate.py` returns DRAFT_REVIEW_REQUIRED or BLOCKED and deterministic receipt. It **never** calls APIs or publishes. Tests: `python -m unittest discover -s tests -p 'test_social_publication_gate.py' -v`.

## Integration contract for later review
1. Inventory existing identity/tenant/authority layers before implementation.
2. Configure per-platform official OAuth via server-side redirect, PKCE where supported, minimum permitted scopes, encrypted token storage, rotation and revocation; never embed secrets in HTML.
3. A server-side tenant-bound connection registry maps channel to platform account ID, token reference, scopes, expiration and evidence provenance; do not treat self-reported connection as authenticated.
4. Provider-specific adapters support platform permissions, text/media constraints, scheduling, rate limits, failures, idempotency and provenance; no assumed cross-platform equivalence.
5. Require explicit owner approval per publication, hash of approved content, account and scheduled time, and secure dispatch authorization. Zero external spend unless separately approved.
6. Require signed action receipts, external post IDs and URLs on confirmed success; mark UNKNOWN on timeout and reconcile instead of blindly retrying.
7. No automatic release, main merge, live publishing or changes to project.genome/Ω.000 without owner authorization.

## Acceptance evidence
Tests and CI tied to source commit and runner; fixture-only UI checked; OAuth integration NOT_RUN, actual publication NOT_RUN, app deployment NOT_RUN. No VERIFIED label for real social integrations.
