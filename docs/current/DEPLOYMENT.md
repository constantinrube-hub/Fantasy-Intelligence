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

Do not edit `dist/`.

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

Expected safe state before V9 empirical promotion can be:

```text
RESEARCH_ARTIFACT_READY
RUNTIME_FALLBACK_ONLY
DEPLOYABLE_SOURCE
```

Research being fail-closed is not itself a deployment failure because the governed fallback remains active.

### 7. Commit/push to GitHub

Cloudflare Pages now uses:

```toml
pages_build_output_dir = "dist"
```

If Cloudflare builds from Git, configure its build command to run the generation/build pipeline or commit the generated `dist` only if that is your chosen workflow. The recommended repository workflow is to build `dist` during CI/deployment, not hand-edit it.

### 8. Preview deploy

Run the browser smoke suite in `TESTING.md` against the preview URL.

### 9. Production deploy

Promote only after the preview checks pass.

## What to upload manually

If using Cloudflare direct upload rather than Git integration, upload the **contents of `dist/`**, not the repository root.

Cloudflare Functions remain deployed from the repository `functions/` directory when using the Git/Pages workflow. For manual static-only upload, proxy-backed source routes will not exist unless Functions are deployed separately.
