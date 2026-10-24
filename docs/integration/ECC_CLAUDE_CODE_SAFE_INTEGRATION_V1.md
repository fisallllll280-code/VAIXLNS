# ECC × Claude Code × VAIXLNS — isolated installation and verification

Status: **PREPARED / NOT INSTALLED / NOT VERIFIED** (2026-10-25).
Authority: VAIXLNS; VX remains the execution/evidence gate. This file does not enable a remote service, connect a model, or grant canonical authority.

## Existing integration retained
- `docs/integration/CLAUDE_CODE_MODEL_GATEWAY_SETUP_V1.md` documents the existing Claude Code MCP model gateway.
- `docs/operations/MODEL_GATEWAY_LIVE_VERIFICATION_V1.md` defines the five-provider live verification obligations.
- ECC is a Claude Code skills/agents plugin, **not** a substitute for the model MCP gateway or the VX runtime.

## Constraints
- Use an isolated worktree and branch; **never auto-merge, publish, or spend**.
- Do not edit `project.genome`, `Ω.000`, or `registry/omega/omega-000-master-index.json`.
- Keep provider credentials outside the repo and prompts. No model API requests without explicit cost approval (spend cap 0 SAR).
- Reject unregistered integrations; run with minimum privilege. Review plugin hooks before enabling them.
- Do not label installed/connected/tested/VERIFIED without session logs and review.

## Operator execution (Claude Code host required)
Use a trusted workstation or remote environment with the Claude Code CLI. From an isolated checkout:

```bash
git fetch origin
git worktree add ../VAIXLNS-ecc -b local/ecc-test origin/feat/ecc-claude-code-safe-integration-20261025
cd ../VAIXLNS-ecc
claude --version
git status --short
claude
```

Inside **Claude Code** (not the shell):

```text
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc
/plugin
/ecc:configure-ecc
```

In the `/plugin` UI select **Local** for this experiment. Configure ECC hooks in Minimal mode initially; inspect exact hooks and permissions before raising to Standard/Strict. Avoid any standalone installer (`npx ecc-universal setup`, `install.sh`) in parallel with a marketplace installation.

CLI verification commands in the regular terminal (the CLI syntax is version-dependent; confirm against `claude plugin --help`):

```bash
claude plugin list
claude plugin marketplace list
git diff --name-only
git status --short
```

Then inside Claude Code check `/plugin`, `/ecc:configure-ecc`, `/mcp`, and use a harmless read-only task. **Do not** use a live provider invocation for smoke testing while the spend cap is zero.

## Acceptance gates

| Gate | Required evidence | Current result |
|---|---|---|
| Repository baseline | branch, HEAD commit SHA, clean worktree, protected-file hashes | NOT_RUN |
| ECC marketplace registered | redacted CLI/Claude plugin listing | NOT_RUN |
| ECC enabled in Local scope | listing and session output | NOT_RUN |
| Skill invocation | harmless skill invocation result | NOT_RUN |
| Existing MCP unaffected | `/mcp` discovery before and after | NOT_RUN |
| Hooks / permissions reviewed | recorded configuration, no unexpected writes | NOT_RUN |
| Security and regression | repo tests, CI link, exact commit | NOT_RUN |
| VX evidence admission | independently reviewed artifacts | BLOCKED |

This document is preparation only. Installing ECC into the user's actual Claude Code session requires execution on the host; GitHub repository file writes cannot install or validate a host plugin.

## Evidence record schema (example template, NOT a test result)
```json
{
  "integration": "ECC_CLAUDE_CODE_V1",
  "branch": "feat/ecc-claude-code-safe-integration-20261025",
  "commit_sha": null,
  "claude_version": null,
  "ecc_version": null,
  "ecc_installed": false,
  "skill_smoke": "NOT_RUN",
  "mcp_regression": "NOT_RUN",
  "protected_files_unchanged": "NOT_RUN",
  "runtime_verified": false,
  "approval_to_merge": false
}
```
