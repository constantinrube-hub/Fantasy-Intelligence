# FIE Feature Evidence Hardening

This patch hardens the existing Phases 1–7 feature-evidence layer without changing any production/runtime projection.

## What changes

### 1. Extended M4 OOS history for evidence only

The original residual/challenger layer had only one usable second-stage holdout because canonical M4 OOS begins in 2022. A residual model needs prior M4 OOS seasons before it can itself be tested chronologically.

The hardening layer therefore creates a separate cached evidence baseline:

- canonical M4 OOS rows are always retained and preferred;
- missing earlier OOS seasons are generated only from seasons available before each holdout;
- the current M4 raw-stat Ridge model family is reused;
- feature availability is determined from the training partition only;
- the evidence cache lives under `.cache/fie-research/.../feature-evidence/`;
- canonical `milestone4_oos_predictions.csv.gz` is never overwritten.

With 2016–2025 history, the target is M4 OOS for 2019–2025, permitting genuine second-stage residual tests for 2022, 2023, 2024 and 2025.

### 2. Fair next-season baseline

The former next-season comparison used raw previous-season fantasy PPG as the baseline but a calibrated Ridge model for the augmented feature case.

The hardened comparison is:

- baseline: `Ridge(prev_fantasy_ppg)`
- augmented: `Ridge(prev_fantasy_ppg + candidate_feature)`

Both are trained and scored on identical feature-covered rows.

### 3. One statistical hypothesis per feature

A feature may appear in multiple semantic catalog families, for example RB target share under both opportunity and receiving role. The old loop could test the same feature twice and count it twice in BH-FDR.

The hardened layer:

- validates each `position + feature` only once;
- preserves the first family as `family` for backward compatibility;
- preserves all semantic memberships in `families`;
- assigns `hypothesis_id = POSITION:feature`;
- applies BH-FDR only to unique feature hypotheses.

### 4. Consumer routing, not automatic activation

Robust evidence is routed to the layer it actually validated:

- same-week residual → weekly projection residual review
- QB pass/rush volume → QB component models
- RB carry volume → RB carry-volume model
- target volume → receiving target-volume model
- next week → weekly forward projection
- next 3 → next-3 projection
- ROS → ROS projection
- floor/ceiling → distribution consumers
- breakout → breakout probability
- next season → preseason projection

Every route is marked:

`research_only_manual_integration_required`

Nothing is auto-activated.

## Evidence tiers

- `tier1_temporal_gate_only`: clears the unchanged FIE temporal robust gate.
- `tier2_multiplicity_supported`: also has BH-FDR q <= 0.10 for the exact validated scope.

The second tier is deliberately difficult with only four temporal folds. The distinction is reported rather than lowering any threshold.

## Additional outputs

The normal Phase 1–7 files remain. Two outputs are added:

- `consumer_routing.csv`
- `hardening_audit.json`

`hardening_audit.json` records canonical/backfilled OOS rows, OOS seasons by position, and second-stage residual fold counts.

## Governance

- Production M1–M9 artifacts remain untouched.
- Canonical M4 OOS is not overwritten.
- The existing production gate remains unchanged.
- Consumer routing is advisory research metadata only.
- A routed candidate still requires separate consumer integration and revalidation before affecting FIE rankings or projections.

## Extended-core input build

The normal M1 derived tables intentionally use the primary 2019–2025 research window. The hardened GitHub workflow therefore creates a separate evidence-only core history for 2016–2025 using `fie_research.py` with exact league scoring from the cached league-profile scoring snapshot.

To keep the backfill focused and tractable, this auxiliary build uses core player/team/snap data and skips PBP opportunity enrichment. It is used **only to create the early M4 baseline holdouts**. The actual feature tests for 2019–2025 continue to use the canonical enriched feature frame and current M1–M8 artifacts.

This separation is intentional:

- extended core history supplies leakage-safe M4 baselines for 2019–2021;
- canonical M4 OOS remains authoritative for 2022–2025;
- canonical enriched feature evidence remains authoritative for candidate metrics;
- no evidence-only extended-core artifact is committed as a production model artifact.
