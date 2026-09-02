# Deployment Guide

## Recommended one-command release build

For the personal managed-league site:

```bash
python tools/release_build.py --mode personal
```

For a sanitized public build:

```bash
python tools/release_build.py --mode public
```

This is the preferred release entry point because it guarantees the generators, final hash manifest, `dist/` build and bounded release gate run in the correct order. The detailed steps below explain what that command does and are useful for debugging.

## Recommended flow

### 1. Make source changes

Do not edit generated `dist/` output by hand. Controlled implementation packages may carry deterministic `dist/` mirrors, but source owners remain authoritative.

### 2. Generate contracts/configuration

```bash
python research/generate_runtime_contracts.py
python research/generate_model_config.py
python research/generate_release_descriptor.py
```

### 2a. Normalize current-snapshot storage when current data changed

If any `build_current_snapshot.py` run produced or replaced a league current snapshot, normalize the portfolio before governance/release packaging:

```bash
python research/deduplicate_current_snapshots.py
python research/integrity_current_storage_test.py
```

The scheduled current-season and bulk-onboarding GitHub workflows already do this automatically.

### 3. Run fast integrity tests

At minimum:

```bash
node research/integrity_runtime_foundation_test.js
node research/integrity_league_switch_runtime_test.js
node research/integrity_v9_model_runtime_test.js
node research/integrity_decision_service_test.js
node research/integrity_monte_carlo_worker_test.js
python research/integrity_scoring_relevance_test.py
python research/production_readiness.py
```

### 4. Generate the final build manifest

This must happen **after the last source/config change**:

```bash
python research/build_app_manifest.py
python research/integrity_build_manifest_test.py
```

### 5. Build Cloudflare output

For this personal multi-league deployment:

```bash
python tools/build_dist.py --mode personal
```

For a public generic deployment:

```bash
python tools/build_dist.py --mode public
```

### 6. Run release gate

```bash
python research/release_gate.py
```

The safe source state is:

```text
DEPLOYABLE_SOURCE
browser_preview_required = true
```

Candidate decision coefficients may remain **NOT PROMOTED** while the source is deployable. That does not replace the production decision authority: `FIEDecisionService` continues to own the canonical V9 decision route.

Governed current-feature activation is a separate **league-scoped** runtime decision. A league may activate eligible current features only when its lineage and M6 gates pass; another league may remain gated without changing the global production decision authority.

`FIE_DRAFT_V71` is a compatibility fallback if canonical V9 rows are unavailable, not the normal unpromoted production state.

### 7. Commit/push to GitHub

Cloudflare Pages uses:

```toml
pages_build_output_dir = "dist"
```

If Cloudflare builds from Git, configure its build command to run the generation/build pipeline or commit the deterministic generated output according to the controlled workflow. Never treat generated output as the semantic source of truth.

### 8. Preview deploy

Run the browser smoke suite in `TESTING.md` against the preview URL.

### 9. Production deploy

Promote/deploy only after the preview checks pass. A deployment does not itself promote candidate model coefficients.

## What to upload manually

If using Cloudflare direct upload rather than Git integration, upload the **contents of `dist/`**, not the repository root.

Cloudflare Functions remain deployed from the repository `functions/` directory when using the Git/Pages workflow. For manual static-only upload, proxy-backed source routes will not exist unless Functions are deployed separately.
