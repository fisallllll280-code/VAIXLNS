# VAIXLNS — Official Website v1

A standalone, bilingual, responsive informational landing page for VAIXLNS as a multi-product technology brand.

## Preview locally

No package manager, build step, credentials, or external API required. Open `index.html` directly in a modern browser, or from the repository root:

```bash
python -m http.server 8765 --directory website/official-v1
```

Then visit `http://localhost:8765`. This does not deploy the website.

## Scope

- Arabic-first, English-toggle UX; responsive for desktop and mobile.
- Product catalog: VX Studio, VAIXLNS AI, VV OS, Ω Reality Forge, VAIXLNS Market, Ω Arena.
- Honest development/planned labels; no authentication, payments, model calls, analytics, tracking, or launch functionality.
- No production domain or hosting configured.

## Smoke checks

```bash
python website/official-v1/test_site.py
```

Open on a desktop browser and on iPhone Safari; verify responsive layout, language toggle, section links, and keyboard focus. Browser and device tests require actual runs and cannot be inferred from file existence.

## Boundaries

This site is a **static informational MVP**. It does not establish any live agent, provider, payment, OS, or federation integration. Preserve `project.genome` and `Ω.000`. No merge to main or deployment without explicit approval and appropriate gates.
