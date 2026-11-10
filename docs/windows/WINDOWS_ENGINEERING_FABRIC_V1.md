# VAIXLNS Windows Engineering Fabric — Architecture Proposal v1

**Status:** PROPOSED — documentation only; no Windows machine has been connected or modified by this document.  
**Owner boundary:** VAIXLNS governance approves changes; VX executes approved actions; NEXENT researches and proposes; evidence and verification decide whether a result may be adopted.

## 1. Mission

Integrate Windows as a governed engineering host for VAIXLNS. The fabric inventories Windows and boot configuration, protects recoverability, hosts local tools and specialist agents, verifies repository changes, and tracks official Microsoft release/security information.

This is not a replacement Windows kernel, bootloader, or Microsoft management plane. It is a controlled integration layer operating through documented Windows interfaces.

## 2. Canonical topology

```text
Ω∞ / VAIXLNS Constitution
  └─ Canonical Nexus: identities, dependencies, lineage, authority
      ├─ NEXENT: research → architecture search → candidate plans
      ├─ XV / Specialist Agents: analysis, code review, test generation
      ├─ VX Windows Adapter
      │   ├─ Read-only host inventory
      │   ├─ Boot & recovery inspection
      │   ├─ Repository / toolchain adapter
      │   ├─ Sandbox and test runner
      │   └─ Approved change executor
      ├─ OIF: health, telemetry, incident and recovery status
      └─ ARC-X Ω / VV: evidence → verification → proof → admission
```

No agent receives unrestricted administrator authority. Each capability is exposed as a typed contract with input validation, an allowlist, resource/time limits, audit events, and a rollback or recovery plan where applicable.

## 3. Windows capability domains

### A. Boot and recovery assurance

Inventory and report, without mutation by default:
- UEFI/Secure Boot state where available.
- Boot Configuration Data (BCD) entries and current boot target.
- Windows Recovery Environment (WinRE) status.
- System volume, free space, BitLocker status (status only; never collect recovery keys).
- Available restore/recovery options and relevant event-log signals.

**Mutation policy:** changing BCD, partitions, EFI System Partition, Secure Boot settings, BitLocker, boot entries, or recovery configuration is a high-impact operation. Require a reviewed plan, verified backup/recovery media, explicit human approval, pre-change snapshot/evidence, and a tested rollback path. Never disable Secure Boot or encryption as a generic troubleshooting step.

### B. OS and platform diagnostics

Collect minimum necessary, non-secret inventory:
- Windows edition/build, architecture, patch level.
- Hardware and driver inventory.
- Service state and startup configuration.
- Reliability and relevant event logs.
- Disk health and system-file/component-store health signals.

Diagnostics should prefer supported interfaces and built-in tools. Repairs such as DISM/SFC or driver updates are separate proposed actions and must not be silently run by a research agent.

### C. Engineering workstation

- Git and repository federation status.
- Python/Node/.NET/C++ toolchain detection.
- Reproducible environment manifests and dependency lockfiles.
- Sandboxed builds and tests.
- Artifact hashes, SBOM/dependency reports where supported, test logs, and provenance.
- Local model adapter (for example, Ollama) only when installed and explicitly configured.

### D. Specialist-agent roles

| Agent | Allowed work | Forbidden by default |
|---|---|---|
| Windows Inventory Agent | Read-only host snapshot | Registry edits, service changes |
| Boot Assurance Agent | Parse boot/recovery status; draft plan | BCD/partition/EFI mutation |
| Security Review Agent | Review advisories, configuration, dependencies | Secret collection or policy bypass |
| Repository Engineer | Branch, edit, test, prepare PR | Push to protected branch or merge without approval |
| Research/NEXENT Agent | Search official docs, compare designs, propose tests | Treat unverified claims as facts |
| Independent Verifier | Re-run checks; compare evidence | Approve its own originating change |
| Microsoft Watch Agent | Track official release/security feeds | Install updates automatically |

Agent outputs are proposals until the verification and authority gates accept them.

## 4. Required action contract

Every action must carry:
- `action_id`, `actor_id`, `host_id`, `timestamp`
- intent and justification
- capability and version
- exact target and expected state transition
- policy decision and required authority
- preconditions, impact estimate, resource/time budget
- backup/recovery reference for high-impact actions
- execution result, event IDs, logs, hashes
- independent verification result
- rollback/recovery result and final status

Lifecycle:

`DISCOVER → IDENTIFY → CLASSIFY RISK → PLAN → AUTHORIZE → SNAPSHOT → SANDBOX/TEST → EXECUTE → OBSERVE → VERIFY → PROVE → COMMIT`

If authority, evidence, observability, or recovery readiness is missing: `QUARANTINE` or `NO-OP`, never guess.

## 5. Risk gates

- **R0 — Read-only:** inventory, parsing, status checks. May run on a schedule.
- **R1 — Reversible project changes:** create a branch, edit a worktree, run tests. Require scoped credentials and isolated execution.
- **R2 — Host configuration changes:** services, drivers, policy, application installation, update installation. Require explicit approval and a rollback plan.
- **R3 — Boot/security/storage changes:** BCD, EFI, partitions, Secure Boot, BitLocker, recovery partitions, firmware. Require explicit per-action approval, independent review, verified recovery media, and a maintenance window.

No automatic agent escalation from R0/R1 to R2/R3. Do not store passwords, API keys, BitLocker recovery keys, private tokens, or full memory dumps in the VAIXLNS ledger.

## 6. Microsoft change and security intelligence

Track official sources only as primary evidence:
- Windows Release Health: https://learn.microsoft.com/en-us/windows/release-health/
- Windows 11 release information: https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information
- Microsoft Security Response Center Security Update Guide: https://msrc.microsoft.com/update-guide/
- Windows Experience Blog: https://blogs.windows.com/windowsexperience/

For each item, store URL, publication/update time, product/version, KB/CVE if applicable, severity/impact, affected and resolved versions, source hash, retrieval time, relevance to the detected host, and reviewer status. Deduplicate by canonical URL + advisory/KB identifier. Label claims as `SOURCE_CONFIRMED`, `INFERRED`, or `UNVERIFIED`.

The watcher must create a report or issue only. It must not download or install an update automatically. Before recommending deployment, check applicability, safeguard holds, known issues, rollback options, and Microsoft’s current guidance.

## 7. Backup and preservation model

Keep host recovery separate from project preservation:
1. **Host recovery:** Windows recovery media and user-controlled system/data backups; verify that recovery is actually bootable where feasible.
2. **Project preservation:** Git history, protected branches, signed/tagged releases where available, archive manifests, hashes, and off-device copies.
3. **Evidence preservation:** append-only event records, source URLs, timestamps, test outputs, and proof artifacts.

A Git commit is not a Windows system backup. A restore point is not a substitute for an independent data backup. Do not claim full system preservation until a restore/recovery test has passed.

## 8. Initial implementation phases

1. **P0 — Contract and threat model:** approve permissions, data minimization, action schemas, risk gates.
2. **P1 — Read-only Windows inventory:** produce a redacted JSON report; no configuration changes.
3. **P2 — Recovery readiness report:** inspect BCD/WinRE/BitLocker/Secure Boot status without changing them.
4. **P3 — Repository adapter:** connect Git operations through branch/PR workflow; run tests in isolation.
5. **P4 — Specialist-agent router:** typed contracts, independent verifier, budgets, and audit trail.
6. **P5 — Microsoft Watch:** ingest official release/security sources and produce change reports.
7. **P6 — Controlled mutation pilot:** only one low-risk reversible action at a time, with explicit approval and recovery evidence.

Each phase needs tests, an evidence bundle, an operator guide, and a documented rollback before the next phase is admitted.

## 9. Acceptance criteria

- Inventory runs without administrator rights where possible and redacts secrets.
- A normal research task cannot invoke privileged operations.
- High-impact operations fail closed without explicit authorization.
- Boot/security configuration is never changed by default.
- Every action is traceable to an identity, contract, policy decision, evidence, and verifier.
- Microsoft Watch cites official sources and distinguishes facts from inference.
- No update is installed automatically.
- Recovery readiness is reported as unknown until evidence supports it.
- CI validates schemas, policy fixtures, and sample evidence records.

## 10. Current truth boundary

This document establishes a proposed architecture and implementation sequence only. It does **not** assert that a Windows host has been connected, that a boot/recovery audit has run, that Microsoft monitoring is scheduled, or that the system is operational. Those states require implementation and fresh evidence.
