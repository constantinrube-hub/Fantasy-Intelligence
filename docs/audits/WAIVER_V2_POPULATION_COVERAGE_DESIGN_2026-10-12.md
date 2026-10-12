# Waiver-v2 outcome population checkpoint

PR83 and its frozen Ridge experiment remain immutable. This checkpoint closes
source evidence only; it does not change the feature grid, coefficients,
eligibility gates, or interpretation of the four reused holdouts.

The observed-target deficit contains missing roster weeks and roster-backed
weeks without a published stat row. The six-season source ledger has only two
roster-backed no-game team-weeks: BUF/CIN in 2022 Week 17. Those are the cancelled
game, not ordinary byes; the preserved legacy ledger calls them `CONFIRMED_BYE`
but their zero point contribution is unchanged. Ordinary bye memberships are
absent. A team schedule alone cannot prove a player's
membership during a bye, especially around transactions. Neither adjacent
rosters nor current team names may supply that missing proof.

Roster-status-only zero assignment is also insufficient. The provider's roster
producer joins/coalesces master player data into weekly rows; a status field
has no retained cell-level source/timestamp evidence. A useful label or a
practice/reserve designation is not an independent game participation receipt.
Review pinned nflverse-rosters revision
`72aba7add6996a9b5775e1559cdf6f05aeb4733a`, `R/rosters.R`, and nflreadr revision
`23f915a5be30415aeaa0c5c80cd23b2c69cda122`,
`data-raw/dictionary_roster_status.csv`. These sources explain semantics; they
do not identify the build revision of the historical CSVs.

The bounded alternative is explicit **scoring-event absence**. The three
admitted profiles use only core passing/rushing/receiving, two-point,
fumble/lost-fumble, interception-TD and TE-reception scoring. Every such score
requires an attributed PBP actor. A confirmed roster player with no published
stat row can be certified zero only when all NFL games that week are complete,
their PBP has a bound schedule/final-score/end-clock receipt, all core actor
roles are complete, all published potentially scoring identities appear in
PBP, and the player is absent from every PBP player-ID field across that week.
All actor fields and even deleted/non-scoring plays exclude candidates
conservatively. Identity ambiguity or an incomplete game blocks the whole
week's absence certificates. The executable scope is
`config/waiver-v2-zero-outcome-contract.json`.

The source is the archived complete provider PBP, not arbitrary caller rows.
Hash replay rejects a changed/truncated local copy; game reconciliation is an
additional completeness check, not a claim that a matching final score alone
proves a complete event set. The existing event-family receipts must still be
exact. The certificate binds raw source hashes, per-week game receipts,
identity, roster membership, scoring scope and builder version. Do not set
`player_stats_complete=True`. Do not fabricate individual component counts or
raw opportunity features from this point-score zero.

Game team names use the established canonical franchise aliases (for example,
2018 OAK and LV identify the same franchise). Preserve the original game ID.
Final-score reconciliation includes post-play team scores and the nondeleted
scoreboard maxima; raw play IDs are not chronological because administrative
corrections can receive a larger ID than the last football play. A scoreboard
maximum that exceeds or fails to reach the official final score remains blocked.

Only missing-stat, null-point, exact-scope, roster/schedule-backed rows can be
filled in a new population namespace. Existing outcomes and prior labels are
preserved. Under this base proof, missing roster weeks and byes remain blocked;
the separate global extension below requires stronger affirmative evidence.
New one/two/three-week
targets follow the existing same-season calendar builder.

Use the already-issued outer forecasts and feature frames to stress-audit
the newly observable targets. Report original, newly observable, combined and
still missing populations separately, with paired baseline/model errors. Do
not refit, select thresholds again, or call these reused seasons an independent
confirmation. Retain all eligibility false even if broader-cohort metrics
improve. Continue with prospective timestamped population/outcome evidence and
shared live feature parity before any promotion review.

## Stronger global identity extension

The separate `config/waiver-v2-global-identity-outcome-extension.json` authorizes
a stronger source proof without rewriting the original membership-based contract.
For an identity already confirmed at an earlier same-season cutoff, a complete
whole-NFL-week event set can prove zero even when that player's future roster
row is absent. Every scoring contributor in the bounded profiles requires an
attributed actor. Scanning **all games**, not the prior team's schedule, detects
scoring after a trade or team change. If the identity has no published stat row
and no actor occurrence anywhere in a fully certified week, its core point
score is zero independent of future membership. This is affirmative event-set
evidence, not missing-roster imputation or a claim that the player stayed on the
old team. Leave future team and position null on these target-only zero rows.

An exact published player-week with explicit canonical identity, team, position,
completed game and PBP identity can likewise supply an observed score without
a separate roster row. Use the existing exact inventory/scorer and ready event
inputs; absent fields, ambiguous games or uncorroborated identities block it.

Only identities first observed strictly before the target week qualify. Added
rows are `target_only_row=true` and cannot create decision opportunities or
enter the old feature frames. Preserve the original cutoff universe and
evaluate only already-issued predictions. Keep unsupported weeks, numeric
incomplete rows, uninformed identities and source gaps null. This extension
changes source evidence, not the frozen model-selection protocol; expanded
results remain a post-selection stress audit with all eligibility false.

## Corrected-label research challenger

Freeze `config/waiver-v2-corrected-label-challenger.json` before fitting the
corrected-label version. It reuses the exact existing feature owner, candidate
grid, nested selection, coverage thresholds, temporal folds and research gates.
Only affirmative source evidence changes: new exact past scores enter recent
calendar means, and exact future labels expand training/evaluation. Raw missing
opportunity inputs stay unknown. The original cutoff identity keys are fixed;
target-only rows never become candidate decisions. Publish new models and
forecasts separately and preserve all original artifact bytes.

The old holdout outcomes have already been inspected, so even a successful
corrected-source replay is exploratory rather than fresh confirmation.
Eligibility remains false. Do not introduce another architecture or adjust a
threshold to make these reused seasons pass. Future promotion requires unseen
prospective evidence, live feature parity and the separate decision-domain gates.
