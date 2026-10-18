# VX Runtime Verification Runbook

## Purpose

This runbook defines a fail-closed readiness gate. A repository file, pull request, connector registry entry, or planned service is not proof of live operation. Missing evidence is reported as FAIL.

## Run locally

```bash
python scripts/vx_verify.py
python scripts/vx_verify.py --run-tests --json-out artifacts/vx-verification-report.json
```

Use `--strict` when a process must exit nonzero unless every readiness gate passes. CI uploads the report first, then runs the strict gate. Missing operational evidence makes the workflow fail rather than reporting a green check.

## Required evidence

- **Model connectors:** at least one registry entry marked `ACTIVE_VERIFIED` plus a smoke receipt supplied as `VX_CONNECTOR_SMOKE_EVIDENCE`. The JSON receipt must include `result: PASS`, `connector_id`, `request_id`, `response_digest`, a timezone-aware ISO-8601 `timestamp` no older than 15 minutes and no more than 60 seconds in the future, and `credential_redacted: true`. Never include prompts, API keys, or raw private responses.
- **Protected-state write paths:** `VX_PCS001_COVERAGE_RECEIPT` must point to a commit-bound JSON receipt with `status: VERIFIED` and a non-empty `writer_paths` list. Each entry must contain `path`, `guard_call`, `bypass_test`, and `bypass_test_result: PASS`. This receipt is an evidence gate, not an automatic proof; review its underlying tests and inventory all writers independently.
- **Unified runtime:** set `VX_SERVICE_HEALTH_URLS` to a JSON object containing HTTP(S) health URLs for all four keys `VX`, `VLNS`, `LNS`, and `NEXENT`. Each endpoint must return JSON with `status: healthy`, `status: ok`, or `ok: true`.
- **Meeting room:** set `VX_MEETING_HEALTH_URL` to a real health endpoint returning `room_live: true`, `audio_test_passed: true`, `participant_presence_verified: true`, `names_persisted: true`, a non-empty `session_id`, and `participant_count >= 2`. The endpoint must echo the unpredictable `X-VX-Probe-Challenge` request header as `probe_challenge` and return a timezone-aware `observed_at` timestamp within 60 seconds. A static mock endpoint cannot pass this per-request challenge.
- **CI:** in GitHub Actions, the workflow runs the test suite first and only then marks `VX_TESTS_PASSED=true` for the report step. The report records commit SHA and workflow run ID. A final green GitHub Actions conclusion must still be checked on GitHub.

## What the gate does not do

It does not deploy services, create a meeting service, configure credentials, activate connectors, or infer health from files. It probes only operator-configured endpoints and reads explicitly supplied evidence receipts. Do not set a gate to PASS merely to make the overall status green.

## Status interpretation

- `READY`: every configured readiness gate passed for the reported evidence.
- `NOT_READY`: at least one gate failed or lacks evidence.
- `CI_TESTS_PASSED` refers to tests in this workflow run, not a claim that all workflows or external end-to-end tests passed.


## Cross-repository conformance

The federated conformance workflow tests pinned revisions of VX-runtime, VX50_COMPLETE_BUILD, and NEXENT. NAXLNS and VX50_COMPLETE_BUILD are private repositories. Their tests run only when the corresponding repository variable and read-only repository secret are configured in VAIXLNS Actions settings: `NAXLNS_READ_ACCESS=enabled` with `NAXLNS_READ_TOKEN`, and `VX50_READ_ACCESS=enabled` with `VX50_READ_TOKEN`. If not configured, that job is skipped and the VLNS identity/runtime remains unverified; do not treat a skipped job as a pass. The workflow tests repository code only and does not prove that any production service is deployed or reachable.
