# Window 1D — Optimal Waiver / Chopped Engine

## Closed implementation scope

Window 1D adds a research-only FAAB decision layer on top of the existing M9/current-snapshot/Window 1C infrastructure. It does not retrain or reweight the football model, alter canonical rankings, promote M10/M9.1c, or move ADP into the football model.

The window solves a different problem from Window 1C. Window 1C tells the user which weekly situations deserve attention. Window 1D asks how much scarce FAAB should rationally be committed to an acquisition, given observable league auction behavior, the user's current budget, opponent budgets, short-horizon FIE value and, in Chopped formats, future eliminated-roster supply.

## 1. Observable waiver evidence

Sleeper's league transaction endpoint exposes free-agent, waiver and trade transactions. FAAB waiver rows can contain `settings.waiver_bid`. Window 1D captures only bids Sleeper actually exposes.

For every normalized waiver observation it records:

- portfolio league and source historical league ID,
- season and week,
- transaction ID,
- player ID,
- roster ID,
- bid amount,
- bid as a percentage of that league season's initial FAAB cap,
- transaction status,
- whether the row is an observable winning bid,
- whether Sleeper returned an explicit failed claim,
- whether the failure metadata explicitly indicates an outbid/higher-bid reason.

A failed claim is **not** automatically treated as a competitive losing bid. A failed waiver can fail for roster, drop or eligibility reasons. It is classified as a competitive loss only when Sleeper's own metadata says so. No invisible bid, abstention or no-bid record is fabricated.

The default capture follows each league into one previous `previous_league_id`, giving up to two seasons of same-league evidence while keeping the full 22-league request volume below Sleeper's documented general API guidance.

## 2. Prospective leakage guard

A Week N bid recommendation may use:

- all captured prior seasons,
- current-season observations from Weeks `< N`.

It may **not** use Week N transactions or any later observation. The history artifact may already contain a Week N transaction if the workflow is rerun after waivers, but `history_before_target()` removes it before every price-curve selection.

This makes the recommendation auditable later and prevents the optimizer from learning the auction result it is supposed to predict.

## 3. Football-value contract

Window 1D does not invent a new player projection model.

Candidate football value comes from the existing current-snapshot contract:

- `waiver_next3_projection` is required and only accepted when `waiver_activation_eligible=true`,
- `decision_weekly_projection` is used only for short-term lineup/survival leverage,
- `p10` is used only when the governed weekly risk gate made it available,
- missing player/drop evidence is never filled with zero.

Candidate players must be unowned in the current live Sleeper rosters and rosterable under the league's stored profile.

The add/drop comparison prefers a bench cut with governed next-3 evidence. If a required drop cannot be valued, that candidate receives `BLOCKED_DROP_VALUE_UNAVAILABLE`; a missing value is never silently interpreted as a free zero-value cut.

For standard managed-lineup formats, the transparent acquisition signal is:

`max(0, next3 add-minus-drop) + 0.25 × max(0, current-week submitted-lineup upgrade)`

For ordinary Best Ball, the current-week term is instead a candidate-versus-drop short-term proxy because the manager does not submit an authoritative optimized lineup.

For Dynasty formats the plan is explicitly labelled `SHORT_HORIZON_ONLY`. It is an in-season waiver-spend recommendation, not a replacement for dynasty asset valuation.

## 4. Separate Chopped economics

`CHOPPED` and `CHOPPED_BESTBALL` use a separate engine policy.

The Chopped acquisition signal is:

`week upgrade + 0.5 × floor leverage + 0.5 × next3 add-minus-drop`

with every negative component floored at zero.

The engine also calculates:

- a proxy for teams remaining using currently non-empty rosters,
- the current free-agent pool's top weekly quality,
- the expected top quality of the next eliminated roster under an exchangeability proxy,
- a `future_supply_index`,
- a survival multiplier as the field shrinks.

Future chopped supply increases the shadow value of keeping FAAB for later. This is intentional: an elite player today can be worth a large bid, but a league that is likely to inject similarly strong players next week should preserve more budget.

The future-supply calculation is **not** called an elimination-probability model. Window 1D does not currently have enough validated evidence to assign calibrated team-by-team chop probabilities. That can be upgraded later without changing the 1D evidence contract.

## 5. Bid-price hierarchy

Winning-price history is pooled only as much as needed:

1. same league + same position, minimum 6 wins,
2. same league, all positions, minimum 12,
3. same format + same position, minimum 12,
4. same format, all positions, minimum 25,
5. full portfolio, minimum 30,
6. sparse portfolio fallback when at least 3 observable winning bids exist.

Fewer than three observable winners yields `BLOCKED_INSUFFICIENT_BID_HISTORY` rather than a made-up market curve.

Position is attached to a historical observation only when the current governed identity can resolve that player. Old/unresolved players remain valid all-position price observations but are not guessed into a position bucket.

## 6. Win-probability curve

For each integer bid from 0 through the user's remaining FAAB:

1. Convert the bid to percentage of the league's initial FAAB cap.
2. Estimate the base probability from the Laplace-smoothed empirical CDF of observable historical winning prices.
3. Count how many current opponents can financially match or exceed that bid.
4. Increase the estimate only to the extent that current budget constraints remove competitors.

The result is an **estimated auction win probability**, not a prospectively calibrated probability yet. Player strength does not secretly shift this win curve because historical player-strength-at-auction is not currently frozen for every old transaction. Player value instead affects the expected-utility side of the decision.

## 7. Expected-utility policy

Each current candidate's positive acquisition signal is normalized against the best current candidate to a decision utility index.

Standard budget preservation is stronger early in the season:

`0.55 + 0.45 × weeks_remaining / regular_season_weeks`

Chopped multiplies that cost by:

`1 + 0.8 × future_supply_index`

and scales acquisition value by a field-shrink survival multiplier.

For each candidate and integer bid:

`EU_index(b) = P(win | b) × player_utility_index - spend_share × 100 × preservation_weight`

The recommendation is the integer bid with maximum `EU_index` within the user's actual remaining budget.

The output includes:

- recommended bid,
- near-optimal bid range,
- empirical and current-budget-adjusted win-probability curve,
- expected-utility curve,
- marginal expected utility of +1 FAAB,
- likely number of opponents able to match/exceed the recommendation,
- confidence,
- history scope and sample size,
- add/drop and short-term value drivers.

`EU_index` is deliberately called a **decision utility index**. It is not fantasy points, expected wins or calibrated championship probability.

## 8. Live-state and profile safety

Before planning a league, the workflow fetches live Sleeper:

- league,
- rosters,
- users.

It restamps the live structural contract with the existing `league_profile.py` logic and compares it to the stored profile fingerprint. A mismatch becomes `BLOCKED_PROFILE_DRIFT` for that league only.

This means the currently deferred `1343914986388353024` MinusPPR rebuild does not stop development or reports for the other leagues. It will remain blocked until the proper complete-league rebuild is run.

The current snapshot must additionally:

- match league/profile identity,
- match the target season/week,
- have `target_week_realised_stats_excluded=true`,
- be within the configured freshness window.

## 9. Outputs

Historical normalized evidence:

`data/research/evaluation/2026/waivers/history/league-<league_id>.json`

Latest operational portfolio plan:

- `data/research/evaluation/2026/weeks/week-<week>/waivers/portfolio-latest.json`
- `data/research/evaluation/2026/weeks/week-<week>/waivers/portfolio-latest.md`

Every successful run also writes an immutable timestamped decision capture:

`data/research/evaluation/2026/weeks/week-<week>/waivers/captures/portfolio-<capture_id>.json`

The timestamped captures make later recommendation-versus-outcome evaluation possible without pretending a later revised plan was the original decision.

## 10. Operational workflow

`.github/workflows/build-fie-window1d-optimal-waiver.yml` supports manual runs and scheduled Tuesday/Wednesday runs.

It runs the focused 1D integrity suite first, then builds either all enabled leagues or one specified league, and commits only `data/research/evaluation/2026/**`.

A league blocker is recorded inside the portfolio artifact and does not abort the other leagues.

## 11. Boundaries preserved

- M9 remains production champion.
- M9.1c/M10 research status is unchanged.
- No app/runtime file is changed.
- No canonical ranking file is changed.
- ADP/market remains outside the football model.
- No missing projection is zero-imputed.
- No hidden bid/no-bid behavior is invented.
- No target-week auction result can inform its own recommendation.
- Chopped and ordinary waiver economics remain separate.
- Window 2A remains the next implementation phase after 1D.
