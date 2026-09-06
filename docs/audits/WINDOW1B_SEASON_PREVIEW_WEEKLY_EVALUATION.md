# Window 1B — Season Preview + Weekly Evaluation

## Closed implementation scope

Window 1B adds a research-only evaluation layer on top of the immutable 2026 Window 1A baseline. It does not change M9, M10 activation, app/runtime behavior, canonical rankings, ADP treatment, waiver recommendations, or any production decision surface.

The purpose is to preserve what FIE believed before the season and before each eligible game week, then make later prediction-versus-outcome evaluation deterministic and auditable.

## 1. Season Preview

`research/window1b_evaluation.py season-preview` consumes `data/research/baselines/2026/baseline-v1.json`.

Before using a league it verifies the frozen SHA-256 bindings for:

- league profile,
- current snapshot,
- app manifest,
- canonical league rankings.

It then resolves the app-core snapshot only through the frozen app manifest and verifies the app-core SHA-256 recorded there. Any mismatch fails closed as source drift. The report therefore cannot silently substitute a later roster, later ranking board, or revised preseason input for the frozen baseline.

### Team ranking semantics

The preview is deliberately not a new predictive model.

For ordinary managed-lineup leagues, the primary team-strength ordering is the sum of the existing canonical `projection_points` values whose ranking rows are explicitly season-scoped for the frozen starting lineup. Weekly-scoped specialist projections are not mixed into season totals. Full-roster projection is the first tie-break and starter VORP is the second tie-break.

For `REDRAFT_BESTBALL`, `DYNASTY_BESTBALL`, and `CHOPPED_BESTBALL`, full-roster season-scoped projection is primary because lineup selection is format-driven rather than a weekly manager choice. Starter projection and roster VORP are tie-breaks.

These are transparent presentation aggregations only. They are not calibrated win probabilities, playoff probabilities, championship probabilities, or promoted model weights.

Missing ranking evidence is never filled with zero. Each team receives exact mapped/expected counts, coverage, missing player IDs, and one of:

- `READY`,
- `PARTIAL`,
- `INSUFFICIENT_EVIDENCE`.

The portfolio report includes all baseline leagues and formats plus a top-24 canonical player board per league using the already-governed canonical `overall_rank` together with the original projection/VORP metadata without re-weighting them.

Canonical outputs:

- `data/research/evaluation/2026/preseason/season-preview-v1.json`
- `data/research/evaluation/2026/preseason/season-preview-v1.md`

The Markdown artifact is intentionally suitable for offline reading.

## 2. Weekly prediction snapshots

`weekly-snapshot` creates an immutable, first-write pregame evidence record.

Required controls:

- the current snapshot must state `target_week_realised_stats_excluded=true`,
- its `generated_at` must be strictly before the supplied kickoff cutoff,
- eligible predictions must be bound explicitly,
- an existing immutable path may only be re-written with byte-identical canonical JSON.

When the current snapshot reports zero weekly activation-eligible predictions, Window 1B emits `BLOCKED_NO_ELIGIBLE_WEEKLY_PREDICTIONS` and preserves the source-health reason. It does not invent projections or substitute missing evidence.

At implementation time the frozen Week 1 current snapshots report zero eligible weekly predictions because current-season nflverse player/team/snap history is not yet available. This is therefore an expected typed blocker, not a Window 1B failure.

## 3. Weekly outcome evaluation

`weekly-evaluate` joins a ready immutable prediction snapshot to explicitly supplied outcome rows using player identity.

It reports only matched evidence and calculates:

- MAE,
- RMSE,
- mean bias (`projected - actual`),
- matched-row coverage.

Missing outcomes remain `PENDING_OUTCOME`; they are never treated as zero fantasy points. Evaluation does not tune, retrain, select, promote, or modify rankings.

## 4. Workflow

`.github/workflows/build-fie-window1b-evaluation.yml` is manual-only and main-only.

It can:

- build the complete frozen Season Preview,
- capture a league/week pregame prediction snapshot,
- evaluate an existing weekly snapshot against an explicit outcomes file.

The workflow runs the focused Window 1B synthetic integrity contract before any output and commits only `data/research/evaluation/2026/**`.

## 5. Regression repair included with Window 1B

The scheduled `Refresh FIE Current Season` run on the Window 1A merged head reached the consolidated legacy 15-point regression suite after the earlier integrity checks passed, but item 10 still expected obsolete Draft Board wording.

Window 1B updates that assertion to accept the current semantic wording (`Draft Board remains independent of selected roster`) while preserving the original decision-separation requirement. This is a regression-test repair only; it does not revert or modify the app UI.

## 6. Boundaries preserved

- M9 remains production champion.
- M10 remains research-only unless separately promoted under its existing governance.
- No app/runtime file is changed by Window 1B.
- No canonical ranking artifact is changed by Window 1B.
- ADP/market remains outside the football model.
- No waiver optimization is introduced; that remains Window 1D.
- No Weekly Actions/operational UX is introduced; that remains Window 1C.
- Missing evidence and timing violations fail closed.
