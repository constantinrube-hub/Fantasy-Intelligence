# Tranche 7C-R7 Target-Domain Decision

## Decision

The failed real-lock target exposed legitimate negative rushing-yard outcomes in the nflverse weekly source. They are valid continuous football measurements, not corrupt records. The prior blanket non-negative assertion incorrectly applied the count-target domain to every raw component.

The locked 7C-R model architecture is unchanged. Terra must implement the following target-domain rule:

- Count targets (`attempts`, `completions`, `passing_tds`, `interceptions`, `carries`, `rushing_tds`, `targets`, `receptions`, and `receiving_tds`) must be finite and non-negative. A negative count is a hard input failure.
- Continuous yardage targets (`passing_yards`, `rushing_yards`, and `receiving_yards`) must be finite but may be negative. Observed negative yardage must be preserved exactly in training and evaluation.
- Poisson loss is eligible only for a count target whose eligible training values have positive total. Its existing zero-sum fallback remains squared error.
- Every continuous target uses squared-error loss for HGB. Ridge behavior is unchanged.
- The zero prediction floor is an inference/output constraint only. It must not clamp, rewrite, or filter historical labels before fitting or evaluation.
- A source null remains missing and is excluded from that target's eligible rows. It must never be converted to an observed zero. An explicit source zero remains zero.

This resolution preserves the approved raw-target requirement, the same-row candidate comparison, the locked candidate ladder, and the portable inference contract. It does not add a feature, change a hyperparameter, select a model, authorize an ensemble, or alter production behavior. M9 remains champion and every M10 artifact remains research-only.

## Terra implementation boundary

Terra may now replace the blanket label-domain assertion with target-aware validation, preserve nullable source labels in the historical-input producer, add negative-yardage and negative-count regression fixtures, and rerun the controlled real-lock target. No scheduler, app integration, 6F path, or default-branch activation is authorized by this decision.
