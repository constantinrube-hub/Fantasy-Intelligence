# V9.3.2 Season Namespace Integrity Hotfix, 2026-08-27

- Fixed the root cause behind the three successive live Season bootstrap failures introduced during V9.3.2 browser QA. The new early resolver had reused `window.FIESeasonContext`, but `runtime-foundation.js` already owned that global for its `active/prior/week/snapshot` facade and overwrote the resolver during startup.
- Established non-overlapping season APIs: `FIESeasonBootstrapResolver` for pre-core startup, `FIECore.SeasonResolver` for canonical strict season resolution after core load, and `FIESeasonContext` for the runtime active/prior/next/week/snapshot facade.
- `activeSeason()` no longer calls `FIESeasonContext.resolve`; it prefers the canonical `FIECore.SeasonResolver` and otherwise uses the isolated bootstrap resolver.
- Added a compatibility `resolve()` delegate to the runtime `FIESeasonContext` so a stale cached V9.3.2 shell cannot crash while Cloudflare assets roll over.
- Cache-busted the season/numeric/runtime scripts and added Cloudflare revalidation headers for `index.html` and `/app/*` to reduce mixed-version HTML/JS during deploys.
- Strengthened the actual season runtime regression to reproduce the namespace overwrite that caused `window.FIESeasonContext.resolve is not a function`.

# V9.3.2 Season Bootstrap Resilience + Dist Determinism Hotfix, 2026-08-27

- Fixed the browser failure `League universe build failed: FIE season context is unavailable`. The canonical external `app/core/season-context.js` remains the preferred season service, but `index.html` now installs an equivalent strict inline bootstrap only when the external helper is unavailable. League loading therefore no longer hard-fails because one tiny static asset was missed, stale, or temporarily unavailable at the edge.
- Changed the season-context request to an absolute, cache-busted asset path so Cloudflare/browser cache state cannot accidentally reuse an older missing asset response.
- Preserved the core season contract: loaded Sleeper league season is authoritative; null, blank, `0`, and `"0"` are invalid; a loaded 2026 league resolves to 2026 in both canonical-service and bootstrap-fallback modes.
- Strengthened `integrity_v932_season_runtime_test.js` to execute the exact failure mode with the external season service deliberately absent. The test now requires league startup to resolve Season 2026 without throwing.
- Fixed a separate release-validation defect where `research/build_app_manifest.py` used wall-clock `datetime.now()` for `generated_at`, making every otherwise identical validation build change `dist/config/build-manifest.json`. The manifest now uses the canonical release descriptor `built_at`, so unchanged release builds are byte-stable.
- Added `integrity_v932_build_determinism_test.py` to the full release gate.
- Full deterministic release build after both fixes: `DEPLOYABLE_SOURCE`, 19-league current-storage integrity PASS, 19/19 structural-profile regression PASS, dist hygiene PASS.

---

# V9.3.2 Deployment Synchronization Hotfix, 2026-08-27

## V9.3.2 bootstrap hotfix — season scope / league-universe startup

- Fixed a browser-only startup regression where the staged league loader invoked `buildPlayerUniverse()` before the later V8.9 compatibility IIFE had defined its private `activeSeason()` helper, causing `League universe build failed: activeSeason is not defined`.
- Added `app/core/season-context.js`, loaded before the first inline application script, as the canonical strict season parser/resolver.
- Added a global bootstrap `activeSeason()` binding before any league-universe caller and made the later V8.9 layer delegate to that binding rather than maintaining a second implementation.
- Preserved Sleeper league season as authoritative and explicitly rejects null, blank, `0`, and `"0"` as valid NFL seasons.
- Updated M5 current compatibility to consume the canonical resolved season rather than independently coercing the season selector.
- Strengthened the season runtime regression to verify actual browser script ordering/scope, not only the helper algorithm. The test now fails if `activeSeason()` is defined after `buildPlayerUniverse()`, which is the exact defect that escaped the previous gate.


The V9.3.2 source update and both validation/refresh workflows executed correctly, but the browser remained on V9.3.1 because Cloudflare Pages is configured to serve the tracked `dist/` directory and the original V9.3.2 overlay patch did not include `dist/`. The validation workflow rebuilt a correct V9.3.2 `dist/` only inside the temporary Actions runner and uploaded it as an artifact; it did not commit that generated tree back to `main`. The Current Season workflow likewise refreshed source research artifacts without rebuilding `dist/`.

This hotfix makes deployment synchronization enforceable:

- adds a manual **Rebuild FIE Deploy Dist** workflow that runs the deterministic release builder and commits the validated `dist/` tree;
- makes **Validate FIE V9.3.2 Browser QA** fail if committed `dist/` differs from the deterministic release build;
- makes **Refresh FIE Current Season** rebuild and commit `dist/` after refreshing league data so deployed current snapshots cannot lag the source store;
- adds `dist/**` to validation triggers.

The source-side Season-0 fix was already present in V9.3.2. The live Season 0 display persisted because the deployed `dist/index.html` was still V9.3.1.

---

# V9.3.2 Browser QA & Ranking Integrity, 2026-08-27

## Why this release exists

V9.3.1 passed the deterministic source/release gates but the first real browser QA exposed runtime-semantic defects that static and isolated tests did not catch. V9.3.2 treats those findings as one integrity sprint rather than a collection of cosmetic fixes. The release repairs missing-data semantics, season resolution, current-research fingerprinting, cross-surface ranking consistency, draft-state synchronization, panel routing, waiver/trade legality, League Intel identity resolution, Weekly refresh reliability, D/ST/Kicker future-week UX, and tiering.

## P0 correctness fixes

- Added a strict nullable numeric contract in `app/core/numeric.js`. `null`, `undefined`, blank strings and whitespace now stay unavailable instead of becoming JavaScript numeric zero. Genuine `0` and `"0"` remain legitimate zeroes.
- Replaced unsafe optional-number coercion across Weekly, Draft/Players, Value Finder, D/ST, Kicker, roster rules and supporting services with the shared numeric semantics.
- Added `app/core/projection-service.js` as the canonical weekly projection resolver. Projection precedence is governed FIE current projection, direct weekly projection, Sleeper weekly projection, explicitly labelled fallback estimate, then unavailable. A verified bye remains a genuine zero and is never confused with unavailable data.
- Fixed the separate `Season 0` defect. Blank or `"0"` season-selector values can no longer win over the loaded Sleeper league season. The loaded league season is authoritative across Weekly URLs, schedule matching, projection loading, weather/odds matching and season-sensitive runtime diagnostics.
- Corrected current-profile fingerprint generation in `research/build_current_snapshot.py` to use the same `structural_contract()` as `research/league_profile.py`. Operational Sleeper settings such as `leg` and `daily_waivers_last_ran` no longer cause false research invalidation.
- Added an offline 19-league structural regression. All 19 captured live Sleeper profiles reproduce their stored structural fingerprint under the corrected contract, proving the prior portfolio-wide mismatch was contract drift rather than 19 genuine structural changes.
- Fixed optional managed-roster cap parsing. `null`, undefined and blank mean unlimited; explicit `0` remains a real zero-player cap. This removes false trade violations such as `R 7/0` and prevents the same bad caps from eliminating otherwise legal waiver candidates.
- Added canonical Sleeper-ID-to-position resolution for transaction analysis so League Intel no longer fails on the missing `playerPosBySleeperId` helper.

## Canonical ranking and decision architecture

- Added `app/core/draft-value-service.js` as the canonical roster-neutral Draft Base Value service.
- Draft Board, Players, Value Finder and Draft Assistant now share one underlying FIE player-quality/positional-rank foundation.
- Market price is explicitly excluded from canonical FIE player-quality rank. ADP/market position is compared after FIE valuation for price, timing and value-gap decisions.
- Value Finder no longer manufactures a competing "FIE positional rank" from its discovery policy score. It consumes the canonical FIE rank and then layers market inefficiency, role path, evidence and timing on top.
- Draft Assistant now starts from the same canonical Draft Board base value before applying intentionally roster-aware/current-pick effects such as exact roster marginal, timing, next-pick survival and Best Ball portfolio fit.
- Draft Assistant displays the intended three recommendation cards: Best Pick, Alternative and Value Play, with Board rank, Decision rank, FIE-vs-market positional context, roster delta, survival estimate and explanation.
- Large Board-to-Assistant rank movements are now traceable to roster/timing effects rather than appearing as an unexplained second valuation system.
- Added `app/core/draft-state-service.js` so Draft Board-related workflows use one synchronized draft ID/pick set/picked-player state. Value Finder's "Undrafted only" filter and Draft Assistant consume the same picked-player IDs.
- Replaced the old adjacent-gap tiering heuristic with canonical value-based tiering that uses normalized base value, local gap behavior, cumulative decay, league size and a Tier-1 sanity constraint. Runaway 70-player Tier 1 outputs are blocked by regression tests.
- Best Ball ranking now combines normalized base/replacement value with normalized ceiling/spike inputs rather than adding incompatible raw scales. Player detail explains Spike/Balanced/Volume-style profiles and labels heuristic ranges as estimates.

## Weekly reliability and season handling

- Weekly now renders missing data as unavailable rather than `0`.
- Added explicit source lineage and fallback status to weekly projection resolution.
- Split Weekly refresh into bounded essential and optional work. Schedule/Sleeper projections are prioritized; odds, weather, snaps, depth and other enrichment are allowed to finish independently.
- Added per-source deadlines, stale-generation protection, league-ID checks and reliable finalization so a failed/stale refresh cannot leave the Refresh button stuck indefinitely.
- Season resolution now rejects blank, zero and invalid selectors and synchronizes back to the real Sleeper league season.
- Added an executable regression against the actual `index.html` `activeSeason()` implementation proving a loaded 2026 league cannot display or request Season 0 because the selector is blank or `"0"`.

## D/ST and Kicker

- Rebuilt D/ST and Kicker nullable projection handling so absent P10/P90/Next-3 values display as unavailable instead of fabricated `0.0`.
- Added `app/core/special-teams-series.js` for shared special-teams week-series logic.
- Added Week 1-18 selectors to D/ST and Kicker decision surfaces.
- Future-week rows use published Sleeper projections when available and otherwise remain clearly labelled baseline estimates.
- An unknown future schedule can no longer masquerade as a bye. Only a verified schedule with no team game produces a true BYE zero.
- D/ST and Kicker rows now open the normal player/detail drawer architecture with Overview and Weeks 1-18 views, replacement context, action, source and confidence.

## Surface routing and browser-state integrity

- Added `app/core/surface-router.js` as the authoritative panel visibility/transition helper.
- Registered the dynamically created Matchup & Playoff panel with the shared surface router.
- Leaving Matchup for Team, Roster Assets, Market, Waivers, Trade, Players, Draft or other sections now explicitly hides/unmounts the Matchup panel instead of allowing it to leak into unrelated tabs.
- Added runtime navigation regression coverage that opens Matchup and then transitions away, asserting the panel is inactive and hidden.

## League Intel, Waivers and Trade

- Added canonical player-identity lookup for transaction profiling and repaired League Intel's add/drop/FAAB position resolution.
- Waiver empty states now preserve diagnostics about candidate counts and legality/upgrade rejection rather than presenting a mysterious empty board.
- Trade and waiver portfolio-rule evaluation share corrected optional-cap semantics.
- Dynasty Players visually prioritizes Asset Rank immediately after Player, matching the default cross-positional sort.

## Data quality and diagnostics

- Public enrichment diagnostics retain per-source status, rows, latency/error and checked time instead of relying only on a 3/4 summary.
- Added ranking/source lineage to the player drawer so canonical FIE position/overall rank, market position, value gap, base value, tier, projection source, evidence confidence and relevant format inputs are traceable.
- Corrected feature copy to emphasize what each surface does rather than repeatedly explaining format differences in boilerplate.

## New/updated integrity coverage

- `research/integrity_v932_structural_profile_test.py`: validates the corrected structural fingerprint contract against all 19 captured league profiles.
- `research/integrity_v932_source_contract.py`: static/source contract for V9.3.2 modules and corrected semantics.
- `research/integrity_v932_browser_qa_runtime_test.js`: executable runtime regression for null semantics, projection fallback, byes, roster caps, canonical rank/tiers, draft-state exclusion, panel cleanup and special-teams future-week behavior.
- `research/integrity_v932_season_runtime_test.js`: executes the actual `index.html` season resolver and proves blank/zero selector state cannot produce Season 0 for a loaded 2026 league.
- V9.3.2 checks are included in both the full release gate and the Refresh FIE Current Season workflow.
- The GitHub validation workflow is renamed in the Actions UI to `Validate FIE V9.3.2 Browser QA` and uploads a complete validation artifact.

## Final local release result

- Deterministic command: `python tools/release_build.py --mode personal`
- Result: `STATUS: DEPLOYABLE_SOURCE`
- Current-storage integrity: 19 leagues PASS
- V9.3.2 structural regression: 19/19 PASS
- V9.3.2 browser-QA runtime: PASS
- Actual Season-2026/Season-0 runtime regression: PASS
- Existing V9.3.1 persistent-cache, scarcity, LeagueContext, Decision UI, Value Finder, Top-100, D/ST, Kicker, M5/M6, Monte Carlo and artifact/dist hygiene gates continue to pass.
- Release remains `release-candidate` until the uploaded repository has completed a fresh connected Current Season refresh and live browser acceptance pass.

# V9.3.1 Completion Patch

- Finished the V9.3 runtime consolidation with a persistent browser cache for stable shared NFL/projection proxy data while keeping live league endpoints network-fresh.
- Routed legacy JSON/CSV consumers through the centralized data client and exposed persistent-cache hits in runtime diagnostics.
- Kept core league switching progressive: league/rosters/users/player identity become interactive first; enrichment, projections, trends and research finish in the background. Background completion now includes public enrichment.
- Centralized structural replacement scarcity on starter-slot/FLEX/Superflex demand. Draft Board scarcity is league-structure aware but does not depend on the selected user roster or stale projected replacement cutoffs.
- Added Best Ball-specific roster-neutral Draft Board profiles plus a clearly labelled heuristic Portfolio Fit in Draft Assistant; Team retains Best Ball Contribution Profile.
- Added V9.3.1 completion, persistent-cache and strengthened scarcity regression tests, and wired them into the current/research workflows and release gate.
- Added a dedicated `Validate FIE V9.3.1 Completion` GitHub Actions workflow for a clean post-upload release build and validation artifact.
- Release metadata remains `release-candidate` until the required live browser preview is completed.

# Changelog

## 9.3 Decision UX & Reliability Consolidation, 2026-08-26

- Added canonical `LeagueContext` for starter slots, legal positions, FLEX/SF scarcity, K/DST/IDP capability and preferred Sleeper-owner resolution.
- Auto-selects the `C0nstant1n` roster by Sleeper owner ID when present, independent of team display name.
- Reworked consumer surfaces into purpose-built Draft, Draft Assistant, Value Finder, Team, Weekly, Waiver, Dynasty Buy, Trade, Players and League Intel decision views.
- Kept Draft Board neutral to owned-player roster state while preserving exact league starter demand and replacement scarcity.
- Added positional FIE-vs-market comparisons and Basic/Advanced context-aware player detail views.
- Fixed runtime roster-slot contract consumers to use `.positions` rather than the obsolete `.eligible` property.
- Hardened Value Finder optional-research loading and explicit action states.
- Fixed post-trade roster legality evaluation and modernized the trade builder.
- Added progressive league loading, request deduplication/caching, lazy League Intel history, stale-request protection and performance instrumentation.
- Added V9.3 runtime smoke tests for LeagueContext, preferred-roster/K-DST/SF detection, scarcity and decision-UI initialization.
- Centralized runtime release display on generated release metadata.
- Added [`docs/archive/implementation/V9.3_DECISION_UX_RELIABILITY.md`](docs/archive/implementation/V9.3_DECISION_UX_RELIABILITY.md) as the implementation and QA handoff.

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
