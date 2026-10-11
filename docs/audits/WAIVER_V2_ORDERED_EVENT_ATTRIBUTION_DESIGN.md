# Waiver-v2 ordered event attribution

Status: research-only source correction, 2026-10-11. M9 remains champion.
This change may improve exact historical outcome coverage, but cannot activate
forecast, ranking, recommendation, bid, transaction, or app authority.

## Observed blockers

The source-bound partial 2026 replay has four remaining event blockers:

- one play with two different fumblers and one play-level lost-fumble flag;
- one completed pass whose primary receiver has 2 official receiving yards and
  whose lateral receiver has 80 official lateral receiving yards and the TD.
  That row blocks the reception-40, reception-TD-40 and reception-TD-50 events.

The normalized nflfastR fields explicitly preserve player identities and yards
for the primary receiver and the last lateral receiver. nflfastR also warns
that only the last receiver is represented when a play contains multiple
laterals. Therefore player IDs or play descriptions alone are not sufficient.

## Attribution contract

### Multiple fumbles

Do not assume that `fumbled_1` pairs with `fumble_recovery_1`. For every
player-week, bind the all-position published `fumbles_lost_total` aggregate.
Single-fumbler plays remain directly attributed. A multi-fumbler lost play is
resolved only when the remaining player-week aggregate deficits admit exactly
one assignment across the complete connected set of ambiguous plays. Zero or
multiple solutions remain `BLOCKED_EVENT_SEMANTICS`; missing/null/negative
aggregates, missing identities, or aggregate totals below already attributed
events block. The solver must not read names or narrative play text.

### Receiving laterals

Before a lateral long-play event can score, reconcile each offensive
player-week's sum of primary `receiving_yards` plus attributed
`lateral_receiving_yards` to the published player-week `receiving_yards`.
Null, missing, duplicate, or mismatched aggregates block the affected rule.
After an exact reconciliation:

- the primary receiver is evaluated only on `receiving_yards`;
- the lateral receiver is evaluated only on `lateral_receiving_yards`;
- a receiving-TD threshold is credited only to the exact `td_player_id`;
- a 50-yard TD still stacks its reception, 40-yard TD and 50-yard TD events.

This admits source-attributed last-lateral yards while the aggregate
reconciliation detects omitted or conflicting player-week accounting. It does
not invent intermediate lateral participants.

## Acceptance

- Preserve every existing event row and source receipt.
- Add explicit reconciliation input hashes and counts to E2/E5 receipts.
- Prove unique and ambiguous multi-fumble fixtures, null/mismatch/duplicate
  aggregate failures, and primary-versus-lateral threshold attribution.
- Replay the preserved partial 2026 source: 1,415 existing event rows remain,
  the four observed blockers close only if both reconciliations are exact.
- Keep field-goal-return roles and every unrelated gate unchanged.
