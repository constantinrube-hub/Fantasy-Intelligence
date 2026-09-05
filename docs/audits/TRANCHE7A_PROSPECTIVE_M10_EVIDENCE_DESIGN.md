# Tranche 7A — Prospective M10 Evidence Design

## Decision and boundary

Tranche 7A authorizes design for real prospective evidence collection. It does not authorize Tranche 6F, a shadow namespace, model selection, promotion, app integration, or production activation. M9 remains champion. QB M10-HGB remains a research lead only.

This is the Sol design result required before implementation. The machine-readable contract is `config/m10-prospective-evidence-contract.json`. Terra may implement that contract in Tranche 7B only after this design is committed. Scheduled operational capture follows separately in 7C after deterministic fixture validation.

The new phase is numbered 7A deliberately: 6F remains a gated shadow-integration phase and was not approved by 6E. Evidence collection must not be presented as shadow deployment.

## Why a new evidence path is required

The 6E result found one promising synthetic signal—QB M10-HGB—but could not honestly answer the questions needed for model governance. The retained 6D artifact has aggregate fold metrics, not real row-level forecasts. It cannot reconstruct player disagreement, conditional calibration, scoring-profile behavior, or fantasy-decision regret.

Prospective collection addresses those missing observables without relaxing the 6A gate:

1. freeze M9, M10-Linear, and M10-HGB predictions before results exist;
2. retain paired player rows and raw football components;
3. replay those raw outcomes through every applicable captured scoring profile;
4. record research-only counterfactual decision traces against the same legal choice set;
5. append independently sourced outcomes later; and
6. evaluate only at predeclared checkpoints.

No present-day endpoint may create an earlier forecast. A missed week remains missing evidence.

## Prospective unit and seasonal lock

The primary unit is one complete NFL week slate. One immutable forecast is written inside the existing verified 18-hour window before that week's first kickoff. Using one slate cutoff gives every model the same information boundary and avoids choosing a more favorable capture for individual players.

Before the first evaluated week of a season, the training manifest, candidate definitions, hyperparameters, feature contract, dependency lock, and model-parameter hashes are frozen. Parameters are trained only through the previous completed regular season. Prior completed weeks in the current season may update explicitly lagged input features, but they may not tune parameters, replace candidates, or change gates.

Every capture records its observed time, first kickoff, hours before kickoff, schedule hash, input hashes, and model hashes. The writer is first-write immutable. If a valid window is missed, it writes a typed missed-capture manifest and never produces a hindsight forecast.

## Paired row-level forecast ledger

Collection covers all predeclared QB/RB/WR/TE candidates—M9, M10-Linear, and M10-HGB—on identical eligible players. Retaining the non-leading positions and linear baseline prevents selection bias and provides negative controls; it does not elevate them.

Each row carries canonical identity, position, team, opponent, player kickoff, model identity, raw component forecasts, default scored points, P10/P25/P50/P75/P90, defined event probabilities, and exact source/model hashes. Reconciliation of targets, carries, receptions, completions, and team budgets occurs before the ledger is written.

Availability probability remains blocked until enough genuine history exists. A field without a locked probabilistic definition is `null` with a typed blocker; confidence may not be manufactured. Model-defined event probabilities and forecast quantiles are retained so later calibration can use honest probability bands.

## Time-safe subgroup labels

The forecast-time ledger records only labels knowable at the cutoff:

- position;
- early, middle, or late-season week range;
- team-change status derived from prior captured roster history;
- rookie/young-player status from then-known experience;
- prior-participation band from completed games only.

Missing information is `UNKNOWN`, not filled from later results. Scoring format, scoring signature, profile fingerprint, and league capability are added by the separate scoring replay. Later evaluation must publish sample size, paired coverage, and uncertainty for every material subgroup and fail closed when a subgroup is too small.

## Exact scoring-profile replay

Raw football predictions are generated once. The existing canonical scorer then applies every enabled league profile captured at forecast time across all 22 currently enabled leagues and all six formats. Equivalent profiles may share computation, but every output row retains league ID, format, scoring signature, and profile fingerprint.

A missing profile, hash mismatch, unsupported scoring key, or scorer-version mismatch blocks that replay. It cannot fall back to default PPR. ADP, market price, roster demand, replacement value, and draft behavior remain outside the football model.

## Decision-utility traces

Decision traces are research-only counterfactuals. They use the same cutoff-time roster, eligible player pool, lineup rules, and scoring profile for M9 and every M10 candidate. They never overwrite, annotate, or impersonate a production recommendation.

The first applicable domains are:

- managed-lineup start/sit;
- best-ball weekly lineup capture; and
- chopped-league lineup downside measures.

Waiver evaluation is conditional on a valid cutoff-time free-agent pool and the required forward outcome window. Draft, trade, and multi-season dynasty utility remain unsupported by this weekly challenger and must report `NOT_APPLICABLE` or a typed blocker. Existing minimum rows and temporal-period rules in `research/decision_validation_contract.json` remain authoritative.

Each trace preserves the complete legal choice set, selected lineup or player, relevant constraints, predicted utility, and later realized regret. Storing only the winning recommendation would make counterfactual comparison impossible and is prohibited.

## Outcome separation and correction handling

Forecasts and outcomes live in separate namespaces. Outcome ingestion begins only after the target games and records the provider release or commit, observed time, exact payload hash, and a monotonically identified revision. Corrections append a new revision; they never rewrite a forecast or silently replace an earlier outcome.

An evaluation declares one outcome revision before it runs. Ambiguous identities, missing results, postponed games, and unsupported positions are excluded symmetrically from every model with typed reasons. Corrected outcomes may train a later season's model, but they do not alter what was known at the forecast cutoff.

## Checkpoints and non-promotion gates

Operational health is validated after each run: timing, first-write behavior, hashes, paired coverage, identities, profile replay, and namespace separation. Passing operational checks means only that evidence was captured correctly.

An interim report may be descriptive after at least eight completed weeks. It cannot select a candidate, change a parameter, approve shadow use, or make a production claim. A season-close review requires a locked outcome revision and returns to Sol.

The original 6A promotion gate is unchanged: at least four completed outer seasons, paired practical improvement with a positive temporal-block bootstrap lower bound, non-inferior calibration without material subgroup failure, all applicable scoring profiles, decision utility, reproducibility, and explicit human authorization. Prospective weeks or one completed season do not substitute for four completed seasons.

## Ordered continuation

### 7B — Deterministic capture contract (Terra)

Implement schemas, a synthetic no-network fixture, first-write storage, missed-capture behavior, validators, and integrity preservation. Use targeted tests while building and one full release gate only at tranche closure. Do not add a production schedule in 7B.

### 7C — Operational collection (Terra)

After 7B closes, connect the validated writer to time-safe M9/M10 inputs, canonical scoring replay, decision traces, and append-only outcomes. Validate it on the audit branch first. Scheduled workflows operate only from the repository's default branch, so enabling recurring collection requires a separate explicit rollout boundary after validation.

### 7D — Evidence accrual (operations)

Let immutable captures accumulate. Monitor capture health and repair code defects prospectively; do not fill missed periods, select models, or reinterpret operational success as football evidence.

### 7E — Evidence review (Sol)

Run only at a declared checkpoint with sufficient captured data. It may retain M9 and continue collection. Any reconsideration of 6F requires a new explicit decision artifact and remains separate from capture.

## Preserved invariants

- M9 remains production champion.
- No runtime, app, canonical rank, recommendation, deployment, or publication behavior changes.
- All 22 leagues and six formats retain their canonical scoring, roster, scarcity, replacement, identity, and provenance ownership.
- Market and ADP information remain outside the football model.
- No ensemble is authorized.
- Missing history, identity ambiguity, leakage, profile mismatch, and incomplete decision evidence fail closed.
