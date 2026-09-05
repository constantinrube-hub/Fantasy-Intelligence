# V9.6 Controlled Runtime Release Notes

- Promotes shadow-approved QB/RB HistGB residual challengers into controlled current-season runtime.
- Keeps WR/TE generic HistGB disabled.
- Keeps RB backfield competitor Ridge diagnostic-only and non-additive.
- Wires validated component and horizon consumers into the league-level `v96_runtime` current-snapshot overlay, avoiding per-player shared-storage fragmentation.
- Does not overwrite canonical M5 next-3/risk consumers with horizon models that were not tested head-to-head against those consumers.
- Preserves existing M4/M5 player activation as an additional runtime gate.
- Requires league/profile/scoring/model-hash identity.
- Blocks preseason and missing-current-season-feature activation.
- Explicitly leaves next-season projections untouched.
