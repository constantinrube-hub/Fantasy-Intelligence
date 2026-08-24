# Fantasy Intelligence Engine V8.9-RTS Implementation Audit

## Executive verdict

V8.9-RTS implements the correctness and statistical-integrity plan on top of the V8.8-M6 repository while preserving the M6 fail-closed contract. It is ready to deploy as a decision-support application. The empirical research layer is intentionally not pre-activated because the shipped M1-M6 artifacts are `pipeline_ready_not_run`; the corrected V8.9 fallback remains active until production workflows create compatible, fresh and statistically qualified artifacts.

This distinction is deliberate:

- **Application/runtime readiness:** ready.
- **Research pipeline readiness:** ready.
- **Empirical M5/M6 activation in the shipped repository:** intentionally off.
- **Fabricated/backfilled evidence:** none.

## Original implementation plan status

| Step | Status | V8.9 implementation |
|---|---|---|
| 1. Freeze baseline | Complete | Original V8.8-M6 code retained under `.baseline` during implementation; regression behavior guarded by tests. |
| 2. Canonical scoring engine | Complete | Shared V8.9 scorer, explicit coverage and unsupported-rule reporting, nonlinear bonus distinction. |
| 3. Remove hard-coded seasons | Complete for live/production paths | Dynamic browser context, dynamic proxy routes, rollover-safe research workflows/defaults/current snapshot inference. Historical fixture years remain intentionally fixed test data. |
| 4. Canonicalize runtime | Complete at resolved-runtime layer | `window.FIE89` is the authoritative V8.9 API and live handlers are rebound to canonical implementations. Legacy declarations remain as compatibility shims to minimize regression risk, but are not the authoritative V8.9 contract. |
| 5. Repair replacement/VOR | Complete | Single rank convention plus lineup-derived marginal FLEX/SF/IDP demand. |
| 6. Chronological calibration | Complete | Expanding-window OOS alpha calibration, fold consistency and temporal block-bootstrap CI. |
| 7. Chronological usage/matchup | Complete | OOS temporal gates and bootstrap evidence replace same-sample beta validation. |
| 8. Calibrated uncertainty | Complete with fail-closed fallback | M5 empirical bands, forward residual quantiles, historical residual quantiles, then explicitly heuristic low/high fallback. |
| 9. Rebuild Draft intelligence | Complete for available data | Empirical saved-draft survival frequency when sufficiently sampled; nonlinear rank-value utility; heuristic fallback labelled. |
| 10. Format-specific utility | Complete at current data resolution | Redraft, Dynasty, Best Ball and Chopped now use distinct roster utilities. Best Ball is roster-level over the loaded projection horizon; Chopped is a lower-tail survival-strength proxy. |
| 11. Stronger promotion/governance | Complete | Temporal block-bootstrap gates plus independent browser SHA-256/governance checks. |
| 12. Product truth + regression | Complete except physical-browser smoke in this container | Integrity strip, provenance, unique IDs, full static/test suite, deployment smoke checklist. |

## Critical conceptual changes

### Scoring truth

The app no longer equates "some scoring rules matched" with exact league scoring. Active league rules have explicit coverage, and season-long expectations that depend on weekly thresholds are marked distribution-dependent.

### Replacement truth

FLEX scarcity is no longer a fixed hand-set percentage. V8.9 assigns marginal starter demand using the league's actual slots and projected player values, then uses one replacement-rank convention everywhere.

### Probability truth

Draft survival is not presented as a calibrated probability unless evidence exists. With sufficient saved draft history, V8.9 uses an empirical survival frequency. Without it, the app explicitly says heuristic estimate.

### Uncertainty truth

Fallback symmetric bands are no longer silently called true P10/P90. Empirical residual distributions are preferred and the final fallback is labelled heuristic.

### Format truth

Best Ball and Chopped no longer differ only by hand-set player weights. Best Ball evaluates roster-level optimal lineups over the loaded horizon. Chopped evaluates lower-tail roster strength. These are material improvements but are not claimed to be a full tournament-equity or guillotine-elimination simulator.

## Remaining evidence/data limitations, deliberately surfaced rather than hidden

1. **Future rookie-pick outcomes:** the supplied repository contains no validated historical fantasy rookie-draft outcome dataset. V8.9 therefore uses a probabilistic slot prior instead of pretending the current rookie class represents future classes. This is a safer model, but not an empirically calibrated rookie-pick chart.
2. **Chopped elimination probability:** no historical league-level elimination/roster-release/FAAB state dataset is supplied. V8.9 uses lower-tail survival strength, not a claimed elimination probability.
3. **Best Ball full-season stochastic simulation:** the current app loads a finite Draft projection horizon. V8.9 optimizes lineups over that loaded horizon. It does not invent future weekly distributions that are not available.
4. **Research activation:** the checked-in empirical bundles are pipeline-ready placeholders. M6 correctly refuses activation until the workflows build complete evidence and a fresh current snapshot.
5. **External-source availability:** Sleeper hidden projection endpoints, nflverse releases, Open-Meteo and optional odds feeds remain external dependencies. Failures are surfaced/fallback-safe but cannot be eliminated by local code.

## Statistical promotion policy

V8.9 candidate activation requires more than a point estimate of improvement. Where applicable, promotion now requires:

- chronological expanding-window evaluation,
- minimum observations/folds,
- minimum mean improvement,
- positive improvement in a majority/two-thirds of temporal folds,
- positive temporal block-bootstrap confidence lower bound,
- and decision-specific non-inferiority checks such as precision/regret or interval coverage.

The block unit is temporal rather than individual player-week to avoid pretending correlated observations are independent.

## Governance state of shipped package

The current `active_release.json` remains fail-closed. Its artifact SHA-256 values correctly match the checked-in M4, M5, M6 and current snapshot files, but `runtime_allow_m5` is false because the empirical milestones/current snapshot have not passed the required completion/freshness/scoring/evidence gates. This is the expected release state.

## QA summary

All deterministic repository tests and parsers pass. Chromium cannot execute in the current build container due a process-level environment issue that also occurs on a trivial one-line page, so the deployment guide requires a real-device browser smoke test after Cloudflare deploy.
