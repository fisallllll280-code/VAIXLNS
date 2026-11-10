# VAIXLNS Windows Intent-to-Execution Contract — v1

**Status:** Initial guarded implementation; local execution only.  
**Scope:** Convert an approved, typed request into a narrowly allow-listed Windows capability and produce auditable evidence.  
**Truth boundary:** This contract does not create remote access, install an agent, grant privileges, or connect a Windows host automatically. An operator must place the repository on Windows and invoke the runner locally.

## 1. Design rule

Natural-language intent is an input to the reasoning layer, not executable code. The reasoning layer must translate a request into a typed request object; Windows must never execute shell text, generated scripts, or model-produced command strings directly.

The execution path is:

`REQUEST → NORMALIZE → RESOLVE TARGET → CAPABILITY LOOKUP → RISK CLASSIFY → POLICY GATE → PLAN → AUTHORIZE → EXECUTE → VERIFY → EVIDENCE`

Unknown intent, missing fields, ambiguous targets, unsupported capabilities, policy disagreement, or failed verification produce `BLOCKED`, `NO_OP`, or `FAILED`—never a best guess.

## 2. Request contract

A request is a UTF-8 JSON object matching `schemas/windows-intent-request.schema.json`. Version 1 supports exactly one executable capability:

- `windows.inventory.readonly` — run the existing read-only inventory collector.

The request contains no arbitrary command field. The runner rejects unknown fields and unsupported operation/risk combinations. Future capabilities must be added deliberately to the schema, policy, implementation, and tests together.

Example (plan only):

```json
{
  "schemaVersion": "1.0",
  "requestId": "inventory-baseline-001",
  "intent": "Collect a baseline inventory of Windows and boot/recovery status without changing settings.",
  "target": "local_windows_host",
  "operation": "windows.inventory.readonly",
  "risk": "R0",
  "mode": "plan"
}
```

For an actual R0 inventory, change only `mode` to `execute`. Do not add PowerShell, cmd.exe, WMI query text, paths, or arguments to the request.

## 3. Intent translation policy

The reasoning layer must extract: objective, target, expected end state, scope, permitted data, risk tier, reversibility, verification criteria, and missing prerequisites. It must produce the JSON request, not an executable command.

Before a capability is eligible:
1. Resolve the named machine/repository precisely.
2. Map the objective to a registered capability ID.
3. Identify the smallest scope that satisfies the objective.
4. Classify risk using the highest credible impact, not the easiest route.
5. State the observable success criteria and evidence to collect.
6. Check prerequisites and whether the request exceeds the caller's authority.
7. If a missing detail changes the target, impact, data exposure, or recovery path, stop for clarification instead of guessing.

## 4. Capability and risk model

| Tier | Meaning | Default decision |
|---|---|---|
| R0 | Read-only inventory and status inspection | May execute only registered R0 capabilities |
| R1 | Reversible source/repository changes in an isolated workspace | Plan or sandbox only until separately implemented and tested |
| R2 | Host configuration, service, driver, software, or update changes | Require explicit action-specific human approval and a rollback plan |
| R3 | Boot, EFI/BCD, partitions, firmware, Secure Boot, BitLocker, recovery layout | Deny by default; require separate reviewed implementation, independent review, verified recovery media, maintenance window, and per-action approval |

A user's broad instruction such as “fix everything”, “make it stronger”, or “fully preserve the system” is not blanket authorization. Approval for one operation does not authorize another operation or tier. No agent may escalate its own permissions.

## 5. Execution rules

- Only fixed, versioned capability handlers may run.
- Never use `Invoke-Expression`, dynamic script generation, or a model-generated shell command as an execution mechanism.
- Do not collect secrets, passwords, API tokens, BitLocker recovery keys, or credential-store contents.
- Do not disable security controls to make a task pass.
- Keep output under the repository's `reports/windows/` directory and include a content hash.
- A successful process exit is not sufficient proof: parse the output, preserve UNKNOWN/UNAVAILABLE states, and verify the artifact's integrity.
- If a check is inconclusive, report it as inconclusive. Do not coerce UNKNOWN into PASS.
- The runner is intended to run as the ordinary user. If a capability later needs elevation, it must stop and request a separate, explicit approved path; do not self-elevate.

## 6. Current runtime behavior

`scripts/windows/Invoke-VaixlIntent.ps1` implements the initial boundary:
- validates the request envelope and supported operation;
- supports `plan` mode without host inspection;
- executes only `windows.inventory.readonly` at `R0`;
- invokes the existing inventory script using a fixed path;
- stores the inventory in `reports/windows/`;
- validates that the report is JSON, calculates SHA-256, and reports inconclusive checks;
- emits a result record and makes no boot, security, registry, service, driver, software, or update changes.

It is a local runner, not a natural-language parser. The VAIXLNS/agent layer must produce the typed JSON; the operator must review the request before executing it.

## 7. Example operator flow

1. Review the request JSON and its target, operation, risk, and mode.
2. Run plan mode first:
   `powershell -NoProfile -File .\\scripts\\windows\\Invoke-VaixlIntent.ps1 -RequestPath .\\requests\\windows-inventory.json`
3. Inspect the returned plan. Change `mode` to `execute` only for the supported R0 inventory request.
4. Run again and inspect both the result record and report under `reports/windows/`.
5. Archive the request, result JSON, report, SHA-256, timestamp, and reviewer decision together.

## 8. Admission criteria for future engineering tools

A future capability is not executable until it has:
- a unique capability ID and exact parameter schema;
- a least-privilege implementation with explicit target scoping;
- a deterministic risk decision and authorization rule;
- timeout/resource limits and safe failure behavior;
- tests for valid, malformed, unknown, denied, and boundary inputs;
- independent verification that does not approve its own originating change;
- evidence schema, redaction policy, and rollback/recovery guidance where relevant;
- documentation that distinguishes implemented, tested, and merely proposed behavior.

## 9. Acceptance criteria

- Unknown operations and extra request fields are blocked.
- Arbitrary command text is never accepted or executed.
- `plan` does not inspect or mutate the host.
- The only executable v1 operation is read-only inventory at R0.
- The artifact path is controlled by the runner, not by request input.
- Output indicates whether checks were inconclusive and includes a SHA-256 hash.
- No host configuration, boot configuration, security policy, or update is changed.
- No claim of a successful backup/restore is made from inventory evidence alone.
