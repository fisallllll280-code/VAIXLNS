# VX DESIGN Ω — Interactive Design Studio Prototype

**Status:** `PROTOTYPE` — not production-ready, not connected to VX, and not a live MagicPath integration.

## Preview

Open `index.html` in a browser, or use the GitHub Pages / static preview workflow approved for this repository. The prototype is a single-file, responsive Arabic-first RTL dashboard with:
- Design workspace and prompt presets
- Concept project cards and local draft creation
- Proposed specialist design-agent roles
- Quality-gate checklist
- Integration status panel
- Exportable JSON status snapshot

## Explicit limitations

- Generated concepts are browser-page state only; no backend persistence.
- The prompt is **not** sent to an AI provider and does not generate actual application code.
- Agent cards describe proposed roles, not deployed agents.
- Quality gates are specified, not executed.
- VX runtime and model-provider integrations are not connected or tested.
- No changes are made to `project.genome` or `Ω.000`.

## Next implementation gates

1. Add repository-native tests and accessibility checks.
2. Move UI into the project's approved frontend stack after inspecting its actual layout.
3. Define a versioned API contract for VX Design requests, results, and evidence receipts.
4. Add provider adapters behind the existing VAIXLNS governance and authorization gates.
5. Run visual regression, responsive, interaction, build, and security checks.
6. Require human approval before production release.

This prototype intentionally avoids claiming implementation or verification beyond what exists in the file.
