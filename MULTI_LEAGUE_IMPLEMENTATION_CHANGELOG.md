# FIE Multi-League Research Architecture, Phase 1 + Runtime Migration

## Goal
Make the empirical M1-M6/current/governance stack permanent per Sleeper League ID so switching between Redraft, Chopped, Dynasty, Best Ball, IDP, Superflex, or other saved leagues never requires rebuilding another league's research.

## Repo-specific migration source
The committed legacy `data/research/milestone1.json` identifies League ID `1313697754907697152` in its embedded Sleeper scoring provenance. The migration workflow validates this provenance before copying anything.

## Implemented

### League-ID namespace
Research now lives under:

`data/research/leagues/<league_id>/`

with:
- `profile.json`
- `milestone1.json` through `milestone6.json`
- `current/milestone5_current.json`
- `governance/operator_override.json`
- `governance/active_release.json`

A global `data/research/leagues/registry.json` tracks enabled league profiles and scheduled refresh eligibility.

### Exact league profile contract
`research/league_profile.py` captures:
- League ID and name
- explicit strategic format
- exact Sleeper scoring settings and 16-character research scoring signature
- roster positions
- Sleeper settings
- team count
- season/season type
- 64-character profile fingerprint

Chopped remains an explicit format because Sleeper has no canonical chopped-league type.

### Historical workflow isolation
`.github/workflows/build-fie-research.yml` now requires a League ID and writes M1-M6 only into that League ID's namespace. Derived/cache files are also isolated per League ID. The workflow fails if a league-specific run modifies a legacy/global generated artifact.

### Artifact identity stamping
Every namespaced M1-M6 bundle is stamped with:
- `league_id`
- `league_format`
- `profile_fingerprint`
- `profile_scoring_signature`

Stamping fails if the empirical scoring signature disagrees with the captured profile.

### Non-destructive legacy migration
`.github/workflows/migrate-fie-redraft-profile.yml` copies the existing M1-M6 profile without editing or deleting the global source files. It builds the migration profile from the exact historical M1 scoring, not from a guessed current scoring configuration. A current Sleeper scoring mismatch is recorded instead of silently rewriting history.

### Current-season multi-league refresh
`.github/workflows/build-fie-current.yml` can refresh one League ID or every enabled League ID in `registry.json`. Scheduled runs iterate registered leagues sequentially and commit successful league updates together.

### Live profile drift protection
`build_current_snapshot.py` now checks both:
- exact current scoring signature
- full current League-ID profile fingerprint, including roster/settings configuration

If the current Sleeper league settings have changed since historical research was generated, empirical activation fails closed and a historical rebuild is required.

### Per-league + global governance
Each league has independent governance. Activation requires:
- League ID match
- profile fingerprint match
- current live profile match
- strategic format match
- artifact path namespace match
- scoring match
- M4/M5/M6 completion
- fresh current snapshot
- leakage guard
- eligible players
- SHA-256 integrity

The existing global `data/research/governance/operator_override.json` remains an emergency kill switch. Global `CONTROL` disables empirical overrides for every league.

### Browser switching safety
The browser no longer fetches global M1-M6 paths. It derives all research paths from the currently loaded Sleeper League ID.

On every league change it:
1. invalidates the previous research state,
2. closes M5/M6 governance,
3. resets SHA-256 verification,
4. loads only the new League ID namespace,
5. discards late responses belonging to a previous league.

A league without a generated research profile still uses the normal fallback engine and does not break the app.

## Validation completed
- Python compile checks
- original M1, M2, M3, M4, M5, M6 integrity tests
- V8.9 integrity/rollover/scoring/statistical guardrail test
- multi-league namespace/governance isolation test
- profile/fingerprint fixture test
- JavaScript syntax check across all inline scripts
- stamped copies of the real M1-M6 bundles revalidated successfully
- migration source files verified byte-identical after migration
- migration rerun verified idempotent
- global CONTROL verified to override otherwise valid per-league AUTO governance
- cross-league artifact injection verified to fail closed

## 2026-08-25 Research Integrity + Draft UI hotfix

- Unified immutable Sleeper benchmark timing across capture paths: regular season only, verified kickoff, <=18h window.
- Current snapshot now distinguishes Sleeper preseason state from regular-season analysis week.
- Added full-history M2 waiver panel and M5 contract revision 3 with an attainable >=4-fold chronological promotion gate.
- Strengthened production-readiness checks and added one-time market-archive quarantine workflow.
- Draft Assistant League Rank is stable across drafted-player removal; Value vs ADP uses identical ADP-covered eligible samples.
- Added model-aware Draft Assistant sorting and generic sortable-table support.

## 2026-08-25 Research Governance hotfix R4

- Fixed Spearman/correlation alignment across M1/M2/M3/M4/M5/M6 helpers by resetting positional indexes before paired correlation calculation.
- M5 waiver contract revision 4 now separates forecast validation from decision-ranking validation and requires both before live waiver promotion.
- Waiver ranking quality is evaluated within weekly decision sets, then aggregated chronologically by holdout season.
- Added paired waiver ranking diagnostics: Spearman improvement vs recent points, top-quartile precision, and top-pick regret.
- Current-season server snapshots now enforce the same decision-specific format gates used by the browser for weekly and waiver activation.
- Production readiness rejects revision-4 waiver gates that expose a position without both forecast and ranking validation.
- Extended integrity tests cover index-misaligned correlations, attainable revision-4 waiver promotion, and server-side REDRAFT/CHOPPED format gating.

## Bulk Portfolio Onboarding

- Added central 19-league managed portfolio configuration with priority and format metadata.
- Added fixed-entry-cohort rules for two custom Dynasty formats and included them in research fingerprints.
- Added browser enforcement for cohort eligibility and fixed legacy-veteran caps.
- Added `PLAN_ONLY` bulk preflight with Sleeper membership, drafts, league history, live fingerprints, and per-league build state.
- Added failure-isolated parallel M1-M6 matrix builds with one final merge/commit.
- Added machine-generated `portfolio-status.json`; unbuilt/failed leagues no longer pollute the production research registry.
- Portfolio Home now syncs the central managed portfolio into the browser and shows priority/research readiness badges.
