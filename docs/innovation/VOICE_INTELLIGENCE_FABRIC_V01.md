# Ω∞ Voice Intelligence Fabric — integration boundary v0.1

State: ISOLATED CODE SLICE; real audio and external tools NOT_CONNECTED.

## Voice architectural layers
Voice WebRTC gateway → session identity → provider adapter (Realtime / GPT-Live) → tool intent → scoped voice gate → backend authority, signature and idempotency validation → VX execution → append-only event evidence → Ω-RAC review.

These are distinct API families; do not copy GPT-Live event names into Realtime SDK sessions.

## Safety innovations
- Voice-to-action two-phase intent/confirmation, bound to request, user, session, expiry and signed challenge. This reference gate only checks nonempty confirmation_ref and matching request_id, **not cryptographic verification**.
- Stop-on-interruption: cancel pending uncommitted action when user interrupts, changes intent or channel disconnects.
- Session authority attenuator: session may narrow but never broaden permissions; revoke upon expiry.
- Privacy-first audit: no raw audio or transcription in default decision receipts. Recording requires separate consent and retention policy.
- Provider-independent tool contracts so Realtime and GPT-Live can be swapped without changing VX policy.
- Human handoff with minimal context and explicit user approval.
- Replay of tool-intent and policy decisions without requiring stored audio.
- Rate limits, latency/cost budgets and voice prompt-injection defense at the trusted backend, not merely in prompts.

## Tools
search_knowledge_base — read
get_order_status — scoped read; production backend must enforce ownership
create_support_ticket — state change; explicit signed confirmation
request_human_handoff — state change; explicit signed confirmation

## Mandatory production gaps
HTTPS server and auth; real WebRTC; provider selection and model access; short-lived credentials; signed confirmation with nonce/expiry/principal binding; revocation; full application policy; idempotency store; VX integration; consent; data residency; cost caps and instrumentation; e2e tests on iPhone; security and prompt-injection tests; independent evidence, G0 and existing T01–T15 tests.

## Source docs (checked 2026-10-25)
- https://developers.openai.com/api/docs/guides/realtime
- https://developers.openai.com/api/docs/guides/voice-webrtc
- https://developers.openai.com/api/docs/guides/live
- https://developers.openai.com/api/reference/resources/realtime/subresources/client_secrets/methods/create

No merge/publish without explicit approval. External spend 0 SAR. Do not alter project.genome / Ω.000.
