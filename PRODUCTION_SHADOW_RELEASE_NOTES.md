# FIE V9.5 Production Shadow Release Notes

## Added

- Independent production-shadow revalidation layer.
- QB and RB HistGradientBoosting residual challenger shadow paths.
- Transparent RB backfield-competitor alternate challenger with nested cap selection.
- Component consumers for QB pass/rush volume, RB carry/target volume, WR target volume, and TE target volume.
- Multivariate next-week, next-3, ROS, floor, ceiling, and breakout consumers built only from hardened routed features.
- Current-season shadow scoring with strict current-season feature requirements.
- Fail-closed validator and workflow.

## Governance

- No current snapshot is modified.
- No `dist/` artifact is modified.
- No canonical projection is replaced.
- No auto-activation is possible.
- RB HistGB and competitor-count adjustments are alternatives, not additive.
- Week 1 does not borrow previous-season player-role features.
