# VAIXLNS — Claude Code and Multi-Provider Model Gateway v1

**Status:** Implementation candidate. Local host registration and live provider requests remain unverified.

## Existing components inspected

- tools/arcx_mcp/server.py is an existing read-only ARC-X MCP server.
- scripts/windows/run_arcx_mcp.ps1 and requirements-arcx-mcp.txt support that separate prototype.
- scripts/arcx_vx_bridge.py provides a request-only ARC-X → VX seam, not proof of a live VX runtime.
- docs/architecture/VAIXLNS_AGENT_AI_SERVER_INTEGRATION_FABRIC_V1.md defines the wider integration architecture.

The model gateway is intentionally a separate process. It adds outbound model API calls without expanding the read-only repository server.

## Provider environment

Configure credentials through the local shell or an approved OS secret manager. Never commit API keys, paste them into prompts, or log them.

| Provider | Credential variable | Required model variable |
|---|---|---|
| OpenAI | OPENAI_API_KEY | VAIXLNS_MODEL_OPENAI |
| Claude | ANTHROPIC_API_KEY | VAIXLNS_MODEL_CLAUDE |
| Gemini | GEMINI_API_KEY | VAIXLNS_MODEL_GEMINI |
| Grok | XAI_API_KEY | VAIXLNS_MODEL_GROK |
| Mistral | MISTRAL_API_KEY | VAIXLNS_MODEL_MISTRAL |

Model IDs are operator-supplied because availability and account access change. Configuration inventory does not make a network request and does not verify credentials.

## Windows setup

From the repository root in PowerShell:

    py -3.11 -m venv .venv-model-mcp
    .\.venv-model-mcp\Scripts\python.exe -m pip install -r requirements-model-mcp.txt
    $env:PYTHONPATH = (Get-Location).Path
    .\.venv-model-mcp\Scripts\python.exe -m unittest tests.test_model_mcp_gateway -v

Set the credential and model variables in the local shell or OS secret manager; do not store real values in repository files.

## Claude Code registration

Run from the local repository root in PowerShell:

    claude mcp add --transport stdio vaixl-model-gateway -- .\.venv-model-mcp\Scripts\python.exe -m tools.model_mcp.server
    claude mcp list
    claude mcp get vaixl-model-gateway

The repository root must be available to the server process through PYTHONPATH. If Claude Code starts the process from another directory, use a local launcher with an absolute path and set PYTHONPATH there. Avoid committing machine-specific absolute paths.

Inside Claude Code, use /mcp and verify that list_model_providers and invoke_model appear. Discovery confirms registration only, not provider API connectivity.

## Exposed tools and boundaries

- list_model_providers: reports provider names and whether key/model variables are present; never returns credential values.
- invoke_model(provider, prompt, max_output_tokens): explicitly sends one text prompt to one selected provider and normalizes the response.
- Supported IDs: openai, claude, gemini, grok, mistral.
- No shell, filesystem write, arbitrary endpoint, automatic model routing, provider tool calling, VX execution, or canonical write is exposed.
- Redirects are rejected; request timeouts, prompt size, response size, and output-token bounds are enforced.
- Provider output remains untrusted. RESPONSE_RECEIVED is not independent verification or evidence admission.

## Verification checklist

- [ ] Install the environment on the target machine.
- [ ] Run the gateway unit tests successfully.
- [ ] Register the MCP server in Claude Code and verify both tools appear.
- [ ] Send one low-risk authorized request to each configured provider.
- [ ] Record provider/model, timestamp, latency, and redacted result evidence.
- [ ] Keep project.genome and Ω.000 unchanged.
- [ ] Do not label any provider VERIFIED until live requests and independent checks are recorded.
