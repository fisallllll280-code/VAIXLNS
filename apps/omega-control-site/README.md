# VAIXLNS Ω∞ — Reality Forge Control Site (v0.1)

**Scope:** Real, responsive static website with six functioning navigation panels and read-only GitHub public API data. This is *not* a live private VX agent operations gateway.

## Open and run

Open `apps/omega-control-site/index.html` in a modern browser, or serve locally:
```bash
python -m http.server 8000 --directory apps/omega-control-site
```
Open `http://localhost:8000`. No npm install or API key required. GitHub's rate limits, CORS, network policies and repository visibility may prevent live data retrieval. The interface shows unavailable states rather than inventing metrics.

## Views

- Reality Forge overview: live repository count, open PR count and latest Actions outcomes.
- Agents: named role registry (not connected or running external AI).
- Memory: existing design boundary; data unavailable until authenticated backend integration.
- Repositories: live public GitHub info.
- Evidence: latest GitHub Actions runs linked to original source.
- Architecture: VAIXLNS authority, VX runtime, Ω evidence and VN gate separation.

## Security and release boundary

- Frontend is read-only; no client-side secrets, personal tokens, GitHub write actions, production agent activation, paid model usage or trading.
- Do not treat an Actions 'success' as sovereign admission.
- Do not edit `project.genome` or `Ω.000`.
- No deployment, DNS configuration, merge to main or production claims authorized by this branch.

## Next stage

1. Review design, accessibility and branch CI.
2. Connect a backend with user auth + narrow permissions to load live VX agent/memory records.
3. Independently verify evidence, authorization and audit receipts.
4. Add deploy workflow only after explicit release approval.

## Static structural test

`python -m unittest discover -s apps/omega-control-site/tests -v`
