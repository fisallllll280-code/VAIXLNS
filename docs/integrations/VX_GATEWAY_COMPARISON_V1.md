# VX Gateway Comparison v1 — LiteLLM vs OmniRoute

Status: IMPLEMENTED_ON_ISOLATED_BRANCH / CI_NOT_YET_VERIFIED / NOT_CANONICAL

## Scope
This slice adds a fail-closed **offline comparison policy** to the existing VAIXLNS model routing implementation. It does not install gateways, authenticate to providers, benchmark models, modify the canonical index, or authorize external calls.

Authority chain: VAIXLNS governance -> existing `scripts/arcx_model_router.py:plan_route` -> `scripts/vx_gateway_comparison.py:compare_gateways` -> proposed candidates for independent review. A comparison result is not an execution grant.

## Preconditions
- Existing model-route plan must have `state=ROUTE_CANDIDATES_READY` and `provider_called=false`.
- `allow_live_requests=false`, `max_external_spend_sar=0`.
- Explicit allowlist for `litellm` and/or `omniroute`.
- Each gateway entry needs verified contract and tenant isolation, `external_secret_store`, zero estimated request cost and egress disabled.
- Unregistered/unverified entries never become eligible.
- Missing route or no eligible gateway => BLOCKED.

## Test plan
Offline:
`python -m unittest discover -s tests -p 'test_vx_gateway_comparison.py' -v`

Integration (NOT RUN): deploy both gateways in an isolated lab with fake OpenAI-compatible responder. Pin images/digests and refuse outbound egress. Test policy route -> gateway -> fake responder including HTTP 401, 403, 429, 500, retries, idempotency, redaction, replay and latency percentiles. Measure each provider behind the same mock model; distinguish overhead from real-model latency.

Production candidate: must separately pass identity/IAM, secret scanning, egress allowlists, provider license review, external cost authorization and G0–G5 gates. No direct merge to main.

## Evidence
For each test run preserve source commit, UTC timestamp, process exit code, test XML/report, runner image digest and artifact SHA-256. Never set VERIFIED merely because a test file exists.

## Protected files
Do not modify `project.genome` or `Ω.000`. No release, no automatic merge, no spending. Changes are isolated to new policy, tests and this documentation.

## Known limitations
Only policy evaluation is implemented. No claims of working LiteLLM/OmniRoute connectivity, speed improvements, or guaranteed free access are made.
