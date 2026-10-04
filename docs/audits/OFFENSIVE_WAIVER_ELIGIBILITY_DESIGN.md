# Offensive Waiver Eligibility and Exact-Scoring Design

## Decision

Do not open the existing offensive waiver gates by ignoring unsupported scoring
keys or by broadening the current format lists. The present M5 waiver result is
not merely hidden by one conservative condition: its historical target has the
wrong horizon semantics, its labels omit active league scoring components, and
one boolean currently conflates a football forecast with a format-specific
add/drop and FAAB recommendation.

The replacement is a versioned waiver-v2 research path with four independent
layers: exact short-horizon forecast, same-cutoff ranking, format-specific
recommendation, and cutoff-current transaction legality. A forecast may be
useful in every format. It does not, by itself, establish dynasty asset value,
best-ball roster utility, chopped survival value, or an optimal bid.

This document is the required Sol methodology boundary. The executable design
contract is `config/offensive-waiver-eligibility-design.json`. It authorizes a
bounded Terra implementation and no production, app, ranking, promotion, or
transaction-execution change.

## Why zero offensive rows is not a feature-availability conclusion

The 3 October diagnostic loaded all 23 enabled hydrated snapshots and matching
local M5 bundles. Every snapshot has the same 419 offensive rows with at least
two historical games: 54 QB, 101 RB, 167 WR, and 97 TE. All 23 snapshot/M5
pairs match league ID, profile fingerprint, and scoring signature. Zero
offensive rows are eligible nonetheless.

Two static gates explain the result before live waiver inference is attempted:

1. Every league/position combination has at least one active scoring rule that
   the M1 raw-stat scorer cannot exactly replay. Depending on profile and
   position, the blockers include fumbles, offensive fumble-recovery
   touchdowns, sacks taken, interceptions returned for touchdowns, individual
   return and special-teams events, and 40/50-yard play bonuses.
2. The current M5 `waiver` format gate admits QB/RB/WR in four Redraft leagues,
   QB only in two Redraft Best Ball leagues, and no offensive position in the
   Dynasty or Chopped leagues. TE is excluded everywhere because its existing
   corrected-model evaluation remains diagnostic.

Because these conditions stop the inference path, recorded zero feature
coverage is not evidence that current features are absent. The implementation
must measure live feature coverage only after the upstream scoring, model, and
lineage conditions are separately reported.

## The legacy target cannot be promoted

`research/fie_research.py` currently constructs `fp_next3` by grouping on
player identity and rolling over the next observed player rows. It does not
group the forward label by player-season. Consequently the label can:

- cross from Week 18 into the following season;
- omit a bye or an inactive/no-stat week because no player-stat row exists;
- use the next three appearances rather than the next three waiver scoring
  periods; and
- average one or two future rows near an endpoint while still calling the
  result “next three games.”

This target tends to overstate players who miss time and does not represent the
decision contract's `next_3_week_gain_vs_replacement`. Existing coefficients,
fold results, and position promotion statuses therefore do not carry forward.
They remain immutable diagnostic evidence.

## Canonical waiver-v2 outcome

At a post-Week-W decision cutoff, the primary target is
`fp_next3_weeks_exact`: the mean exact league fantasy points in NFL regular-
season Weeks W+1, W+2, and W+3 of the same season. The companion total is also
stored because total points, rather than a per-appearance rate, is the natural
short-horizon acquisition quantity.

The label is built from a dense player-week outcome ledger, not a sequence of
stat rows. A team bye contributes zero to that scoring period. A player who is
confirmed on an NFL roster for a completed team game, whose outcome sources
are complete, and who recorded no scoring event also contributes zero. An
unresolved player/team identity, incomplete game outcome, or incomplete source
remains null and blocks the label; missing is never silently converted to
zero.

Training requires all three future scoring weeks and never crosses seasons.
Near the end of the regular season, runtime may use an independently trained
and validated one- or two-week horizon, with its actual horizon exposed. It may
not relabel a partial horizon as a next-three-week projection. This also makes
candidate and drop values comparable: both must share scoring signature,
horizon, model version, and label-builder version.

Every label row binds decision week, target weeks, schedule, weekly roster/team
identity, outcome sources, scoring signature, canonical scoring contract, and
label-builder hashes. A later correction produces a new append-only revision;
it does not rewrite the evidence used by an earlier model build.

## Exact league scoring

The direct waiver model predicts league fantasy points. It therefore needs
exact league-scored training labels, but it does not need the M4 weekly raw-stat
projection scorer to be exact at runtime. Waiver-v2 binds each model spec to an
exact scoring signature, position, horizon, and label-builder version. The
current `position_support()` result remains relevant to the M4/M6 weekly model;
it must not be reused as a substitute for the new waiver label lineage.

For a scoring-signature/position pair to be eligible, every nonzero relevant
rule must be reconstructed. A 95% coverage rate is not exact when the omitted
5% can change player ordering. Unknown rules fail closed.

The enabled portfolio currently requires investigation or implementation for:

- aggregate candidates such as `fum` and `pass_sack`;
- play- or participation-level events such as `fum_rec_td`, `pass_int_td`,
  `fg_ret_yd`, `kr_yd`, `pr_yd`, `st_ff`, `st_fum_rec`, and `st_td`;
- long-play event counters such as `pass_cmp_40p`, passing/rushing/receiving
  40/50-yard touchdown rules, and non-touchdown 40-yard rush/receipt rules; and
- `bonus_rush_td_qb`, which must first receive an explicit Sleeper-semantic
  contract and QB-only relevance. Its observed nonzero AEF value must not make
  it relevant to RB, WR, or TE.

Terra may use nflverse weekly data when the exact field exists. Otherwise it
must derive the event from completed-game play-by-play plus participation and
canonical identity. Individual special-teams touchdown fields and aggregate
special-teams touchdown fields require an explicit precedence rule so the same
event cannot be counted twice. Rare-event components require reconciliation
against an independent aggregate or provider result where available. A source
that does not expose an event completely cannot justify a zero.

Profiles with byte-equivalent scoring signatures and position relevance may
share a model. Similar-looking profiles may not. The scoring-rule inventory
must list, for every enabled signature and offensive position, the source,
field/event derivation, exactness status, reconciliation result, and blocker.

## Model and ranking validation

The existing Ridge is a reasonable first challenger, not a grandfathered
winner. For each scoring-signature, position, and horizon, Terra rebuilds the
labels and runs whole-season expanding outer folds. Each valid test season has
at least two earlier training seasons; promotion requires at least four valid
holdout seasons.

Feature choice, regularization, imputation policy, and the live coverage
threshold are selected only inside the earlier-season training data or nested
inner folds. The current fixed `0.45` feature-coverage threshold is not
grandfathered. At minimum, an eligible row needs `fp_prior_4` and one
position-relevant role or opportunity input, but the final threshold must also
show stable performance by missingness/coverage stratum and reject live
patterns outside training support.

The same exact-label rows are used for the model and the recent-production
baseline. Forecast validation retains MAE, RMSE, and the paired temporal-block
confidence interval. Ranking validation retains within-cutoff Spearman lift,
top-quartile precision, and top-one regret. Candidate, feature, or threshold
selection cannot use the final outer folds.

QB, RB, WR, and TE independently re-earn eligibility. In particular, TE stays
blocked unless it passes the corrected exact-target forecast and ranking gates;
the existence of a deployable fitted spec is not a promotion result.

Historical all-player rows can validate a football forecast. They cannot, by
themselves, validate a waiver decision, because the actionable comparison set
is the free-agent pool available at that cutoff. Ranking and downstream
decision evaluation therefore use captured cutoff-current ownership/candidate
sets when making waiver claims.

## Four eligibility layers

The current `waiver_activation_eligible` flag is replaced internally by four
explicit questions:

| Layer | Question | Required evidence |
| --- | --- | --- |
| Forecast | Is this exact next-H-week point forecast valid? | Exact label replay, validated model, matching hashes, supported live features |
| Ranking | Can it rank the players who were available at the same cutoff? | Forecast gate plus candidate-set ranking validation |
| Recommendation | Does adding this player and dropping another improve the roster under this format? | Ranking gate, legal replacement value, format-domain validation |
| Transaction | Is this recommendation feasible now? | Current ownership, adds enabled, roster/drop legality, budget and waiver timing |

The snapshot fields are
`waiver_forecast_eligible`, `waiver_ranking_eligible`,
`waiver_recommendation_eligible`, and `waiver_transaction_eligible`, plus a
typed status and blocker list. `waiver_next3_projection` may be present for a
forecast-only row. Legacy `waiver_activation_eligible` becomes a conservative
alias of recommendation eligibility, not forecast eligibility, so existing
planners cannot accidentally consume forecast-only values.

Window 1D must explicitly require `waiver_recommendation_eligible`. It also
requires the candidate and proposed drop to have the same scoring/horizon/model
lineage. Missing drop value remains a blocker. No planner may substitute a
weekly projection, zero, or another league's scoring profile.

## Format policy

Short-horizon football production is meaningful in every format, while the
meaning of an acquisition is not.

| Format | Forecast display | Recommendation authority |
| --- | --- | --- |
| Redraft | Allowed after forecast validation | Requires same-cutoff ranking, legal replacement, and waiver-domain evidence |
| Dynasty | `SHORT_HORIZON_FORECAST_ONLY` | Blocked until future production, age, asset market, and multi-season utility are validated |
| Redraft Best Ball | `SHORT_HORIZON_FORECAST_ONLY` | Blocked until spike distribution, roster fit, and automatic-lineup contribution are validated |
| Dynasty Best Ball | `SHORT_HORIZON_FORECAST_ONLY` | Requires the intersection of Dynasty and Best Ball gates |
| Chopped | `SHORT_HORIZON_FORECAST_ONLY` | Blocked until roster-level survival, expected shortfall, and future supply are validated |
| Chopped Best Ball | `SHORT_HORIZON_FORECAST_ONLY` | Requires the intersection of Chopped and Best Ball gates |

This removes the current error of hiding a valid mean forecast merely because
the format utility is incomplete, without committing the opposite error of
calling that forecast a validated acquisition strategy.

The UI may show forecast-only evidence with its actual horizon, scoring
identity, and blocker. “Add,” “drop,” “recommended bid,” and “optimal” language
remain hidden unless recommendation eligibility is true. App integration is a
later authorization boundary; the first implementation is research and current-
snapshot infrastructure only.

## Redraft decisions and FAAB are still separate from forecast accuracy

Even Redraft does not receive an automatic recommendation merely because the
forecast beats `fp_prior_4`. The canonical waiver decision contract requires at
least 200 eligible decision rows and six temporal periods, evaluated on:

- next-three-week gain versus the legal replacement;
- FAAB efficiency; and
- roster usefulness.

Prospective capture must preserve the cutoff-current free-agent pool, managed
roster, legal drops, budgets, bids/claims, recommendation, and later outcomes.
Private absent bids remain unknown. Observed winning-bid curves can remain
research evidence, but sparse history or a forecast edge cannot justify an
“optimal FAAB” claim. Transaction execution is not authorized.

Until those thresholds pass, Redraft output is a research watchlist or forecast
ranking, not a production recommendation. This distinction lets useful 2026
evidence appear as soon as the corrected models pass while continuing to gather
the decision evidence needed for later promotion.

## Terra implementation order

1. Add failing contract fixtures for cross-season shifts, byes, confirmed
   zero-stat weeks, incomplete sources, partial horizons, scoring isolation,
   and forecast-only planner exclusion. Do not change current eligibility yet.
2. Build a versioned dense offensive player-week outcome ledger and a complete
   scoring-rule inventory for every enabled scoring signature and position.
3. Add and reconcile the missing scoring components. Unsupported signature/
   position pairs remain blocked; partial support is still useful diagnostics.
4. Generate exact one-, two-, and three-week same-season labels with full
   lineage and completeness guards.
5. Retrain and nested-temporally evaluate waiver-v2 challengers per scoring
   signature and position. Publish all failures as typed diagnostics.
6. Write new immutable M5 waiver-v2 artifacts and validators. Never rewrite
   historical M5 bundles or treat their prior statuses as v2 evidence.
7. Add the layered fields to current snapshots. Preserve the legacy
   recommendation gate and prove forecast-only rows cannot enter Window 1D.
8. Update Window 1C/1D diagnostics and summaries to report offensive forecast,
   ranking, recommendation, and transaction coverage separately.
9. Accrue prospective candidate, replacement, bid, roster-usefulness, and
   outcome evidence under the existing waiver decision thresholds.
10. Return any model or decision promotion request to Sol after the required
    rows and temporal periods exist.

## Required preservation and acceptance tests

At minimum, implementation must prove:

1. Week 18 cannot shift into the next season.
2. A bye and a confirmed complete no-stat week are explicit zero outcomes.
3. Missing source data or unresolved roster identity never becomes zero.
4. A one- or two-week horizon is never labelled next three weeks.
5. Processing scoring profile A, then B, then A reproduces A exactly.
6. Every nonzero relevant scoring key is supported or emits a typed blocker.
7. `bonus_rush_td_qb` is QB-only after its semantics are confirmed.
8. Return and special-teams touchdowns cannot be double counted.
9. Existing M5 artifacts remain byte-identical.
10. Dynasty, Best Ball, and Chopped forecast-only rows cannot enter the
    recommendation planner.
11. TE remains blocked when its corrected validation is diagnostic.
12. Live feature missingness is not zero-imputed into eligibility.
13. Candidate/drop comparisons require identical scoring, horizon, model, and
    label lineage.
14. No Sleeper transaction mutation is executed.

## Authorization boundary

Terra is authorized to implement the versioned exact outcome/scoring ledger,
corrected waiver labels and challenger validation, layered fail-closed current-
snapshot fields, research diagnostics/planner guards, and prospective decision
capture.

This design does not authorize relaxing exact scoring, carrying forward legacy
M5 promotion results, changing M9 or canonical rankings, automatic promotion,
app integration, a Sleeper mutation, or a Dynasty/Best Ball/Chopped acquisition
claim derived only from a short-horizon mean forecast.
