# FIE Research Integrity + Draft UI Hotfix

Date: 2026-08-25

## Scope

This release fixes four release-candidate research integrity findings and two Draft Assistant usability/ranking issues.

### Research integrity

1. **Unified Sleeper market timing policy**
   - Benchmark capture requires regular season.
   - Capture requires a verified regular-season first kickoff.
   - Capture is allowed only in the final 18 hours before first kickoff.
   - `build_current_snapshot.py` can no longer bypass the dedicated capture policy.
   - M4 independently rejects snapshot files that lack capture-policy-v2 timing evidence.

2. **Preseason/regular-week separation**
   - Sleeper preseason week numbers are no longer interpreted as regular-season week numbers.
   - During preseason, an automatic current snapshot analyzes upcoming regular-season Week 1 unless `--week` is explicitly supplied.
   - Current snapshots record `season_type`, `sleeper_state_week`, and the analysis-week policy.

3. **Waiver validation full-history panel**
   - M2 now writes `milestone2_waiver_player_week.csv.gz` from the complete historical player-week backbone.
   - The waiver model uses time-safe rolling role/competition features and raw backward-looking role deltas. The globally standardized diagnostic `opportunity_change_score` is excluded from promotion to avoid retrospective scaling leakage. `fp_next3` is retained only as the supervised label.
   - M5 uses expanding whole-season holdouts, normally 2021-2025 on the 2019-2025 backbone.
   - M5 contract revision 3 requires the validation design itself to demonstrate at least four valid folds.

4. **Production readiness strengthened**
   - Eligible Sleeper benchmarks without auditable timing evidence are errors.
   - Legacy M5 bundles that cannot reach their four-fold waiver gate are warned for rebuild.
   - Revision-3 bundles that cannot reach their own gate are errors.
   - Old current snapshots without season-type semantics are flagged for refresh.

5. **Invalid August 2026 Week-3 benchmark repair**
   - `repair_market_archive.py` quarantines unverifiable eligible snapshots outside the M4 benchmark root rather than deleting the evidence.
   - `Repair FIE Market Archive` GitHub Action performs the repair and commits it.

### Draft Assistant

1. **Stable League Rank**
   - League Rank is now calculated over the complete league-eligible draft universe, including already drafted players.
   - Roster fit and stack synergy are excluded from League Rank because they are personal, changing decision inputs.
   - A separate `available decision rank` remains dynamic and reflects current roster construction.

2. **Sample-consistent Value vs ADP**
   - Raw Sleeper ADP remains unchanged and is used for market timing/survival.
   - Sleeper ADP rank is calculated within the full league-eligible players that have usable ADP.
   - The league model is re-ranked over that exact same ADP-covered player intersection.
   - `Value vs ADP` is the difference between those two directly comparable ranks.

3. **Sortable tables**
   - Draft Assistant supports model-aware full-pool sorting by ADP, Player, League Rank, Value vs ADP, survival and recommendation before Top-75/150 slicing.
   - Other standard data tables receive click-to-sort behavior through `app/table-sort.js` unless they already have model-aware sorting.

## Required post-deploy workflows

1. Run **Repair FIE Market Archive** once.
2. Rebuild **Build FIE Research Milestones 1-6** for each League ID whose waiver research should use revision 3.
3. Run **Refresh FIE Current Season** for each League ID so preseason/regular-week semantics are regenerated.
