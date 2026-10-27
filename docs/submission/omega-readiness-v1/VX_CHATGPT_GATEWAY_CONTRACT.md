# VX ↔ ChatGPT Governed Gateway — Integration Contract v0.1

Status: SPECIFIED / NOT CONNECTED / NOT VERIFIED
Date: 2026-10-27

## Intent
Make VX a governed external tool and evidence engine callable by an AI assistant through a supported connector, custom GPT action, or MCP-compatible gateway. This does NOT change model weights or imply internal access to ChatGPT. Until an endpoint, authentication, tool discovery and a successful real call are independently evidenced, the integration is not active.

## Trust architecture
ChatGPT client (untrusted natural language intent) → authentication + request signing → VAIXLNS authority/policy gate → VX dispatch/router → bounded tool/agent adapter → sandbox → append-only evidence receipt → response summary. VX cannot grant itself canonical approval. Every model-generated suggestion is untrusted input until reviewed.

## Mandatory request envelope
request_id; principal_id; purpose; tool_name; arguments; source_refs (repository/commit/path); data_classification; requested_capability; budget_sar (default 0); execution_deadline; idempotency_key; approval_id (optional); policy_version.

## Mandatory response
request_id; disposition (DENIED|SIMULATED|EXECUTED|FAILED); policy_decision_ref; execution_receipt_ref; source_commit; output_digest_sha256; test_results; evidence_refs; errors; reviewer_status (UNREVIEWED|REVIEWED); canonical_state (never auto-promoted).

## Minimum endpoints (design only)
GET /healthz — does not imply tools connected.
GET /v1/capabilities — authenticated, least privilege, no secret exposure.
POST /v1/operations/preflight — read-only, no spending.
POST /v1/operations/execute — denied by default; policy + approval + bounded sandbox required.
GET /v1/receipts/{id} — authorized, immutable record and integrity check.

## Required negative tests
Missing/expired credentials; replayed idempotency key; oversized requests; prompt injection in tool output; cross-tenant access; budget > 0 SAR; protected path write; direct VX-to-system bypass; no evidence sink; stale commit and endpoint down. Deny and issue a failure receipt. Simulations must remain distinct from executions.

## Authentication
Prefer OAuth with short-lived audience-scoped tokens, rotation and revocation for delegated user operations; machine-to-machine credentials in a secrets vault and mTLS where appropriate. Never commit any key. Endpoint URL, owner, issuer, required scopes and reachability currently UNKNOWN.

## Proof before activation
1. Resolve an actual HTTPS gateway address and ownership; TLS and certificate checks.
2. Validate OAuth/API authentication and available scopes.
3. Run read-only health + capabilities using a dedicated nonprivileged identity.
4. Execute one authorized isolated test with explicit receipt.
5. Reproduce receipt hash independently and verify policy denial for one forbidden action.
6. Declare IMPLEMENTED only after source and deploy evidence, VERIFIED only after independent end-to-end review.

No automatic merge, deployment, chargeable provider call or unrestricted autonomous invocation.
