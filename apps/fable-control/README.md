# Fable Control Plane

Repository-first control surface for the VAIXLNS/NEXENT federation.

## Controls

- Provider status
- Target repository
- Audit
- Re-index
- Engineering-plan generation
- Verification
- Controlled proposal

## Security boundary

The browser contains **no GitHub token and no Anthropic credential**.
Actions are queued through GitHub Actions/server-side adapters.

The external `claude-fable-5.md` repository is reference data only. It is not automatically installed as a system policy.

## Architecture

```
UI
 ↓
GitHub workflow / API adapter
 ↓
NEXENT provider fabric
 ↓
Fable worker
 ↓
Artifacts + evidence
 ↓
Tests / proof
 ↓
VAIXLNS governance
```
