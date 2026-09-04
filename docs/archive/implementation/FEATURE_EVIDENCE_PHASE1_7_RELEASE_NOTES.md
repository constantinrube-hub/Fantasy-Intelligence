# Feature Evidence Phases 1–7 — Release Notes

Implemented a fail-closed research layer for diagnosing why advanced QB/RB/WR/TE metrics do or do not become production-relevant.

## Added

- Complete feature evidence matrix: coverage, sample size, player/season count, same-week/next-week/next-3/ROS association, persistence, peer redundancy, weekly residual gate, next-season portability gate, temporal CI and FDR diagnostics.
- Formal incremental horizon gates for next week, next 3, ROS, floor, ceiling, and breakout outcomes, with next-season portability retained separately.
- Multi-state evidence classification instead of binary relevant/not-relevant, including mechanism-specific and horizon-specific value.
- Feature-level component-target validation so efficiency/ability metrics can prove incremental value for the football mechanism they plausibly affect, beyond calibrated component persistence, rather than only fantasy points directly.
- Nested chronological Ridge, Elastic Net, regularized player-level partial-pooling, and HistGradientBoosting challengers.
- Pre-specified interaction tests that require incremental value beyond both main effects.
- Automated data-expansion priority plan for underpowered and low-coverage features.
- Dedicated GitHub workflow with checkpoint restoration/rebuild fallback, integrity tests, artifact upload and commit.
- Strict validator asserting that no research evidence can auto-activate runtime projections.

## Governance

The existing production gate is unchanged. This release increases research resolution and statistical power where legitimate; it does not lower promotion standards.
