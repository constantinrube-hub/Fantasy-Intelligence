# Waiver-v2 first frozen validation results

All four outer seasons (2022–2025) are evaluable for each of twelve signature/position units. Nine pass the frozen **conditional research-signal** gates; every forecast, ranking, recommendation and transaction eligibility remains false. Copied source-label and canonical feature-input bytes make the research artifact replay self-contained. The raw PBP/event derivation is a separate source audit and is not replayed by this validator.

| Scoring signature | Position | Equal-season MAE lift | Research signal | Exact future-label observation among base-feature cutoff rows |
| --- | --- | ---: | --- | ---: |
| `0b264245218667cd` | QB | 14.38% | Pass | 47.6% |
| `0b264245218667cd` | RB | 4.54% | Pass | 50.5% |
| `0b264245218667cd` | WR | 7.78% | Pass | 48.8% |
| `0b264245218667cd` | TE | 10.26% | Blocked: coverage stratum | 40.4% |
| `f407dd1959d9d675` | QB | 14.25% | Pass | 47.6% |
| `f407dd1959d9d675` | RB | 4.54% | Pass | 50.5% |
| `f407dd1959d9d675` | WR | 7.78% | Pass | 48.8% |
| `f407dd1959d9d675` | TE | 10.23% | Blocked: coverage stratum | 40.4% |
| `fec2fca13ae53e1d` | QB | 14.25% | Pass | 47.6% |
| `fec2fca13ae53e1d` | RB | 4.54% | Pass | 50.5% |
| `fec2fca13ae53e1d` | WR | 7.78% | Pass | 48.8% |
| `fec2fca13ae53e1d` | TE | 9.68% | Blocked: coverage stratum | 40.4% |

QB/RB/WR improve paired average errors within the observed-target cohort. TE fails the material-stratum guard: in 2024, rows with three observed weeks in the limiting score/opportunity history regress MAE by about 4.8–5.1%, despite positive aggregate lift. This cannot be cured by changing a threshold after seeing these holdouts.

Across positions, only 40–51% of feature-admissible cutoff rows have complete exact future targets. This is a major selection problem, not a model abstention rate. The reported 86–100% per-fold covered fractions refer to the narrower already-labelled cohort. Correlated copies of football outcomes across profiles and overlapping targets are not independent evidence.

The season-block percentile intervals remain descriptive. Four positive seasonal signs have one-sided sensitivity probability 1/16 under independent symmetric signs, before comparison multiplicity; this is not calibrated inference or promotion proof. Historical publication timing, current feature parity and free-agent decision-domain evidence are also absent.

The next priority is independent complete roster/bye/no-stat outcome coverage, followed by time-stamped historical/live feature parity and a promotion checkpoint. Keep these holdouts frozen. M9, legacy M5, runtime, rankings, planner gates and transaction authority are preserved.

## Replay

From the repository root:

```powershell
python research/validate_waiver_v2_validation.py `
  --validation-report data/research/waiver-v2/model-validation/2026-10-12/revision-1/validation-report.json `
  --expected-sha256 941b9c902c86753ceef020f50b770227412f3654ed6aaae058656c75de104107
```

The pinned report digest comes from this reviewed observation, not from an untrusted file. Replay verifies bytes, rebuilds calendar features and targets, repeats nested selection, and checks coefficients, predictions, metrics and fail-closed eligibility. It does not recapture providers or rewrite artifacts. The source reconstruction must use a new revision directory when independently rerun.
