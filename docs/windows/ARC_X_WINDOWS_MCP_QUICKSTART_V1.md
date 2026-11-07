# ARC-X Ω — Windows MCP Prototype Quickstart v1

**State:** Implementation candidate; local execution must be validated on the target Windows machine.  
**Scope:** Read-only local repository inspection and bounded UTF-8 source retrieval.  
**Not included:** ChatGPT installation, remote hosting, GitHub write actions, VX task submission, canonical writes, or production deployment.

## Prerequisites

- Windows 10/11 x64.
- Python 3.11+ available as the py launcher or python command.
- Git installed and available on PATH (revision metadata is optional).
- A local checkout of VAIXLNS.
- PowerShell 5.1 or PowerShell 7.

## Setup

Open PowerShell in the repository root and run:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\windows\setup_arcx_mcp.ps1

The script creates an isolated .venv-arcx environment, installs the MCP SDK from requirements-arcx-mcp.txt, and runs unit tests. It does not modify the system Python environment.

## Start the server

From the repository root:

    .\scripts\windows\run_arcx_mcp.ps1 -RepositoryRoot (Get-Location).Path

The server uses MCP stdio transport. It is intended to be launched by a compatible MCP host; running it directly in a terminal waits for protocol messages and is not a user-facing console.

## Exposed tools

- inspect_repository: bounded inventory of up to 2,000 paths; excludes common generated directories, symlinks, and sensitive filenames.
- fetch_source: reads one UTF-8 file under the configured root, maximum 256 KiB, and returns the source revision and SHA-256 digest.
- classify_claim: reports evidence coverage; it never promotes a claim to VERIFIED and does not independently validate supplied evidence.

## Security boundaries

- Read-only: no file writes, arbitrary shell execution, network fetches, GitHub writes, or VX submissions.
- Path traversal and resolved symlink escapes are rejected.
- Sensitive filenames such as .env, SSH private keys, and common credentials JSON names are blocked.
- Repository contents are untrusted input. Tools return content for inspection; they do not execute it.
- Do not place credentials in repository files. The filename denylist is a guardrail, not a secret scanner.
- The MCP server is not a network listener; stdio transport does not make it remotely reachable.
- Connecting this server to ChatGPT requires a separately supported host/connector configuration. A local Windows process is not automatically available to ChatGPT cloud sessions.

## Verification checklist

- [ ] Run setup script on the target Windows machine.
- [ ] Confirm all unit tests pass.
- [ ] Confirm repository inventory stays within the selected root.
- [ ] Confirm traversal and symlink escape tests reject outside paths.
- [ ] Confirm sensitive files cannot be fetched.
- [ ] Test with a compatible MCP host and verify the three tools appear.
- [ ] Review permissions before connecting to any host.
- [ ] Keep write-capable tools disabled until separate security review and approval.

Successful setup or tests establish only the tested local prototype behavior; they do not establish production readiness or truth of repository claims.
