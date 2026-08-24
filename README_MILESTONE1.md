# Fantasy Intelligence Engine V8.3-M1

This package is the first research milestone built on the supplied V8.2.2 app.

## Deployable app

Use `index.html` as the Cloudflare Pages root file. Keep the included `functions/`, `_routes.json` and `wrangler.toml` structure exactly as shown.

## Historical research bundle

The app expects:

`data/research/milestone1.json`

A safe placeholder is included, so the app deploys normally before historical analysis has been run. In that state, **Lab → M1 Research** explains that the pipeline is ready but no empirical bundle exists yet.

### Recommended generation method

Commit the complete package to GitHub, then run:

**Actions → Build FIE Milestone 1 Research → Run workflow**

Optionally enter a Sleeper league ID. If supplied, historical fantasy outcomes are re-scored to that league's scoring settings before stability/predictiveness/validation tests are run. The bundle reports whether every non-zero rule is reconstructable; unsupported scoring keys are surfaced rather than silently ignored.

The workflow is intentionally manual-only in Milestone 1. It writes and validates `data/research/milestone1.json`, then commits only that compact bundle. Raw historical downloads and derived CSV.gz tables stay out of the deployed website.

## Why the bundle is separate

The historical source data are far too large to embed into the single HTML app. The research pipeline reduces them to compact diagnostics and validated model results. This keeps Cloudflare/mobile loading fast and avoids re-running years of historical analysis in the browser.

## Live-model safety

V8.3-M1 **does not replace the V8.2.2 live projection model**. The new research surfaces are diagnostic only. Integration into Draft/Waiver/Weekly belongs to the next milestone after results have been reviewed.

## Local integrity test

```bash
pip install -r research/requirements.txt
python research/fie_research.py --fixture --output /tmp/m1_fixture.json
python research/validate_bundle.py /tmp/m1_fixture.json
```

This synthetic test verifies the full transformation, scoring, stability, predictiveness and validation code without using fake results in the shipped app.
