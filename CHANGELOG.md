# Changelog

## 9.2.1 Current Snapshot Storage, 2026-08-26

- Replaced 19 repeated ~8 MB `milestone5_current.json` player payloads with lightweight league manifests.
- Added content-addressed shared current player bases and scoring-specific projection overlays.
- Preserved exact logical hydration of all 19 pre-refactor source snapshots, including row order.
- Reduced namespaced current-snapshot source storage from ~154.2 MB to ~5.85 MB, about a 96% reduction.
- Deduplicated 19 leagues into 1 compatible shared player base and 17 scoring overlays.
- Added `app/current-snapshot-store.js` as the canonical browser hydrator for M5, D/ST and Kicker Intelligence.
- Reworked `tools/build_dist.py` to perform portfolio-wide shared runtime compaction; the shared runtime current store is ~808 KB and the complete current-snapshot footprint is ~0.98 MB for the present portfolio instead of ~6.63 MB.
- Updated current-season and bulk workflows so full snapshots are built first, deduplicated once, then governed and committed with shared artifacts.
- Added current-storage and deployed-hydration integrity coverage plus living architecture/deployment documentation.

## 9.1.0 Consolidation, 2026-08-26

### D/ST first-class implementation

- Added dedicated team-D/ST research instead of mapping team defense into IDP player models.
- Added exact league-specific D/ST scoring signatures and portfolio inventory.
- Added standard points-allowed buckets plus Genesis return-yard, pass-defense, fourth-down-stop and defensive return-yard scoring.
- Added Sleeper-style points-allowed event attribution and exact scoring integrity fixtures.
- Added lagged team-defense/opponent-vulnerability features and chronological candidate validation.
- Added Week-1-capable prior architecture and fail-closed D/ST activation.
- Added D/ST current snapshot rows only for leagues that actually roster `DEF`.
- Added compact D/ST Intelligence UI backed by canonical 9.1 replacement services.
- Normalized nflverse betting spread to team perspective and corrected opponent implied-points derivation.
- Added D/ST research/current workflow integration and external evaluation guidance.

- Added canonical generated runtime contracts for roster slots, position aliases and scoring relevance.
- Added `FIECore` services for player identity, exact lineup optimization, league-wide demand/replacement, exact roster marginal value, cache fingerprints and diagnostics.
- Added centralized `FIEDataClient` with timeout, abort-scope, response-size and secret-redaction support.
- Added canonical `FIEDecisionService` so Draft Assistant, Value Finder and Monte Carlo select the same production valuation source.
- Reworked league switching around generation IDs and abort scopes.
- Fixed saved-league format mutation across inactive leagues.
- Added native Sleeper Chopped type handling and canonical 3RR sequencing.
- Migrated 19 namespaced league profiles to structural-v2 fingerprints that exclude volatile Sleeper operational fields.
- Reworked Monte Carlo worker serialization, roster reconstruction, lineup utility, common random worlds and cancellation granularity.
- V9 decision weights are fail-closed behind generated model configuration.
- Value Finder current opportunity overlays require full research/governance permission.
- Added clean `dist/` deployment build and changed Cloudflare Pages output from repository root to `dist`.
- Added unified release descriptor/build manifest and explicit repository/runtime readiness semantics.
- Moved historical documentation into `docs/archive/`.

## 9.2 Kicker Intelligence
- Added first-class league-specific Kicker Intelligence alongside D/ST.
- Added exact K scoring replay, including `fgm_yds` and distance-specific FG miss penalties.
- Added historical play-by-play K opportunity/distance/conversion research with chronological fail-closed validation.
- Added governed current-week K raw-outcome projections, risk bands, next-three streaming signal and Sleeper fallback.
- Added Weekly → Kicker Intelligence UI with ADD/START/HOLD/DROP actions and PAY/WAIT/STREAM draft strategy.
- Added 19-league kicker scoring inventory. Current registry: 5 kicker leagues, 0 unsupported K scoring keys.
- Added kicker workflow integration and deterministic integrity tests.
