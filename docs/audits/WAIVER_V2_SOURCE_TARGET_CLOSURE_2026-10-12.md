# Waiver-v2 source repair and exact-target advancement

Base main: PR81, `ce89bd4e9b`. This is a bounded implementation under the
existing exact-scoring extension and offensive waiver eligibility designs.
It closes admitted source/label scopes, not every historical scoring profile.

## Repair

The event aggregate previously contained only player-weeks with at least one
event. Its left join to ordinary published player stats left other player-weeks
null. Even a completely covered zero-fumble or zero-return week was therefore
rejected as missing event data.

The event producer now materializes zero-event rows only for canonical
published player-stat identities in PBP-covered season/weeks, and only for
rules with `EXACT_EVENT_READY` source/reconciliation evidence. Existing event
values are preserved. For new zero-population rows, blocked rules, explicit matched nulls, uncovered weeks,
missing player stats and unobserved roster membership cannot become zero.
The existing `player_stats_complete` assertion stays false in these runs.

## Real reconstruction

The active portfolio has 19 scoring signatures covering 22 operational leagues;
the eliminated league remains preserved outside this active batch. These are
retrospective downloaded-source reconstructions, not old prospective captures.

| Scope | Exact scoring admitted for all four positions | Complete next-three-week targets across profiles | Remaining source constraints |
|---|---:|---:|---|
| 2025 | 17/19 signatures; QB admits all 19 | 48,529 | Two signatures retain unsupported individual field-goal return yards for RB/WR/TE; incomplete player-stat weeks remain unavailable |
| 2021–2025 | 3/19 signatures | 40,833 | Four recovery-TD, nine return-yard and two long-play event blockers keep other multi-year profiles blocked; field-goal return roles remain unavailable |
| 2018 plus 2021–2025 | 3/19 signatures | 48,177 | Four recovery-TD, thirteen return-yard and six long-play blockers keep other profiles blocked; the three admitted profiles have six seasons of exact targets |

The 2025 event replay has zero event-attribution blockers. Both ambiguous
fumble-loss plays resolve uniquely; the five-year replay resolves all 26.
The three closed multi-year signatures are Stoned Lack Bestball 2, Stoned Lack
Bestball Dynasty 3 and Stoned Lack Bestball Dynasty 4. Each has 13,611 complete
next-three-week target rows. Profile-weighted counts repeat underlying football
observations; they are not independent sample counts.

The zero-event repair increases complete 2025 profile-outcome rows from 35,677
to 103,762. Ordinary published stat rows remain the authoritative aggregate
source. Receiving-yard reconciliation still records two 2025 differences; no
qualifying long-play attribution blocker was emitted for those rows. This is
not a claim that all PBP and aggregate statistics agree.

## Label producer

`build_waiver_v2_label_batch.py` replays the existing batch/profile/ledger hashes
and coverage before writing immutable new outputs. It builds exact one-, two-
and three-calendar-week targets using the established same-season contract.
Incomplete outcomes remain null, missing weeks are not skipped, and Week 18
does not enter a new season. Signature mixing, duplicate identities and
complete-but-nonexact outcomes fail closed. The indexed implementation matches
a separate literal calendar-week replay on sparse, shuffled, signed-score
multi-season fixtures and makes portfolio-scale reconstruction practical.

Target files bind the outcome ledger/report, scoring signature, source batch,
builder hashes and validation policy. These artifacts certify targets only;
point-in-time feature rows and model results are not certified. Re-running
requires a new output directory. Old ledgers and labels were not rewritten.

## Offensive waiver eligibility checkpoint

Exact targets advance the data gate. The existing approved model protocol
requires at least two earlier training seasons and four valid whole-season
outer holdouts, nested feature/regularization/coverage selection, and separate
forecast/ranking/decision gates. Five clean seasons allow at most three outer
holdouts. That first scoped report exposes `BLOCKED_INSUFFICIENT_HOLDOUT_SEASONS`.
The subsequent bounded 2018 source replay closes the fumble/pick-six families
for the same three signatures. A combined six-season replay admits 16,059
complete next-three-week targets per signature. It can support at most four
outer holdouts (2022–2025, using 2018 and 2021 as the first two training seasons).
Those rows now expose `BLOCKED_MODEL_VALIDATION_REQUIRED`. This upper bound is
not a claim that feature completeness, fold eligibility or model performance
has passed. The extra year was selected for source/temporal capacity before any
forecast performance was measured. 2019/2020 remain explicitly excluded due to
their unresolved source roles. One clean season for other profiles cannot pass
validation.

The unresolved 2019/2020 fumble roles and other historical source conflicts
remain blocked. Restoring older cohorts from authoritative corrected roles or
reviewing a bounded additional historical source is the next source-methodology
checkpoint. Reducing holdout requirements, ignoring rare rules, inheriting old
M5 eligibility or treating targets as predictions would violate the approved
contract. M9, rankings, live recommendations and transaction authority remain
unchanged.

## Reproduction and validation

Run `run_waiver_v2_profile_batch.py` for the desired scoped seasons, then
`build_waiver_v2_label_batch.py --batch-report <profile-batch-report.json>
--output-dir <new-label-directory>`. Do not assert player-stat completeness
unless its own source proof is available. The committed observation summary
retains source hashes, rule blockers, signature/position target counts and
validation capacity. Full local historical caches are reproducible inputs,
not production model artifacts.

Focused source, outcome, closure and label tests pass. The personal release
gate adds the label-batch integrity check and requires 91 green checks at this
closure. New model/statistical-methodology reasoning must honor
`CODEX_MODEL_ROUTING.md` before the next checkpoint. The three six-season cohorts
can advance to their feature/model validation checkpoint under that routing.
Historical and profile-batch runners also reject existing output directories
before fetching or changing evidence. Corrected provider data requires a new
revision directory; shared caches remain reusable.
