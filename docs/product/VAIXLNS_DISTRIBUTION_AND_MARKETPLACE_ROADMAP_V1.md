# VAIXLNS Distribution and Marketplace Roadmap v1

**State:** SPECIFIED / not published to any marketplace.  
**Product target:** VAIXLNS Engineering Continuity Platform (VX + XV).

## Distribution principle

Do not attempt a broad consumer launch before the core task-to-evidence loop is reproducible. Start with the smallest installable product, earn trust through visible evidence, and expand distribution only after reliability, security, licensing and support gates pass.

## Stage 0 — Repository-native alpha
- Publish the source, usage guide, threat model, architecture, tests and known limitations in VAIXLNS.
- Install from a tagged source release or built wheel in a clean Python 3.12 environment.
- Provide the `vaixlns-plan` CLI for plain-language requests and optional local SQLite checkpoints.
- Make it explicit that this version plans and records tasks; it does not yet connect external model providers or execute arbitrary code.

## Stage 1 — Developer preview
- Add a repository read-only scanner and evidence report.
- Add GitHub App integration with least-privilege permissions; begin read-only.
- Add sandboxed patch preview, test output capture, and explicit approval before writes.
- Publish signed release artifacts, checksums, SBOM, changelog, and reproducible install instructions.

## Stage 2 — Extension / developer marketplace
Candidate channels after their current submission requirements and policies are checked:
- GitHub Marketplace for a repository app/action that performs a narrow, auditable workflow.
- Python Package Index (PyPI) for the CLI package after name, ownership, licensing, security and supply-chain checks.
- VS Code extension marketplace only after the product has a tested editor workflow and privacy documentation.

Do not claim a listing exists until the marketplace accepts and publishes it. Marketplace names, policies and availability must be checked again at submission time.

## Stage 3 — Desktop and mobile distribution
- Desktop first if repository access, local runners, and recovery controls are central to the value proposition.
- Mobile should initially be a secure companion for task status, approvals, notifications and evidence review—not an unrestricted code execution surface.
- Android/iOS store submission requires a real app shell, tested authentication, secure secret handling, privacy disclosures, support URL, signing keys and store review. No app-store build or listing is included in this alpha.

## Stage 4 — Team and enterprise
- Shared workspaces, role-based approvals, audit exports, retention policies, private runners and SSO.
- Enterprise claims require security review, backup/restore exercises, incident response, privacy/legal review and support readiness.

## Go-to-market loop
1. Show a reproducible demo with a known repository issue.
2. Produce a baseline report and an evidence-backed repair proposal.
3. Show exact diff and test output; user approves changes.
4. Export a redacted result and invite a second maintainer to review it.
5. Measure repeat usage, repair acceptance, regression rate, and cost per successful task.
6. Convert repeated individual use into team workflows only when user interviews and usage data support it.

## Release blockers
- License/IP choice has not been established by this roadmap.
- Package build, clean install, CLI smoke test, end-to-end repository task, and CI pass must be recorded.
- Local SQLite memory currently lacks encryption and remote backup.
- Real multi-provider adapters, actual repair execution, app UI, store metadata, and marketplace listings remain future work.
- Do not market autonomous trading or guaranteed financial returns. Ω-CAP remains research/paper mode only.

## Truthful status
This file defines a launch path. It does not mean the program has been submitted to, accepted by, or published in any marketplace.
