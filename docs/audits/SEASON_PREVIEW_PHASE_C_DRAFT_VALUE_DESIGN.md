# Season Preview Phase C — Draft Value and Market Comparison Design

## Decision

Phase C completes the deferred league-value and market-comparison layer above the
immutable 2026 general and league previews.  It does not retrain or alter the
football forecast.

The permanent order is:

`Phase A raw football scenarios -> Phase B exact league scoring -> Phase C canonical replacement/VOR -> format-completeness boundary -> frozen ADP comparison`

This is the Sol methodology checkpoint required by
`docs/audits/CODEX_MODEL_ROUTING.md`.  It authorizes a bounded Terra
implementation after this design is committed.  It does not authorize an app,
runtime, M9, M10, canonical-ranking, model-promotion, waiver, or scheduled-workflow
change.

## What Phase C adds

For each of the 22 frozen league profiles, Phase C produces:

- the exact structural starter demand and replacement cutoff for every supported
  offensive position;
- a roster-neutral current-season value distribution above replacement;
- overall and positional current-season value ranks and transparent value tiers;
- a point-in-time comparison with the correct available Sleeper ADP family;
- descriptive bargain candidates, reach risks, late-round value candidates, and
  upside profiles;
- typed blockers wherever the current preview cannot support the full semantics
  of a format.

Phase C remains research-only.  Its ranks are season-preview evidence and never
replace the governed application Draft Board.

## Bound inputs

The producer must bind and hash all of the following:

1. `data/research/baselines/2026/baseline-v1.json`;
2. `data/research/evaluation/2026/preseason/general-preview-v2/manifest.json` and
   its player and joint-scenario artifacts;
3. `data/research/evaluation/2026/preseason/league-preview-v3/manifest.json` and
   its scored player output;
4. every baseline-bound league profile;
5. the baseline-bound frozen ranking blobs used only to determine the preseason
   draft-relevant player universe;
6. one explicit `season_market_YYYY-MM-DD.jsonl.gz` capture and its metadata;
7. `config/contracts/runtime-contracts.json`, the generated runtime-contract
   source, and the canonical Core implementation used for replacement ownership.

The market capture must be named explicitly by workflow input, have one consistent
capture timestamp, match its metadata row count and as-of fields, be hashed into the
Phase C manifest, and precede the
baseline's `first_regular_season_kickoff`.  Phase C may use a later market cutoff
than the Phase A football cutoff because market is a downstream comparison only;
both cutoffs remain visible and separately hashed.

No current provider endpoint may be queried by Phase C.  No file is selected merely
because it is the latest file present in the directory.

## Draft universe and identity

The scored Phase B table intentionally contains historical identities required by
the general-model population.  Those rows are not automatically draftable.

Phase C includes a player in replacement and ranking calculations only when all are
true:

- the canonical player ID and position are unambiguous;
- the player is marked `draft_relevant` in at least one baseline-bound frozen
  ranking source;
- Phase A and Phase B provide a non-blocked projection for the player;
- the position is legal in the league's canonical roster-slot contract.

`within_watchlist_horizon` may widen reporting but may not make an inactive player
part of the replacement pool.  Display-name matching is forbidden.  Phase C joins
Phase B to Phase A by canonical player ID, then joins market data by exact Sleeper ID
or exact canonical ID.  Ambiguous or missing joins remain typed unavailable rows.

The first release supports QB, RB, WR, and TE.  K, DEF, and IDP retain typed
`BLOCKED_PHASE_B_FAMILY` status until their Phase A/B statistic, identity, and
calibration contracts are complete.  Their roster slots remain visible in league
coverage diagnostics and are never silently treated as zero-value slots.

## Canonical demand and replacement ownership

Phase C must execute the existing `FIECore.LeagueDemandService` and
`FIECore.ReplacementService` from `app/core/core-services.js`; it must not re-code a
parallel Python replacement formula.

For each league:

1. Phase B fantasy-points P50 is supplied as `engineSeasonProjection` to the Core
   services.
2. Exact frozen roster positions and team count are supplied from the verified
   profile.
3. Fixed and flexible starter slots are allocated by
   `LeagueDemandService.starterDemand`.
4. `ReplacementService.profiles` supplies the sole 1-based replacement-player
   cutoff and provenance.
5. `benchInfluence` is zero unless a future separately governed profile field is
   authorized.  Actual ownership never changes the cutoff.

The output records the Core source, cutoff convention, fixed demand, flexible-slot
allocation, structural demand, position-pool size, and replacement rank.  A focused
parity test compares every emitted cutoff with a direct Core invocation for all 22
profiles.

No separate scarcity multiplier is added to VOR.  The exact starter demand and
replacement frontier already encode positional scarcity; adding another scarcity
bonus would double count the same league structure.

## Scenario-level value above replacement

Phase C uses the 200 reconciled Phase A joint scenarios and the same exact Phase B
scoring adapter.  For each league and scenario:

1. score every eligible player under that league's verified scoring contract;
2. retain the canonical P50-derived position cutoff from Core;
3. sort scenario scores within position and take the score at that fixed cutoff as
   the scenario replacement level;
4. calculate player scenario VOR as player fantasy points minus the scenario
   replacement level.

Quantiles P10, P25, P50, P75, and P90 are then taken from the player VOR scenario
distribution.  This avoids subtracting unrelated marginal quantiles and preserves
common-scenario team and league uncertainty.

The primary current-season value is `vor_p50`.  Overall and positional ranks are
ordered by `vor_p50`, then `fantasy_points_p50`, then canonical player ID.  Positive
VOR is not required for a player to remain visible, but negative-VOR rows are never
called bargains or targets.

Value tiers are descriptive only.  Boundaries use robust adjacent P50-VOR gaps
within the draft horizon: a boundary requires a gap above
`median_gap + 2.5 * MAD`, with a one-point minimum.  Tier IDs never enter the value
calculation.

## Format-completeness boundary

Exact scoring, roster demand, flexible-slot allocation, and replacement value are
valid for every league.  Phase A/B currently provides season-total uncertainty, not
all information needed for every format's complete draft utility.

| Format | Phase C V1 output | Required blocker |
|---|---|---|
| REDRAFT | Complete current-season roster-neutral value | None when inputs pass |
| REDRAFT_BESTBALL | Current-season value plus upside distribution | `BLOCKED_WEEKLY_SPIKE_SHAPE` for a full best-ball utility rank |
| CHOPPED | Current-season value plus lower-tail distribution | `BLOCKED_WEEKLY_SURVIVAL_SHAPE` for a full survival utility rank |
| CHOPPED_BESTBALL | Current-season value plus both diagnostics | Both weekly blockers |
| DYNASTY | Current-season value | `BLOCKED_LONG_HORIZON_ASSET_VALUE` for a full dynasty rank |
| DYNASTY_BESTBALL | Current-season value plus upside distribution | Long-horizon and weekly-spike blockers |

Season P10/P90 may be reported as risk and upside evidence but may not be relabelled
as weekly floor or weekly spike rate.  Existing M9 dynasty, weekly, health, or market
fallback values may be displayed only as separately identified external context;
they may not be blended into the Phase C rank.

Therefore the canonical Phase C V1 rank field is
`current_season_value_rank`, not `full_format_draft_rank`.  A full-format field is
null whenever one of the required blockers above is present.

## Frozen market comparison

ADP selection is deterministic and occurs after all football, demand, replacement,
VOR, rank, and tier fields are finalized.

### Market-family selection

- A profile containing `SUPER_FLEX` or more than one fixed QB starter per team uses
  a 2QB market family.
- Otherwise, reception scoring uses PPR when `rec >= 0.75`, half-PPR when
  `0.25 <= rec < 0.75`, and standard when `rec < 0.25`.
- Dynasty formats use the corresponding `adp_dynasty_*` field; non-dynasty formats
  use the corresponding redraft field.
- A 2QB field takes precedence over the reception family because Sleeper exposes a
  single 2QB field.
- TE premiums, points per first down, negative receptions, and other rules not
  represented by the selected ADP family are recorded as comparison-basis
  limitations.  They alter FIE scoring but never the market value itself.
- `999`, non-positive, missing, or non-finite ADP is unavailable.  Cross-family
  fallback is forbidden.

### Comparable ranks and edge

Market comparison uses only eligible players with usable values from the selected
market family:

- `market_sample_rank`: ascending ADP in that exact comparable sample;
- `model_comparable_rank`: descending Phase C P50 VOR in the same sample;
- `rank_edge = market_sample_rank - model_comparable_rank`;
- `utility_edge`: the player's P50 VOR minus the P50 VOR of the player occupying
  the same market-sample rank in the model ordering.

Positive edge means FIE values the player earlier.  These fields do not change
`current_season_value_rank`.

### Descriptive labels

Labels are deterministic research summaries, not calibrated draft instructions:

- `BARGAIN_CANDIDATE`: positive P50 VOR and rank edge at least
  `max(8, ceil(teams / 2))`;
- `REACH_RISK`: rank edge at most the negative of that threshold;
- `LATE_ROUND_VALUE_CANDIDATE`: bargain criteria plus market round at least
  `max(8, starter_slots_per_team + 1)`;
- `MARKET_ALIGNED`: usable comparison inside the threshold;
- `MARKET_UNAVAILABLE`, `PROJECTION_BLOCKED`, or `NEGATIVE_VOR`: typed otherwise.

Market round is `ceil(ADP / teams)`.  `upside_delta` is VOR P90 minus VOR P50 and
remains a distribution diagnostic, not a market input.  The report may surface
high-upside candidates only when P50 VOR is positive and P90 VOR is in the top
quartile of the player's position.

## Artifacts

Phase C first-writes a new immutable research bundle:

- `data/research/evaluation/2026/preseason/draft-preview-v1/manifest.json`
- `data/research/evaluation/2026/preseason/draft-preview-v1/league-draft-board.csv`
- `data/research/evaluation/2026/preseason/draft-preview-v1/league-replacement-levels.csv`
- `data/research/evaluation/2026/preseason/draft-preview-v1/league-draft-summary.json`
- `data/research/evaluation/2026/preseason/draft-preview-v1/validation.json`
- `data/research/evaluation/2026/preseason/draft-preview-v1/draft-preview.md`

The manifest binds every input and output hash, football and market cutoffs, Core
source hash, runtime-contract hash, seed/scenario count, market-key decision per
league, coverage, blockers, and governance flags.

## Publication gates

The bundle may publish as `READY_RESEARCH_ONLY` only when:

1. all Phase A/B manifests and artifact hashes verify;
2. all 22 baseline profile fingerprints and scoring signatures verify;
3. the draft-relevant universe is reconstructed from the frozen sources with no
   ambiguous canonical identity entering a value pool;
4. Core replacement parity passes for every supported active position in every
   league;
5. scenario-score medians reproduce Phase B P50 within the configured numeric
   tolerance;
6. ADP permutation and complete ADP removal leave demand, replacement, VOR, ranks,
   and tiers byte-identical;
7. selected-market coverage is reported overall, by position, and inside the top
   200 ADP; low coverage changes labels to unavailable rather than causing a
   cross-family fallback;
8. all nonstandard format limitations are typed and full-format ranks are null;
9. two identical no-network runs are byte-identical apart from no fields; the
   bound cutoff timestamps provide `generated_at`;
10. first-write, path allowlist, and production-surface guards pass.

A league is `BLOCKED_INCOMPLETE_VALUE_POOL` if a structurally demanded supported
position has fewer eligible players than its replacement cutoff.  Other leagues may
still publish, but the portfolio manifest must list the blocked league and cannot
claim 22/22 complete.

## Terra implementation boundary

Terra may now implement:

1. one Python Phase C orchestrator that imports the existing Phase B scoring adapter
   and calls a bounded Node bridge which loads the canonical generated runtime
   contracts and Core demand/replacement service;
2. deterministic CSV/JSON/Markdown serialization for the bounded artifacts;
3. a no-network synthetic integrity test and a 22-profile parity/invariance test;
4. one manual-only, main-only workflow with an explicit market-date input;
5. a production-surface/path guard and first-write commit restricted to
   `draft-preview-v1`.

Implementation must stop rather than invent a fallback if it cannot execute the
canonical Core services, reconstruct the frozen draft universe, validate the market
capture, or reproduce Phase B scoring.

## Explicit non-goals

- no market-informed football feature, calibration, candidate selection, rank, or
  replacement cutoff;
- no selected-roster, current ownership, live draft-pick, next-pick survival, or
  manager-behavior adjustment;
- no full dynasty asset rank without a governed future-value model;
- no full chopped or best-ball utility rank without governed weekly distributions;
- no K, DEF, or IDP value until Phase A/B supports them;
- no app publication, canonical ranking replacement, schedule, or automatic model
  promotion.
