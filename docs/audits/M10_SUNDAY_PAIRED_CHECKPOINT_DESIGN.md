# M10 and Sleeper Sunday Paired Checkpoint Design

## Decision

Add one supplementary, research-only Sunday checkpoint named
`SUNDAY_MAIN_T6`. It captures M9, M10-Linear, M10-HGB and Sleeper in one
coordinated run around 07:00 New York time, six hours before the normal 13:00
Sunday main slate. It does not replace or modify the immutable
`WEEK_OPEN_FIRST_KICKOFF` capture. M9 remains the production model.

This is the required methodology boundary before implementation. The executable
contract is `config/m10-sunday-paired-checkpoint-design.json`. Implementation
may add storage and scheduling only after this design commit exists. It cannot
change model parameters, features, selection, app output, ranks or promotion.

## Why the week-open capture remains necessary

The current capture answers a clean question: what did each locked model know
before any game in the NFL week began? In weeks with Thursday football, that
freezes the slate before Thursday kickoff, often long before Sunday injury,
roster and provider projection updates. Replacing it would destroy the only
consistent full-week cutoff and make historical comparisons depend on the game
calendar.

The Sunday checkpoint answers a different question: what did the same locked
models and Sleeper project for the remaining slate on Sunday morning? Both
identities are retained. Reports must declare the checkpoint and may never pick
whichever checkpoint looks better after outcomes are known.

## Timing decision

The anchor comes from the captured schedule: the earliest Sunday regular-season
game whose New York local kickoff is at or after 13:00 and before 16:00. The
target is anchor minus six hours. Collection opens at exactly T-6 and closes at
T-4.5, with a 30-minute poll cadence during that interval. Every artifact stores
the actual observed time and actual lead; it never records 07:00 when GitHub ran
later.

Six hours is retained because 07:00 New York precedes the usual 09:30
international window while being materially closer to Sunday than the week-open
capture. A single later checkpoint would lose already-started international
players. A player-level series immediately before every kickoff window would
create several different information sets and substantially more operational
complexity. That can be considered later as a separately designed experiment.

The 90-minute late tolerance handles delayed scheduled dispatch. A run before
the window skips without writing evidence. A run after it writes a typed missed
status when possible. If no qualifying main slate exists, the result is
`NO_MAIN_SLATE`, not a guessed 13:00 anchor.

## Remaining-slate cohort

The checkpoint covers QB, RB, WR and TE in the current governed M10 roster
universe whose game has not begun and is at least 30 minutes away at the actual
capture time. Thursday, Saturday or exceptional early games already underway
are excluded from every candidate and from Sleeper comparison. The schedule
hash and every excluded game/player reason are retained.

M9, M10-Linear and M10-HGB must have an exact three-model row set for every M10
forecast identity. Sleeper is a separate provider and may omit players. The
comparison cohort is therefore the canonical-identity intersection of both
immutable ledgers. Missing Sleeper rows are recorded by reason and never
imputed; they do not cause valid M10 evidence to be discarded. Every run reports
M10-eligible, Sleeper-returned, identity-resolved, matched and excluded counts.

## Time-safe Sunday inference

Sunday reuses the frozen season lock and existing shared feature owner. Target-
week realized statistics remain excluded, including completed Thursday or
Saturday games. Only prior completed weeks may feed M10 features. This keeps the
Sunday forecast comparable with the declared weekly model rather than silently
creating a within-week updating model.

Schedule, current roster universe, identity, captured league profiles and
Sleeper projections may change by Sunday. Consequently M10 values may remain
unchanged for many players. The checkpoint measures that honestly. Adding
injury, weather or within-week outcome features would require their own
methodology and leakage review.

## Coordinated capture and source drift

One orchestrator captures and hashes the schedule once, decides the checkpoint,
then collects the M10 source envelope and Sleeper projection response. It writes
both original observation times and binds both ledgers to the same schedule
snapshot. The maximum permitted gap between component observations is ten
minutes.

A partial failure preserves a typed component status but never labels the run as
paired comparative evidence. Identical retries are no-ops. Divergent writes to
an existing checkpoint fail closed. No present endpoint may reconstruct a
missed Sunday.

The additive namespaces are:

- M10: `data/research/prospective/m10/checkpoints/{season}/week_{week}/sunday-main-t6`
- Sleeper: `data/research/market/sleeper/checkpoints/{season}/week_{week}/sunday-main-t6`
- binding: `data/research/prospective/paired-checkpoints/{season}/week_{week}/sunday-main-t6/manifest.json`

Existing weekly paths and hashes remain untouched.

## Fair comparison

Sleeper raw projected statistics are preserved and scored through the same
captured league scoring profiles, scorer version and profile hashes used for
M10 replay. Provider-published PPR/half-PPR/standard totals remain diagnostic;
they are not substituted for exact league scoring.

Three comparisons are predeclared:

1. Sunday M9 versus M10-Linear versus M10-HGB on exact same-row identities;
2. Sunday M9/M10 versus Sleeper on the resolved intersection only; and
3. Sunday-minus-week-open forecast change on identities eligible at both
   cutoffs, reported separately from outcome accuracy.

Outcome analysis uses one declared append-only outcome revision and symmetric
exclusions. Existing row and temporal-period thresholds in
`research/decision_validation_contract.json` remain authoritative. Operational
success or a better Sunday point estimate cannot promote a model or checkpoint.

## Implementation boundary

The next implementation may add additive schema fields, timing and cohort
helpers, deterministic fixtures, validators, coordinated storage and the Sunday
workflow. It must prove DST-safe New York timing, international/started-game
exclusion, exact M9/M10 pairing, missing Sleeper behavior, shared schedule
binding, source drift, retry collisions, missed windows and preservation of the
week-open archive before scheduling reaches `main`.

No app/runtime integration, recommendation change, model selection, feature or
parameter change, ensemble, historical reconstruction or automatic promotion is
authorized. Evidence accrual remains operational. Any football conclusion waits
for an already governed review checkpoint.
