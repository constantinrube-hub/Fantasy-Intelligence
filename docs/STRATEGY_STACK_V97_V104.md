# FIE V9.7-V10.4 Strategy Research Stack

## Purpose

This patch implements the next research/action program without replacing M1-M9 or V9.6.

The permanent separation is:

1. **Football model**: M1-M4, M7-M9, V9.6, V9.7. Never consumes ADP.
2. **League value**: exact league format, replacement level, scarcity and VORP.
3. **Market intelligence**: immutable Sleeper ADP, movement and eventually historical ADP outcome curves.
4. **Decision policies**: M5-compatible Draft/Waiver/Start-Sit research consumers.
5. **Actionable findings**: compact league-level output; it does not mutate canonical player rows.

## Implemented projects

### V9.7 Preseason Engine V2
`preseason_projection_v2.py` is a component-first challenger. It predicts next-season per-game football components from prior role/volume/conversion profiles and scores those components with the canonical league scoring function. It has its own chronological four-fold gate and cannot activate itself.

### V9.8 Market Intelligence
The existing `capture_sleeper_season_market.py` remains the source contract. A new daily workflow accumulates first-write preseason snapshots. The strategy workflow defaults to `AUTO` ADP selection from the existing league profile so redraft/dynasty, reception format and Superflex/2QB markets cannot be mixed accidentally; explicit overrides are provenance-labelled. `fie_strategy_stack.py` calculates ADP movement. Historical ADP outcome curves require an explicit verified preseason-snapshot index; no old ADP is reconstructed from hindsight.

### V9.9 League Value / Outliers
The existing M9 `season_board.csv` remains the player projection input. Replacement level is calculated from the actual league roster positions, including FLEX and SUPER_FLEX allocation. Outputs include VORP, rank edge, ADP-history point edge when verified history exists, and transparent component labels. A single composite 0-100 outlier score is deliberately disabled until historical weights are validated.

### V10.0 Draft Intelligence
Research labels include VALUE_TARGET, DRAFT_NOW_MARKET_MEAN, WAIT_MARKET_MEAN_ONLY and AVOID_AT_MARKET. Empirical probability that a player survives to the next pick remains blocked until actual pick-distribution evidence exists.

### V10.1 In-season actions
`actionable_findings.json` consumes V9.6 weekly/horizon overlays when they exist. It does not duplicate the V9.6 model.

### V10.2 Injury opportunity
Current OUT/IR/DOUBTFUL role is redistributed diagnostically to same-team peers. This is not a trained injury fantasy-point multiplier and cannot activate until prospective pregame availability history is sufficient. `capture_fie_availability.py` plus `Capture Daily FIE Availability Evidence` now creates that immutable point-in-time evidence prospectively using Sleeper IDs, injury/status fields and depth-chart context.

### V10.3 Matchup Intelligence V2
No second matchup engine is created. M8 remains the owner of pressure/pass-rush/coverage/run-front mechanisms. The strategy stack reserves the consumer layer for component-specific M8 research rather than generic matchup multipliers.

### V10.4 Actionable Findings
Outputs are stored under the league-level strategy directory rather than copied into every shared player row, preserving the current deduplicated storage architecture.

## Output directory

`data/research/leagues/<league_id>/performance/<season>/strategy/`

Files:

- `preseason_v2.json`
- `market_movement.csv`
- `adp_outcome_curves.csv`
- `league_value_board.csv`
- `draft_actions.csv`
- `injury_opportunity.json`
- `market_mistake_research.json`
- `actionable_findings.json`
- `strategy_stack.json`

## Preflight/reproducibility hardening

- Cache restoration cannot overwrite newer checked-out league state: committed league files are preserved before restore and overlaid afterwards.
- Split current snapshots are hydrated with the existing `current_snapshot_storage.py` contract before V9.6/injury consumers read them.
- `strategy_stack.json` contains source commit, upstream artifact hashes, resolved ADP market, latest market snapshot hash and per-phase readiness/block reasons.
- Prospective availability evidence is stored separately under `data/research/availability/sleeper/<year>/`.

## Governance

This first release is **research/shadow-only**.

- ADP never enters the football model.
- Canonical weekly projections are not modified.
- V9.6 remains the only newly approved runtime projection layer.
- V9.7 preseason models may become `validated_candidate`, but a separate runtime integration is still required.
- Missing historical ADP or injury evidence is a block, not an excuse for reconstructed data.
- No generic opponent multiplier is introduced.
- No arbitrary combined outlier score is promoted.

## Verified historical market index

Historical ADP-outcome and recurring-market-mistake research is intentionally blocked unless a verified preseason snapshot index is supplied. `research/verified_market_index.example.json` shows the contract. Only snapshots independently known to predate their target season may be listed. This keeps old market research from becoming a hindsight exercise.
