# Window 1C — Weekly Actions + Operational UX

## Closed implementation scope

Window 1C turns the already-governed current-week decision evidence into an action-first portfolio report. It does not create a new football model, change M9/M10 governance, alter canonical rankings, execute transactions, or optimize FAAB bids.

The output is deliberately separate from the production browser decision engine. The browser remains the authoritative interactive surface for full lineup optimization and live decisions. Window 1C creates a compact, auditable report that can be read on mobile/offline and can later be consumed by a dedicated app surface without changing the current release contract.

## 1. Evidence inputs

For every enabled league the producer uses:

- `profile.json`,
- the live app manifest,
- the app core resolved only through that manifest and verified by SHA-256,
- the shared Sleeper player catalog referenced by app core,
- the hydrated current snapshot,
- the managed Sleeper username from `config/league-portfolio.json`,
- the previous week's Window 1B evaluation when one already exists.

A split current snapshot is hydrated through the existing `current_snapshot_storage` helper. No separate current-player contract is invented.

## 2. Fail-closed behavior

A league produces a typed blocker rather than a guessed action when any critical contract is invalid. Important blockers include:

- `BLOCKED_PROFILE_DRIFT`,
- `BLOCKED_STALE_CURRENT_SNAPSHOT`,
- `BLOCKED_REALIZED_STATS_GUARD`,
- `BLOCKED_APP_CORE_DRIFT`,
- `BLOCKED_MANAGED_ROSTER_UNRESOLVED`,
- `BLOCKED_WEEK_MISMATCH`,
- `BLOCKED_SEASON_MISMATCH`.

This is intentionally league-local. One blocked league does not prevent the other enabled leagues from producing their weekly actions report.

This matters for the currently deferred MinusPPR league profile rebuild: until its Sleeper profile is rebuilt, Window 1C will preserve the drift as a blocker for that league instead of silently using the stale profile.

## 3. Projection semantics

Window 1C consumes the existing current-snapshot `decision_weekly_projection` exactly as produced by the current M6 decision layer.

Every row is classified as one of:

- `FIE_GOVERNED` when the weekly FIE gate is active,
- `SLEEPER_FALLBACK` when the current production decision path is using Sleeper because the FIE gate is off,
- `EXISTING_DECISION_PROJECTION` for another existing non-null decision source,
- `UNAVAILABLE` when no weekly projection exists.

This distinction is important: Sleeper fallback can support an operational decision, but it is not re-labelled as a governed FIE prediction for Window 1B model evaluation.

Missing projections remain missing. They are never converted to zero.

## 4. Action queue

### Injury and status checks

The shared Sleeper player catalog supplies current injury/status metadata. Starter injuries are prioritized above bench injuries. This is an operational check, not an injury-outcome prediction.

### Submitted-lineup alerts

For managed-lineup formats, Window 1C compares the currently submitted Sleeper starter slots with eligible bench players using the existing weekly decision projection.

It emits only a positive-delta alert when:

- both players have a real weekly projection,
- the bench player's position is legal for that exact submitted slot,
- the difference exceeds the configured minimum delta.

The report calls these **submitted-lineup alerts**, not a replacement lineup optimizer. The production browser's full lineup optimizer remains authoritative.

Best-ball formats return `NOT_APPLICABLE_BEST_BALL` for Start/Sit because lineup selection is automatic.

If the report is built after the week's first kickoff, lineup alerts are downgraded to `REVIEW_ONLY_AFTER_KICKOFF`; Window 1C does not reconstruct player-specific lock states and therefore cannot claim the transaction is still executable.

### Available-player watchlist

When the current M5 waiver gate has eligible evidence, free agents are ordered by the existing `waiver_next3_projection` and labelled `REVIEW`.

If that model is not available, Window 1C may show a `WATCH_ONLY` list ordered by the existing weekly decision projection. This keeps the report useful without pretending that a weekly projection is an optimized waiver model.

Window 1C does **not**:

- choose the final player to drop,
- size a FAAB bid,
- estimate an optimal winning bid,
- output `CLAIM`/`PASS` as an optimized transaction decision.

Those are intentionally reserved for Window 1D.

## 5. Operational UX

Canonical outputs are:

- `data/research/evaluation/2026/weeks/week-<week>/weekly-actions-portfolio-v1.json`
- `data/research/evaluation/2026/weeks/week-<week>/weekly-actions-portfolio-v1.md`

The JSON is structured as app-ready action cards, while the Markdown is optimized for quick mobile/offline reading.

Each league surfaces, in order:

1. empty/unavailable starter problems,
2. urgent/high starter injury checks,
3. positive submitted-lineup projection deltas,
4. the available-player watchlist,
5. prior-week Window 1B evaluation metrics when present.

## 6. Automated weekly workflow

`.github/workflows/build-fie-window1c-weekly-actions.yml` supports manual dispatch and scheduled portfolio runs.

During the 2026 season it runs at:

- Tuesday 06:07 UTC,
- Tuesday 12:47 UTC as a delayed-public-data retry,
- Wednesday 06:07 UTC.

These times are intentionally after the existing current-season refresh cadence. The workflow commits only `data/research/evaluation/2026/**` and publishes the generated Markdown into the GitHub Actions job summary.

## 7. Boundaries preserved

- M9 remains the production champion.
- M10 activation is unchanged.
- No canonical ranking is modified.
- ADP/market is not used as a football feature.
- No app/runtime file is changed by the producer.
- No transaction is executed.
- No missing projection is zero-imputed.
- No FAAB or add/drop optimization is introduced.
- Window 1D remains the sole next phase for Optimal Waiver / Chopped logic.
