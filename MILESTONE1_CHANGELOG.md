# Fantasy Intelligence Engine V8.3-M1 — Milestone 1 Changelog

## Scope

Implements the approved research roadmap through **Step 9** only. The production decision model is deliberately frozen at **V8.2.2**. No historical research signal is allowed to alter Draft, Waiver, Weekly, Trade or Team values in this milestone.

## Step 0 — Frozen control

- V8.2.2 is recorded as `control_build` in every research bundle.
- The UI labels V8.3-M1 as a diagnostic research branch.
- Existing live ranking/scoring functions were not modified.

## Step 1 — Historical data pipeline

- Added `research/fie_research.py` with cached public-source loading.
- Primary analysis window: 2019–2025.
- Extended robustness/cache window: 2016–2025.
- Core source set: nflverse players, weekly player stats, weekly team stats, PFR snap counts, DynastyProcess cross-platform IDs and 2019–2025 PBP reduced to opportunity features.
- Optional broader archive: participation, NGS, PFR advanced stats, rosters, weekly rosters, depth charts, historical injuries through 2024, FTN charting, contracts, draft picks and combine.
- Added reproducible compressed derived outputs: player-week, team-week, player identity, player-season, team-season and game-environment tables.
- Added GitHub Actions workflow to generate and commit `data/research/milestone1.json`.

## Step 2 — Canonical identity

- GSIS ID is the primary canonical key.
- PFR fallback and normalized-name fallback are explicit and counted.
- Canonical table carries PFR, PFF, OTC, ESPN and Sleeper identifiers where public mappings exist.
- Added TFG normalized name key for joining the app's embedded scouting evidence.
- Bundle exposes identity match rate and unresolved/duplicate diagnostics.

## Step 3 — Historical league scoring replay

- Historical raw player-week stats are re-scored from Sleeper-style scoring settings.
- Supports a live Sleeper league ID, scoring JSON, or default PPR profile.
- Supports common passing/rushing/receiving/IDP categories, two-point conversions, TE reception premium and major yardage bonuses.
- Every non-zero rule receives a support audit. `exact_replay_eligible` is true only when every rule has both a mapping and a source field.
- Research bundle stores scoring provenance and a deterministic scoring signature.
- The app warns when a generated research profile does not match the currently loaded league scoring.

## Step 4 — Team Opportunity Engine

- Derives team plays, dropbacks, pass attempts and rush attempts from team-week data.
- Derives opponent offensive volume for defensive players.
- Adds pregame-only rolling team/opponent features.
- Expanding-window team-volume models are validated against simple prior-four-game baselines.
- PBP adds team red-zone plays and goal-line plays, which receive the same time-safe rolling forecasts and expanding-window validation when available.

## Step 5 — Pure opportunity metrics

Public-core metrics implemented by position include:

- QB: team volume, snap share, QB rush share and PBP-derived red-zone/inside-5 carry share.
- RB: team rush/pass volume, snap share, carry share, target share plus PBP-derived red-zone, inside-10 and inside-5 carry shares and red-zone target share.
- WR/TE: team pass volume, snap share, target share, explicit pass-play participation proxy, red-zone target share and an explicitly-labelled end-zone-target proxy.
- EDGE/IDL: defensive snap share, opponent dropback volume and pass-rush-opportunity proxy.
- LB: defensive snap share, opponent play/rush volume and tackle-opportunity proxy.
- S/CB: defensive snap share, opponent pass volume and coverage/tackle proxies.

True route participation is deliberately stored separately and left unavailable until a legitimate all-route source exists.

## Step 6 — Opportunity vs outcome classification

- Added a metric dictionary that classifies variables as team opportunity, participation, participation proxy, opportunity or outcome.
- Realized statistics such as receptions, touchdowns, sacks, interceptions and tackles are not mislabeled as usage.

## Step 7 — Stability Lab

For each position/metric:

- week-to-week Spearman stability,
- rolling four-week block stability,
- year-to-year player-season stability,
- sample counts,
- low/medium/high descriptive stability class.

No stability result activates a live model feature in M1.

## Step 8 — Forward Predictiveness Lab

Every tested metric uses lagged information only and is evaluated against:

- next-week fantasy points,
- next-three-game average,
- rest-of-season average,
- next-season PPG.

The research bundle exposes correlation and sample-size diagnostics by position.

## Step 9 — Expanding-window validation

Hard-coded time-safe folds:

- 2019–2021 → 2022
- 2019–2022 → 2023
- 2019–2023 → 2024
- 2019–2024 → 2025

Each position compares:

- baseline model: recent fantasy scoring only,
- opportunity model: baseline plus lagged position-specific opportunity features.

Outputs include MAE, RMSE, Spearman rank correlation and MAE improvement versus baseline.

## New app surface

**Lab → M1 Research** displays:

- control/research version status,
- source coverage,
- player identity health,
- scoring replay compatibility,
- team-opportunity validation,
- stability tables,
- forward-predictiveness tables,
- expanding-window validation,
- model limitations and guardrails.

## Guardrails

- Historical research is `diagnostic_only: true`.
- No random train/test split is used.
- Current-week data are shifted before predictive use.
- Pass-play participation is never called true route participation.
- Defensive role opportunities are explicitly labelled proxies until true role-specific data are added.
- Missing data are reported, not coerced to zero opportunity.

## Final QA

- Deterministic end-to-end fixture: 4,760 player-weeks, 90 position-validation rows.
- All four expanding holdout seasons verified: 2022–2025.
- Team Opportunity validation includes red-zone and goal-line volume.
- PBP opportunity and scoring-support unit tests pass.
- Python, JavaScript and Cloudflare Function syntax checks pass.
- HTML research-panel structure and GitHub workflow YAML parse pass.
- Shipped empirical bundle remains a clean placeholder until the real public-data workflow runs; no synthetic result is presented as historical evidence.
