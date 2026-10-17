# Deep-Index Agent Execution Preflight — VAIXLNS / VX

**Status:** implementation aid; not an admission record and not proof of live model execution.

This runbook uses the canonical `Ω.000` index and existing registries. It does not create a parallel agent roster. Its purpose is to identify exact blockers before running the existing `vx-agents-fabric` orchestrator.

## 1. Run the read-only preflight

From the VAIXLNS repository root:

```powershell
python scripts/agent_execution_preflight.py
$LASTEXITCODE
```

The report classifies source/contract integrity separately from admission and runtime prerequisites:

- `PRECHECK_PASSED_NOT_LIVE_VERIFIED`: static prerequisites appear configured; a real smoke run, retained evidence and independent review are still required.
- `HOLD`: one or more required bindings, provider settings, or admission gates are missing.
- `REJECT`: a required source artifact or a hard authority/contract invariant is invalid.
- Exit codes: `0` precheck only; `2` HOLD; `3` REJECT; `4` local input/output error.

To save a report without overwriting the canonical files:

```powershell
python scripts/agent_execution_preflight.py --output reports/agent-execution-preflight.json
```

The report contains SHA-256 digests and environment-variable presence only. It does not emit model keys, endpoint values, prompts or credentials. The preflight does not perform network requests or execute agent tasks.

## 2. Run the existing VX orchestrator in a separate checkout

The runtime is maintained in `fisallllll280-code/vx-agents-fabric`. Do not copy its source into VAIXLNS or create a competing orchestrator.

On Windows PowerShell:

```powershell
cd ..\vx-agents-fabric
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Configure only an endpoint and model IDs that you are authorized to use. Keep API keys in local environment variables or a secret manager, never in tracked files:

```powershell
$env:VX_OPENAI_COMPAT_BASE_URL = "http://127.0.0.1:11434/v1"
$env:VX_RESEARCH_MODEL = "<configured-research-model>"
$env:VX_FINANCE_MODEL = "<configured-finance-model>"
$env:VX_ENGINEERING_MODEL = "<configured-engineering-model>"
$env:VX_GOVERNANCE_MODEL = "<configured-governance-model>"
$env:VX_MIND_MODEL_MIND_SYS_ARCH = "<independent-review-model>"
$env:VX_MIND_MODEL_MIND_RESEARCH = "<independent-review-model>"
$env:VX_MIND_MODEL_MIND_FINANCE = "<independent-review-model>"
$env:VX_MIND_MODEL_MIND_SECURITY = "<independent-review-model>"
$env:VX_MIND_MODEL_MIND_PROOF = "<independent-review-model>"
```

For authenticated endpoints, set `VX_OPENAI_COMPAT_API_KEY` in the shell or secret manager; do not write its value here. Set durable local paths for the event ledger, artifact archive and failure memory if they are required for the run.

Run the existing CLI and preserve the complete JSON report:

```powershell
$env:PYTHONPATH = "src"
python -m vx_agents_fabric.cli --goal "Run a bounded, evidence-first VAIXLNS agent workflow and report missing capabilities" --workflow-id "WF-DEEP-INDEX-AGENT-PREFLIGHT-001" --output reports/WF-DEEP-INDEX-AGENT-PREFLIGHT-001.json
$LASTEXITCODE
```

A `HOLD` result is the expected safe outcome when adapters or required evidence are absent; it is not a successful live run. Configure the internet-search, repository and sandbox adapters separately because a chat model endpoint alone does not provide those capabilities.

## 3. Admission boundary

The current canonical binding map is `PROPOSED_NOT_ACTIVE`, runtime templates are not deployed, provider connectivity is not asserted, and the canonical durable VAIXLNS event-ledger link is not admitted. Do not change these statuses merely to make the preflight pass. The next gate requires a reviewed exact role/version mapping, adapter tests, failure/replay evidence, independent verification, fresh proof and an explicit VAIXLNS governance decision.

Production publication, canonical registry mutation and deployment remain outside agent authority.
