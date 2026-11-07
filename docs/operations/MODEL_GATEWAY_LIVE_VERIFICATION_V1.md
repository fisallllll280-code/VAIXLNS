# VAIXLNS Model Gateway — Live Verification Runbook v1

## Status boundary

This runbook is a verification procedure, not evidence that any provider is connected. The gateway's mocked contract tests and CI do not prove local Claude Code discovery or live provider reachability. Keep all providers at `PARTIAL` until the evidence below is captured.

Canonical files `project.genome` and `registry/omega/omega-000-master-index.json` are out of scope and must not be modified by this integration.

## 1. Preconditions

- Use branch `feat/claude-code-model-gateway-001`; do not merge or promote provider status as part of verification.
- Install the model MCP dependencies from `requirements-model-mcp.txt` in an isolated environment.
- Supply credentials only through the local process environment or a local, ignored secret manager. Never paste keys into Claude prompts, commits, CI logs, screenshots, or issue comments.
- Set a valid provider model ID for each configured provider. A present key/model variable means only `CONFIGURED`, not connected.

## 2. Provider configuration inventory

Run the MCP server through Claude Code and call `list_model_providers`. Record for each provider:

- provider name;
- credential present (boolean only);
- model configured (boolean only);
- returned status;
- timestamp, branch, and commit SHA.

Expected before live calls: configuration-only states such as `MISSING_CONFIGURATION` or `CONFIGURED`. The tool's `live_connectivity_verified` must remain false until a live request succeeds.

## 3. Required live request per provider

For each of OpenAI, Claude, Gemini, Grok, and Mistral:

1. Confirm the provider's credential and model variables are present without printing their values.
2. Call `invoke_model` explicitly for that provider with a harmless prompt asking for the exact token `VAIXLNS_PROVIDER_SMOKE_OK`.
3. Capture the tool result and the timestamp. Redact credentials and any sensitive response content.
4. Require `status=RESPONSE_RECEIVED`, the expected provider name, the configured model ID, and a non-empty text response.
5. Record the provider HTTP/API result separately from MCP discovery and CI status.

A failure, timeout, missing credential, or invalid response remains `PARTIAL`/blocked; do not infer success from a different provider.

## 4. Claude Code discovery test

- Start the MCP server using the branch's documented configuration.
- In Claude Code run `/mcp`.
- Verify the server is listed and both tools `list_model_providers` and `invoke_model` are visible.
- Invoke `list_model_providers`, then execute one live request per authorized provider as described above.
- Save sanitized output plus branch/commit identity. A valid configuration file alone does not pass this gate.

## 5. Security and failure tests

- Unknown provider is rejected.
- Empty and over-limit prompts are rejected.
- Output-token values outside 1..8192, including booleans, are rejected.
- Missing key or model ID fails closed without network access.
- Redirect responses are not followed.
- Oversized, invalid-JSON, empty, and malformed provider responses are rejected.
- Provider error bodies and credential values are never returned to the caller.
- No tool execution, shell execution, filesystem writes, repository writes, or canonical admission is exposed by the model gateway.

Run the repository's existing model-gateway unit tests and CI before treating these checks as passed. Do not report a test as passed unless its actual output is available.

## 6. Evidence record

For every test record:

```json
{
  "verification_id": "VAIXLNS.MODEL_GATEWAY.LIVE.001",
  "provider": "openai | claude | gemini | grok | mistral",
  "branch": "feat/claude-code-model-gateway-001",
  "commit_sha": "<actual commit SHA>",
  "timestamp_utc": "<actual timestamp>",
  "mcp_discovery": "PASS | FAIL | NOT_RUN",
  "configuration": "CONFIGURED | MISSING_CONFIGURATION",
  "live_request": "PASS | FAIL | NOT_RUN",
  "response_contract": "PASS | FAIL | NOT_RUN",
  "secret_redaction": "PASS | FAIL | NOT_RUN",
  "evidence_uri": "<sanitized log or CI run URL>",
  "epistemic_status": "VERIFIED | PARTIAL | MISSING"
}
```

Do not fill placeholders with assumed values. `VERIFIED` requires a reproducible live result tied to the exact commit, and independent review of the evidence. This procedure does not grant canonical authority or change `Ω.000`.
