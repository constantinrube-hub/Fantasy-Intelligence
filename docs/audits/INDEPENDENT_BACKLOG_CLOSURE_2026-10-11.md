# Independent backlog work while current refresh runs

Base: main `1d9d0997` (PR79 merged). Refresh run `38173485050` was in
progress during this work; its inputs, outputs and chained workflows were left
alone. The backlog is the delivered P0–P3 progress checklist; GitHub currently
has no open issue tickets.

## Work that can proceed

| Item | Result | Remaining acceptance |
|---|---|---|
| P2.7 snap units | Pinned upstream scraper and writer prove the published fractional convention; immutable source bytes, hashes and observation time accompany an optional descriptive annotation | The exact build revision of the downloaded dataset remains unverified; production features remain blocked |
| P1.9 decision views | Basic, Expanded and Advanced views derive from one frozen decision across lineup changes, status checks and waiver plans | Browser/product integration and live owner coverage remain separate |
| P1.4 historical source closure | Two remaining fumble cases investigated; source roles conflict with player-week loss totals | Authoritative source correction required; no attribution guessed |

## Snap convention

Upstream `nflverse/nflverse-pfr` commit
`b51f20bf03ee05823eeee63bccef8c89d9ab7f26` strips percent signs, converts
the three percentage columns to numeric and divides each by 100 in
`R/game_snaps.R`. `auto/update_snap_counts.R` preserves these columns when
publishing season files to the existing nflverse-data snap-count endpoint.
Both exact source files and their URLs are retained in
`config/source-contracts/nflverse-snaps-v1`.

The `--provider-convention` option on the canonical snap builder checks the
pinned manifest/source hashes and rejects cutoffs before the contract's actual
observation. It preserves missing values and zeros, rejects values outside
0–1, and records the convention separately as
`*_snap_share_provider_convention`. Existing `offense_snap_share` and
`percentage_scale` stay unverified because the CSV release does not bind its
exact scraper build revision. No denominator inference or percentage-range
heuristic establishes the unit. Historical receipts/reports remain immutable.

The new current-observation descriptive revision retains 5,955 canonical
rows, 11 unmatched PFR rows and 4 missing GSIS rows. Routes remain missing.

## Decision presentation

`weekly_decision_ledger.py --presentation-views` optionally attaches the three
views to a report. Every level carries the same decision identity, complete
owner recommendation, owner confidence, declared impact fields, adoption,
outcome and governance. Expanded adds owner explanations, alternatives and
issuance times; Advanced adds source/input/profile bindings and existing
quality classifications. Missing confidence and impact stay null. These
views do not assess calibration, create explanatory drivers, infer adoption
or recompute advice. The frozen recommendation identity is checked before
presentation, and views are independent copies.

## Source blockers that cannot be repaired safely

On `2019_17_MIA_NE`, play 3958, recorded fumblers are `00-0027150` and
`00-0032391`; the aggregate's unresolved lost fumble belongs to `00-0031062`.
On `2020_03_LA_BUF`, play 4027, fumblers are `00-0030431` and `00-0036415`;
the aggregate requires `00-0033943`, recorded as the first recovery player.
The published roles cannot satisfy the totals by selecting any subset of the
listed fumblers. Both remain blocked. Narrative/name inference and relaxing
reconciliation would conceal the conflict rather than repair source evidence.

## Wait for current evidence or a separate design boundary

Live refresh/1C/1D coverage, current scoring reconciliation and freshly issued
decision reports depend on the running chain. New calibrated distributions,
joint dependence, nonlinear scoring contracts, optimal FAAB economics and
model promotion require their separate source/design/evaluation gates.
Realized weather and missing tracking/bid fields require additional bound raw
observations. These are not completed by this source/presentation tranche.

## Validation

Focused tests cover source/contract tampering, pre-observation cutoffs,
fraction/percent mismatch, null/zero semantics, frozen decision changes,
independent view copies and identical recommendation/confidence/impact across
the three selected decision kinds. Closure runs the existing deterministic
personal release gate; the final gate result is recorded with the delivery.
The real stored Week 5 ledger replay presents all 694 decisions without an
identity mismatch: 572 status checks, 63 lineup changes and 59 waiver plans.
These are historical stored reports, not newly issued live recommendations.
