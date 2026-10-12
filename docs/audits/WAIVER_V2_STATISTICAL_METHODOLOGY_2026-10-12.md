# Waiver-v2 statistical methodology checkpoint

The user authorized GPT-6.1 Sol High for this checkpoint. GPT-5.6 is not a
methodological dependency. This design narrows the existing offensive-waiver
contract into a reproducible **research experiment**, before outer results are
read. Its executable preregistration is
`config/waiver-v2-statistical-methodology.json`. Freeze that file's SHA-256 in
every output; changes after viewing results require a new version and cannot
turn the same holdouts into fresh confirmation.

## Population and estimand

Use the source-admissible 2018 and 2021–2025 seasons and the three signatures in
the source handoff. Exclude 2019/2020 solely for their documented source-role
conflicts. Do not pool copies of the same football outcomes across signatures
or claim 48,177 independent observations. QB/RB/WR/TE are separate units; the
twelve units form one declared comparison family.

Build features and a prediction opportunity for every decision-week roster
identity, before testing future target availability. Keep the three future
calendar weeks, signed league scores and full-horizon requirement unchanged.
Report denominator counts, past-feature coverage, missing future labels and
model abstentions separately, by season, week and position. Restrict decision
opportunities to weeks with three regular-season weeks remaining, established
from the source-bound team schedule rather than observed player appearances.

The observed future labels disproportionately cover players who keep producing
published stat rows for three consecutive weeks. Injuries, absences, omitted
bye roster memberships and no-stat weeks are not random missingness. The
experiment estimates error **conditional on exact future-label observation**;
it does not establish unconditional waiver error or injury risk. Do not use
inverse-probability weighting, imputed zero outcomes, or a missing-at-random
claim to repair this without additional evidence. An apparently strong result
cannot close this blocker.

## Past-only features and baseline

At a post-Week-W cutoff, inspect W, W−1, W−2 and W−3 of the same season.
Lookup explicit calendar identities; never shift through appearances, carry
across seasons, forward-fill roster membership, or use modern age/team/status.
Weekly position and roster identity belong to W. Retrospective source revisions
are not proof that their values were published by the historical cutoff.

`fp_prior_4` is the mean of the finite, complete exact scores in this four-week
window, requiring at least two. Expose the observation count and four-bit mask;
this is a recent-calendar-window observed mean, not a claim that four scores
are known. Use this exact same-row baseline for every paired comparison.
Required opportunity means use attempts for QB, carries + targets for RB, and
targets for WR/TE. A composite requires all component values for that week.
Confirmed bye/no-stat zero outcomes may contribute an exact score, but do not
create a raw opportunity zero unless that input is explicitly observed.

Core features are recent score, opportunity and yardage means, plus score and
opportunity counts. The second, predeclared feature set adds recent-minus-older
two-week score and opportunity means, nullable when either half is unobserved.
Yardage uses passing yards, rushing + receiving yards, or receiving yards by
position. No market, future depth chart, injury outcome or future player-universe
information enters features. Required score/opportunity means are never
imputed; optional inputs use prior-training medians with fixed missingness
indicators. Standardization is fitted only on the training rows.

## Selection and outer evaluation

Run Ridge with the frozen alpha grid, two feature sets, and history coverage
thresholds of two, three or four score **and** opportunity weeks. At inference,
also require the joint score/opportunity calendar mask to have at least twenty
training observations. Unsupported masks abstain. Save all inner candidate
results, selected threshold, preprocessing, coefficients and supported masks.

Outer holdouts are 2022–2025. Each uses every earlier admitted season, at least
two. Inner folds expand over the earlier training seasons; the first uses 2018
to validate 2021. One inner training season is permitted because the two-season
rule governs outer evaluation. Enforce the frozen minimum row, week and coverage
counts, and record a blocked fold rather than weakening them.

Select by equal-inner-season mean paired MAE gain over the common base-feature
label cohort. An abstention contributes the baseline error, hence zero gain;
this is a **selection accounting fallback**, not an eligible model forecast.
It prevents a candidate winning solely by rejecting difficult rows. Require
at least half the inner base cohort covered. Resolve ties deterministically as
the contract specifies. Fit the selected candidate on outer training, lock it,
then predict every feature-admissible outer decision row before attaching
future targets for evaluation. Outer results never choose features or thresholds.

Report covered-row MAE/RMSE, same-row baseline, coverage and baseline-fallback
policy metrics. Keep fallback rows labelled abstentions. Coverage strata are
the predeclared history counts two/three/four; material strata need at least
thirty rows and may not regress MAE by more than two percent for a research
signal. Save missing-label prediction opportunities even when they cannot
contribute to metrics.

## Uncertainty and ranking

Aggregate paired absolute-error gains by outer season; weight seasons equally.
Exhaustively enumerate resampled season blocks. Entire seasons preserve all
overlapping three-week labels and shared weekly shocks within a block. Report
ordinary 95% and family-adjusted percentile intervals (twelve-unit Bonferroni
tail levels), leave-one-season-out means and the exact one-sided sign
sensitivity under independent symmetric season signs. Do not row-bootstrap,
pool profiles, or treat within-season weekly ranks as independent replications.

Only four possibly dependent seasons are available, and later training sets
reuse earlier holdouts. These intervals are descriptive stability checks,
not calibrated population confidence or proof of an error-controlled discovery.
Even four positive season signs have one-sided probability 1/16 under the
independence sensitivity assumption, before multiplicity. A positive adjusted
interval is therefore insufficient for promotion. The fixed research-signal
gates additionally require four admissible folds, positive MAE gains in every
season, at least 2% equal-season relative MAE lift, positive RMSE gain, coverage
and stratum checks. Publish every failure rather than a selected winner.

Rank only paired covered/labelled players at the same season/week with at least
four candidates, using Spearman lift, predicted-vs-realized top-quartile
precision and selected-player regret relative to the best realized candidate.
Canonical ID breaks score ties; undefined constant ranks remain null. These
are conditional all-player diagnostics, not captured free-agent pools, legal
replacement comparisons, or waiver ranking eligibility.

## Gates and next evidence

All twelve units retain forecast/ranking/recommendation/transaction eligibility
false. Research signal and eligibility are separate fields. Mandatory blockers
are outcome-selection bias, unverified historical publication timing, absent
live feature parity, and missing promotion review; ranking additionally lacks
cutoff free-agent-domain evidence. Preserve M9, legacy M5, app/runtime, ranks
and planner gates. No prospective captures are backdated or reconstructed.

Before forecast eligibility can be reconsidered, obtain independently complete
roster/bye/no-stat outcomes or prospectively score all cutoff candidates with
their missingness accounted for; bind the same feature owner to timestamped
live evidence and test parity; then review the frozen model and adequate
independent temporal evidence. Recommendation also requires the existing
format-specific replacement, FAAB and roster-utility contract. This checkpoint
authorizes research implementation and diagnostics, not activation.

## Methodological references

Training-only preprocessing follows scikit-learn's documented leakage guidance:
https://scikit-learn.org/stable/common_pitfalls.html#data-leakage
Temporal nesting prevents selection results being reused as final performance,
consistent with Cawley and Talbot (2010), *On Over-fitting in Model Selection
and Subsequent Selection Bias in Performance Evaluation*:
https://jmlr.org/papers/v11/cawley10a.html
Neither reference certifies the completeness of this football cohort or a
four-season bootstrap; those limitations remain explicit design decisions.
