# FIE Bulk Portfolio Onboarding

## Purpose

FIE now separates the human-managed portfolio from generated research state:

- `config/league-portfolio.json`: the leagues FIE should manage, their strategic format, priority, and custom cohort rules.
- `data/research/leagues/registry.json`: only League-ID namespaces whose historical M1-M6 research actually exists.
- `data/research/leagues/portfolio-status.json`: readiness for every managed league, including leagues not built yet.

This prevents a failed/new league from making the production research registry invalid.

## Managed portfolio

The configuration contains 19 leagues: 4 Chopped, 3 Redraft, 2 Redraft + Best Ball, 7 Dynasty, and 3 Dynasty + Best Ball.

Two Dynasty leagues have fixed cohort rules:

- `1316165875291668480`: entry class 2025+ remains permanently unrestricted. The fixed pre-2025 legacy cohort is capped at 15 in 2026, 10 in 2027, 7 in 2028, 4 in 2029, and 1 from 2030 onward.
- `1342896584593018880`: only entry class 2025+ is eligible. The cohort floor stays fixed, so additional rookie classes naturally expand the legal player universe each year.

These constraints are included in the research profile fingerprint and enforced by the browser decision engine.

## Workflow

Use GitHub Actions → **Bulk Onboard FIE Portfolio**.

### First run: PLAN_ONLY

Recommended inputs:

- Mode: `PLAN_ONLY`
- Priority cutoff: `ALL`
- Max parallel: `4`
- Refresh current: `true`

This makes no repository changes. It resolves the Sleeper username, verifies membership in every league, captures league/draft metadata, follows previous-league history links, compares live fingerprints with existing research, and classifies each league as `CURRENT`, `REFRESH_ONLY`, `NEW`, `PROFILE_CHANGED`, or `ERROR`.

### Second run: FULL

After reviewing the plan:

- Mode: `FULL`
- Priority cutoff: `ALL`
- Max parallel: `4`
- Refresh current: `true`

Historical builds run in isolated parallel jobs. Individual jobs never push to GitHub. Successful League-ID artifacts are uploaded temporarily; failed leagues produce no artifact and cannot overwrite existing research. A final merge job downloads successful artifacts, rebuilds the generated registry/status, validates every namespace, refreshes current snapshots, runs production readiness, and commits once.

## Failure behavior

A single league failure does not erase or block successful leagues. The failed league remains visible in Portfolio Home with fallback behavior/status, while complete League-ID namespaces remain usable.

## Portfolio Home

`app/portfolio-config.js` loads the central portfolio and syncs the managed list into the existing browser saved-league cache. Portfolio Home therefore shows all managed leagues automatically on each device after the config loads. Deep recommendation snapshots remain League-ID-specific and browser-cached.

## Existing single-league workflows

The existing **Build FIE Research Milestones 1-6** and **Refresh FIE Current Season** workflows remain available. Single-league builds now also read `config/league-portfolio.json`, so custom cohort constraints are fingerprinted consistently whether a league is built individually or through bulk onboarding.
