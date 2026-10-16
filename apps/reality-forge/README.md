# VAIXLNS Ω Reality Forge — UI Prototype v0.1

## Purpose
A self-contained, responsive, browser-only command-center prototype for inspecting the four-system federation, agent role templates, evidence admission gates, local intent drafts, and canonical source references.

## Run
Open `index.html` directly in a modern browser. No package manager, build step, server, or external dependency is required.

## Core repository screens
Open `core-repositories.html` directly in a modern browser for the dedicated repository workspace. It provides separate anchor-navigation screens for:
- VAIXLNS canonical control plane
- VAIXLNS-unified integration workspace
- VX-runtime execution boundary
- NEXENT discovery and architecture search
- vaixlns-core and vaixlns-csd-kernel
- Build, execution, naming, and operational-assurance contracts

The repository screens are based on `docs/REPOSITORY_MAP.md` and `docs/INTERFACE_ARCHITECTURE.md`. They show declared roles and verification gates, not live service health.

## Current capabilities
- Navigate between command center, federation, agent mesh, evidence vault, event timeline, and canonical index.
- Select a system or agent role to inspect its declared state and next evidence gate.
- Filter agent roles and evidence records.
- Draft an engineering intent locally in the page; the form explicitly does not dispatch it.
- Reset the demo view.
- Navigate the core repository role map and inspect each repository boundary and required evidence.

## Truth boundary
These are **UI prototypes / static role and snapshot data**, not a connected control plane. They do not call model providers, execute agents, read GitHub live, dispatch tools, write a ledger, or mutate canonical state. Counts and statuses are snapshot/demo content and must be replaced by source-backed API responses before production use.

The current data reflects repository evidence:
- `project.genome` is the canonical source.
- `registry/omega/omega-000-master-index.json` is the canonical `Ω.000` master index.
- `registry/vx-runtime-role-binding-map.v1.json` declares `PROPOSED_NOT_ACTIVE`.
- `VLNS ↔ NAXLNS` and `NEXNET ↔ NEXENT` identity mappings remain `UNVERIFIED` in the reconciliation snapshot.

## Non-negotiable integration gates
1. Read-only API adapters first; attach source ref, commit, timestamp, and digest to each returned record.
2. Runtime tool calls must pass an admitted `BoundEngineeringToolDispatcher + VX_FEDERATION_GATE` policy path.
3. Unknown or unconfigured adapters fail closed to `NOT_CONFIGURED_HOLD`.
4. Separate contradiction detection from evidence admission.
5. `VERIFIED` requires reproducible executable evidence; `CANONICAL` requires verified evidence plus explicit authority.
6. No self-approval, no automatic canonical promotion, and no writes to `project.genome` or `Ω.000` from the UI.

## Next integration slice
Add a typed, read-only status API backed by existing federation preflight and Omega Arena audit receipts; keep sample data visually marked until each record carries verifiable provenance. Add a separate approved command endpoint only after negative/bypass tests and independent review pass.
