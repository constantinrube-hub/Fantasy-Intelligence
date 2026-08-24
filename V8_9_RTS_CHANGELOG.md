# Fantasy Intelligence Engine V8.9-RTS Changelog

**Release date:** 24 August 2026  
**Base:** V8.8-M6 repository package  
**Release purpose:** correctness, statistical integrity, rollover safety, decision-value coherence, and fail-closed deployment hardening.

## 1. Canonical league scoring and coverage

- Added a single V8.9 league-scoring compiler for live Sleeper projections and public-stat replay.
- Active non-zero Sleeper scoring rules are classified and surfaced instead of silently ignored.
- Added support for common offensive, IDP, return and kicker linear rules, position-specific reception scoring, and weekly yardage-threshold bonuses.
- Added derived combined tackles and pass incompletions when source fields support the derivation.
- Every scored player can carry scoring coverage/exactness provenance.
- Weekly threshold bonuses can be replayed exactly from weekly realized stats when the source fields exist.
- Season aggregate projections with nonlinear weekly bonuses are explicitly marked distribution-dependent rather than falsely exact.
- M5/M6 research activation still requires the stricter historical scoring-compatibility gate.

## 2. Rollover-safe season architecture

- Removed live dependence on hard-coded 2025/2026 season URLs.
- Cloudflare proxy now supports allowlisted dynamic season routes for player/team weekly stats, snaps, depth charts, and reg+post aggregates.
- Front-end season context derives current/prior season from the loaded league and rolls over safely.
- January/February unattended current-snapshot builds infer the NFL season that began in the prior calendar year.
- Historical research defaults now advance automatically to the latest conservatively completed season.
- GitHub Actions research builds derive their historical end season at runtime instead of stopping permanently at 2025.
- Historical validators accept contiguous expanding-window folds instead of a frozen 2022-2025 set.

## 3. Replacement level and scarcity

- Fixed the prior rank/index inconsistency between replacement-score and projected-VOR calculations.
- Added one canonical replacement rank-to-index rule.
- Removed fixed 78% Superflex and fixed FLEX/IDP-FLEX positional shares from the V8.9 replacement engine.
- Marginal position demand is derived from the league's actual starter slots, eligible positions and current player values.
- Bench depth and actual ownership can still influence replacement, but both projected and legacy-compatible replacement calculations now use the same cutoff convention.

## 4. Chronological out-of-time calibration

- Replaced same-sample weekly projection calibration with expanding-window chronological evaluation.
- Alpha is fitted only on earlier completed weeks and evaluated on the next unseen week.
- Activation now requires minimum evaluation volume, minimum temporal folds, at least 1% mean MAE improvement, positive improvement in at least two-thirds of folds, and a positive temporal block-bootstrap 95% confidence lower bound.
- Calibration remains at 1.00x whenever those conditions are not met.

## 5. Usage and matchup learning

- Replaced same-sample beta selection/evaluation with chronological temporal gates.
- Usage and matchup overlays are now fitted on prior periods and evaluated on later periods.
- Activation requires sample/fold thresholds, improvement, temporal consistency and a positive block-bootstrap confidence interval.
- Existing leakage restrictions remain intact.

## 6. Uncertainty and risk bands

- Governed M5/M6 empirical risk bands remain first priority when eligible.
- Added empirical residual quantile fallbacks from immutable forward snapshots when enough data exist.
- Added historical residual quantile fallbacks by position when forward history is insufficient.
- The last-resort symmetric CV range is explicitly labelled `heuristic low/high, not calibrated P10/P90`.
- Table and drawer labels no longer imply calibrated quantiles when the data do not support that claim.

## 7. Draft intelligence

- Added empirical draft-survival frequency estimation from saved Sleeper draft/ADP history when at least 120 usable historical pick rows exist.
- Sparse-history leagues fall back to an explicitly labelled heuristic ADP survival estimate.
- Fixed the survival-event direction so later-than-ADP selections correctly increase survival probability.
- Raw `Value vs ADP` remains visible for humans, but recommendations use a nonlinear rank-value curve rather than treating a 20-pick edge equally at pick 5 and pick 200.
- Draft Assistant labels survival as an estimate and does not claim calibration.

## 8. Dynasty future picks

- Removed the prior behavior that used the current rookie/current player class as a proxy for future rookie classes.
- Future pick value now integrates a probabilistic owner-slot distribution over a generic rookie-slot prior and applies future-year discounting.
- An uncertainty range is retained for each pick.
- The UI explicitly states that this remains a conservative prior until a validated historical fantasy-rookie outcome dataset is available.

## 9. Decision currencies and league formats

- Added V8.9 player decision-value currencies instead of relying on raw mixtures of rank gaps and 0-100 scores.
- Redraft emphasizes remaining-season optimized lineup VOR and immediate weekly value.
- Dynasty uses a three-year discounted projected-VOR/future-value utility.
- Best Ball uses roster-level optimal-lineup simulation across the loaded projection horizon rather than a ceiling label alone.
- Chopped uses a lower-tail-heavy roster survival-strength utility rather than a generic redraft total.
- Trade and roster-fit calculations now consume the active format-specific roster utility.
- Chopped remains honestly labelled a survival-strength proxy, not a calibrated elimination probability.

## 10. Governance and supply-chain checks

- M6 browser activation no longer trusts `runtime_allow_m5` alone.
- Browser independently requires all mandatory governance checks, AUTO mode, freshness, matching target season/week and SHA-256 verification.
- Browser independently hashes Milestones 4, 5, 6 and the current snapshot and compares them with the signed-by-repository governance manifest values before any research override can activate.
- Existing fail-closed CONTROL fallback is preserved.

## 11. Statistical promotion guardrails

- Added `research/statistical_guardrails.py`.
- M3, M4, M5 and M6 candidate promotions now use temporal block-bootstrap confidence intervals and temporal consistency requirements in addition to minimum effect thresholds.
- Weekly ranking promotion adds robust season-level Spearman evidence while preserving precision/regret non-inferiority checks.
- Risk calibration now requires multiple folds and fold-level coverage consistency.

## 12. Runtime/UI truth and provenance

- Added a V8.9 integrity strip summarizing scoring coverage, OOS calibration state, uncertainty source, governance-hash state and Draft survival source.
- Player drawer now surfaces decision model source, uncertainty source, scoring coverage and nonlinear market-edge utility.
- Removed stale V8.2 release footer and replaced it with V8.9 methodology/provenance language.
- HTML now contains 182 IDs and all 182 are unique.

## 13. Deployment/runtime

- Cloudflare health endpoint reports `V8.9-RTS`.
- Dynamic proxy remains allowlisted; arbitrary upstream URLs are not accepted.
- `_routes.json` remains scoped to `/api/*`.
- `wrangler.toml` retains the existing Pages project name to avoid accidentally creating a different Cloudflare project when using Wrangler.

## Validation performed

- JavaScript syntax: PASS for all inline app scripts and both Cloudflare Functions.
- Python compilation: PASS.
- JSON parsing: PASS for all repository JSON artifacts.
- YAML parsing: PASS for both GitHub Actions workflows.
- HTML parsing: PASS; 182/182 IDs unique.
- M1 integrity: PASS.
- M2 integrity: PASS.
- M3 integrity: PASS.
- M4 integrity: PASS.
- M5 integrity: PASS.
- M6 integrity: PASS.
- New V8.9 integrity/rollover/statistical guardrail suite: PASS.
- Milestone bundle schema validators M1-M6: PASS in their shipped fail-closed states.
- Existing governance artifact SHA-256 references: PASS.

## Environment limitation

A Chromium smoke run could not be completed inside the artifact container because the installed Chromium process hangs even for a minimal one-line `data:` page in this environment. No app-specific JavaScript/browser exception was observed before the process-level timeout. Static HTML parsing, duplicate-ID validation, JavaScript syntax validation, function-contract tests, Python research tests and Cloudflare route/config validation were used instead. A real Chrome/Safari deployment smoke check is therefore included in the deployment checklist.
