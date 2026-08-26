# Fantasy Intelligence Engine

League-specific fantasy-football decision support for Sleeper leagues.

## Current release

**9.2.1 Current Snapshot Storage**

This repository contains the browser application, Cloudflare Pages Functions, league-specific M1-M6 research artifacts, governance, tests, and deployment tooling.

The production architecture is intentionally fail-closed. Candidate research/model logic may be visible diagnostically without being permitted to alter production recommendations.

## Start here

- [Architecture](docs/current/ARCHITECTURE.md)
- [Consolidation sprint](docs/current/CONSOLIDATION_SPRINT.md)
- [How to change the codebase](docs/current/CHANGE_GUIDE.md)
- [Deployment](docs/current/DEPLOYMENT.md)
- [Release checklist](docs/current/RELEASE_CHECKLIST.md)
- [Model governance](docs/current/MODEL_GOVERNANCE.md)
- [Data contracts](docs/current/DATA_CONTRACTS.md)
- [Current snapshot storage](docs/current/CURRENT_SNAPSHOT_STORAGE.md)
- [Testing](docs/current/TESTING.md)
- [Security](docs/current/SECURITY.md)
- [D/ST integration foundation](docs/current/DST_INTEGRATION_GUIDE.md)
- [D/ST implementation & evaluation](docs/current/DST_IMPLEMENTATION_AND_EVALUATION.md)
- [Kicker Intelligence implementation](docs/current/KICKER_INTELLIGENCE_IMPLEMENTATION.md)
- [Release handoff / what to change](docs/current/HANDOFF.md)

Historical milestone/version documents have been moved to `docs/archive/` so the repository root stays usable.

## Repository layout

```text
app/                     Browser runtime and feature modules
  core/                  Canonical shared services
  generated/             Generated browser contracts/configuration
config/                  Source configuration and release contracts
data/research/            Full research and namespaced league artifacts
docs/current/             Living documentation, source of truth
docs/archive/             Historical milestone/release documentation
docs/audits/              Formal audits
functions/                Cloudflare Pages Functions
research/                 Research pipeline, governance and integrity tests
tools/                    Build/release utilities
dist/                     Generated Cloudflare static output, never hand-edit
index.html                Legacy-compatible application shell
wrangler.toml             Cloudflare Pages build-output configuration
```

## Build

Preferred one-command personal release build:

```bash
python tools/release_build.py --mode personal
```

For a sanitized public build:

```bash
python tools/release_build.py --mode public
```

The script regenerates runtime contracts, model configuration and release metadata, creates the final source hash manifest, rebuilds `dist/`, and runs the bounded release gate. `dist/` is the deployable static output. Do not deploy the repository root.

## Important

The current V9.1 decision model is a **candidate** unless `config/model-config.json` contains a promoted production artifact. The runtime automatically stays on the governed V8.9 fallback when V9 is not promoted.

### Kicker Intelligence
Leagues that start K now receive a specialist Kicker Intelligence path. The model projects kick opportunity, distance and conversion before applying exact league scoring, including per-yard FG scoring and distance-specific miss penalties. Weekly output includes replacement-aware streaming signals and a PAY / WAIT / STREAM draft recommendation. See `docs/current/KICKER_INTELLIGENCE_IMPLEMENTATION.md`.

### Shared current-snapshot storage

League-specific `milestone5_current.json` files are now lightweight manifests. Shared invariant player data and scoring-specific projection overlays live under `data/research/shared/current/`, and the browser hydrates the unchanged logical M5 contract through `app/current-snapshot-store.js`. This removes roughly 96% of duplicated current-snapshot source storage across the 19 managed leagues.
