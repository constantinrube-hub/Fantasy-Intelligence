# Fantasy Intelligence Engine V8.9-RTS Deployment Guide

## Recommended deployment path

Your Cloudflare Pages project is already designed around a GitHub repository. Deploy the **repository-root ZIP contents to GitHub**, preserving the directory tree, then let Cloudflare Pages redeploy from the commit.

Do **not** upload only `index.html`: V8.9 depends on the Cloudflare Functions, `/data/research` governance artifacts and GitHub research workflows that are part of this repository.

## Repository tree that must remain intact

```text
/
├── index.html
├── _routes.json
├── wrangler.toml
├── functions/
│   └── api/
│       ├── health.js
│       └── data/
│           └── [[path]].js
├── data/
│   └── research/
│       ├── current/
│       ├── governance/
│       ├── market/
│       └── milestone1.json ... milestone6.json
├── research/
│   ├── *.py
│   └── requirements.txt
└── .github/
    └── workflows/
        ├── build-fie-research.yml
        └── build-fie-current.yml
```

## Cloudflare Pages settings

Keep the existing Pages project connection to the GitHub repository.

- **Framework preset:** None / static site.
- **Build command:** leave empty unless your current project requires one.
- **Build output directory:** `.`
- **Root directory:** leave empty, meaning repository root.
- `_routes.json` sends only `/api/*` through Pages Functions.
- `wrangler.toml` deliberately retains the existing project name to avoid accidentally creating a new Pages project through Wrangler.

## Deployment steps

1. Back up or tag the currently deployed V8.8-M6 commit.
2. Replace the repository contents with the V8.9-RTS package while preserving the tree above.
3. Commit the changes to the branch watched by Cloudflare Pages.
4. Open the Cloudflare Pages deployment and confirm the commit reached **Success**.
5. Open `/api/health` on the deployed domain and confirm:
   - `ok: true`
   - `version: V8.9-RTS`
   - runtime reports Cloudflare Pages Functions.
6. Open the app and hard-refresh once after deployment.
7. Load one known Sleeper league.
8. Confirm the V8.9 integrity strip appears directly below the league connection card.
9. Confirm scoring status is not falsely green if the league contains unsupported rules.
10. Open Draft Assistant, Team Analysis, Trade Center, Weekly/Start-Sit and Validation once each.
11. On iPhone/Safari and desktop Chrome, confirm tabs, table scrolling, drawer open/close and league loading work normally.

## Research workflows

### Historical build

Run **Build FIE Research Milestones 1-6** manually when you want to generate/update the empirical research stack.

V8.9 now resolves the latest conservative completed historical season automatically. You no longer need to edit `2019-2025` every year.

If league-specific scoring replay is required, supply the Sleeper league ID to the workflow.

### Current-season refresh

**Refresh FIE Current Season** is already scheduled during NFL/preseason months and can also be run manually.

- `KEEP`: preserve the versioned operator setting.
- `AUTO`: allow promotion only if every M6 gate passes.
- `CONTROL`: force research overrides off and use the fallback engine.

Do not manually edit `active_release.json` to make it green. The workflow/governance builder should produce it.

## Expected first-deploy governance state

The repository currently ships with M1-M6 in `pipeline_ready_not_run` state. Therefore a first V8.9 deployment should remain on the corrected fallback engine. This is expected.

A research override activates only after:

- M4, M5 and M6 are complete and compatible,
- current snapshot is complete and fresh,
- scoring signatures match,
- target-week leakage guard passes,
- eligible players exist,
- operator mode is AUTO,
- and browser-side SHA-256 verification matches the governance manifest.

## Rollback

Fastest safe rollback:

1. In GitHub, revert the V8.9 commit or redeploy the tagged V8.8-M6 commit.
2. If only empirical overrides need to be disabled while keeping V8.9 code, run the current-season workflow with `CONTROL` mode.

`CONTROL` keeps the app usable while preventing M5/M6 research-driven overrides.

## Post-deploy smoke checklist

- [ ] Home page says V8.9.
- [ ] `/api/health` says V8.9-RTS.
- [ ] Known Sleeper league loads.
- [ ] Integrity strip appears.
- [ ] Scoring coverage appears plausible for that league.
- [ ] No `ADP=0` players rise to the top as valid market values.
- [ ] Draft Assistant sorts by market/ADP presentation while decisions use league value.
- [ ] Draft survival is labelled empirical only when sufficient saved history exists, otherwise heuristic.
- [ ] Trade Center future-pick note mentions probabilistic slot prior.
- [ ] Best Ball team utility reports optimal-lineup simulation over the loaded horizon.
- [ ] Chopped is described as survival strength, not a calibrated elimination probability.
- [ ] Weekly Low/High labels do not imply calibrated P10/P90 when fallback uncertainty is heuristic.
- [ ] Mobile drawer closes correctly.
- [ ] Browser console shows no uncaught app exceptions.

## No additional Cloudflare secret is required for the core app

The existing proxy is allowlisted and core Sleeper/nflverse access does not require a secret. The optional odds key remains user-provided in the application if that feature is used.
