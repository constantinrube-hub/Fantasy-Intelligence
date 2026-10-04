# Waiver-v2 Exact-Scoring Extension Design

## Decision

The first real 2019–2025 Waiver-v2 profile batch is source-complete enough to
build 90,858 dense offensive player-week rows for each of 19 scoring
signatures covering 22 active leagues. It correctly produces zero exact rows:
every signature/position still contains at least one unreconstructed nonzero
Sleeper rule.

Do not weaken the exactness gate, ignore rare rules, or substitute Sleeper's
final fantasy-point total. Extend the outcome ledger with a versioned,
event-level scoring layer that preserves the raw football events needed to
replay every active scoring signature. The work remains research-only. It
does not authorize M5 replacement, app integration, recommendations, FAAB,
transactions, or automatic promotion.

This is the required Sol methodology checkpoint for the next bounded Terra
implementation. The machine-readable authority is
`config/offensive-waiver-v2-exact-scoring-extension-design.json`.

## Observed blocker inventory

The completed batch has 19 profiles, 22 leagues, 90,858 rows per profile, and
zero exact rows. The most common blockers are:

| Rule group | Signatures blocked | Required interpretation |
| --- | ---: | --- |
| `fum_lost` | 18 | Player fumble lost on any play type |
| `fum_rec_td` | 16 | Player fumble-recovery touchdown |
| `st_ff`, `st_fum_rec`, `st_td` | 16 | Individual special-teams events |
| `kr_yd`, `pr_yd` | 8 | Individual kick/punt return yards |
| `fum` | 6 | Player fumble on any play type |
| `pass_int_td` | 5 | Pick-six charged to the passer |
| 40/50-yard play rules | 1–2 | Exact qualifying play counters with stacking |
| `pass_sack` | 1 | Sacks taken by the passer |
| `bonus_rush_td_qb` | 1 | QB-only rushing-touchdown adjustment |

The portfolio clusters make implementation order material:

- three Stoned Lack Best Ball signatures can become exact after all-play
  fumbles/fumbles lost and passer pick-sixes are reconstructed;
- seven additional signatures covering eight leagues require the common
  fumble-recovery and individual special-teams event layer (MinusPPR also
  needs sacks taken);
- six additional signatures covering eight leagues then require player return
  yards; and
- Genesis, Drive, and Crazy Tryhards retain field-goal-return or long-play
  requirements after those shared layers.

## Canonical source hierarchy

The exact scorer consumes completed regular-season outcomes only.

1. nflverse weekly player stats remain authoritative for exact published
   weekly aggregates that exist directly, including sacks taken and ordinary
   passing/rushing/receiving totals.
2. nflverse play-by-play is authoritative for event class, play distance,
   touchdown state, turnover state, return type, and the primary event-player
   identifiers.
3. nflverse play participation may resolve an event participant only when the
   play ID, role, team, and canonical GSIS identity agree. Names alone never
   resolve identity.
4. Weekly player or team aggregates are reconciliation evidence for derived
   play-level totals. They cannot overwrite a conflicting event ledger.
5. A source/version/season whose expected event fields or player attribution
   are incomplete remains blocked. Absence is zero only after completed-game
   source completeness is proven.

Every raw input and derived event table binds source URL, content hash,
season, schema fingerprint, builder hash, and reconciliation result. Corrected
provider data creates a new revision; it never rewrites prior evidence.

## Canonical event ledger

Terra may add one shared event ledger before scoring profiles are applied. Its
minimum key is `(season, week, game_id, play_id, event_type,
canonical_player_id)`. Each row stores team, opponent, play type, yards,
touchdown flag, fumble/lost/recovery state, special-teams flag, source-player
roles, identity evidence, source hashes, and one of:

- `EXACT_EVENT_READY`;
- `BLOCKED_EVENT_IDENTITY`;
- `BLOCKED_EVENT_SEMANTICS`;
- `BLOCKED_SOURCE_INCOMPLETE`; or
- `BLOCKED_RECONCILIATION_MISMATCH`.

The ledger must deduplicate one football event before any profile weights are
applied. Profile scoring counts event rows; it never reparses play text or
independently infers an event.

## Rule semantics

### All-play fumbles

Sleeper's `fum` and `fum_lost` apply to a player on any play type, including
offense and special teams. Therefore summing only sack, rushing, and receiving
fumble columns is not exact. Those weekly components may reconcile offensive
plays, but the canonical count is derived from all completed plays with an
exact fumbler identity and loss state.

`fum_rec_td` is credited only to the exact player who recovers a fumble and
scores a touchdown on that recovery. The original fumbler, forced-fumble
player, and team recovery do not receive this player event. Ambiguous multiple
fumbles/recoveries on one play require ordered source roles or remain blocked.

### Passing mistakes and sacks

`pass_sack` is sacks taken by the passer and may use the exact weekly `sacks`
aggregate after source-column verification. `pass_int_td` is charged to the
passer when the same valid play is an interception returned for a touchdown.
It stacks with `pass_int` exactly as Sleeper documents.

### QB rushing-touchdown adjustment

`bonus_rush_td_qb` is the Sleeper QB Rushing TD scoring option. It is relevant
only to QB and is applied once per QB rushing touchdown in addition to the
ordinary `rush_td` value. In AEF, its negative weight reduces the value of QB
rushing touchdowns. It is irrelevant to RB, WR, and TE and must be corrected
in the canonical relevance contract before scoring.

### Long-play counters and stacking

Qualifying plays exclude penalties marked no-play and require exact passer,
rusher, or receiver identity:

- `pass_cmp_40p`: completed passes with at least 40 passing yards;
- `rush_40p` / `rec_40p`: rushes/receptions with at least 40 yards;
- `pass_td_40p`, `rush_td_40p`, `rec_td_40p`: touchdowns of at least 40 yards;
- the corresponding `*_td_50p` rules: touchdowns of at least 50 yards.

A 50-yard touchdown also qualifies for its 40-yard touchdown rule because
Sleeper documents those TD bonuses as stacking. The 40-yard completion/rush/
reception event also stacks with a qualifying TD bonus. Thresholds use the
official play statistic, not air yards or return yards.

### Individual special teams

`kr_yd`, `pr_yd`, and `fg_ret_yd` are credited to the exact returner on the
corresponding kick, punt, or missed/blocked-field-goal return. Lateral or
multi-returner plays require attributed player yardage; a team return total
cannot be assigned to the first named returner.

`st_td` counts an individual player's special-teams touchdown. It must not
double count the same touchdown through return-type-specific source fields.
`st_ff` and `st_fum_rec` require the exact individual forced-fumble or recovery
role on a special-teams play. Team-only attribution is insufficient.

The source has known edge cases around return-team and player attribution.
Accordingly, return and special-teams rule families become source-ready only
after season-level reconciliation and adversarial fixtures for onside kicks,
muffs, blocked kicks, laterals, null returners, and penalty/no-play rows.

## Ordered Terra implementation

### Phase E1 — source inventory and event contract

- Extend the historical runner to snapshot PBP and, when required,
  participation for 2019–2025 once per batch.
- Emit a season-by-field completeness inventory before deriving events.
- Add adversarial fixtures for every event family, identity ambiguity,
  penalty/no-play, duplicate events, incomplete games, and reconciliation
  mismatch.
- Build the shared event ledger and receipt without changing any exact-scoring
  status.

### Phase E2 — first exact profiles

- Implement all-play `fum` and `fum_lost`, `pass_int_td`, and `pass_sack`.
- Correct `bonus_rush_td_qb` to QB-only and replay it from rushing touchdowns.
- Reconcile fumble and sack totals by game/week.
- Rerun all 19 signatures. Expected first unlock: the three Stoned Lack Best
  Ball signatures, subject to green real-data reconciliation.

### Phase E3 — common rare-event layer

- Implement `fum_rec_td`, `st_td`, `st_ff`, and `st_fum_rec`.
- Require exact player attribution; preserve row-level blockers where the
  source cannot prove zero or ownership.
- Expected additional unlock: seven signatures covering eight leagues,
  subject to reconciliation. No global pass is assumed.

### Phase E4 — return yards

- Implement `kr_yd` and `pr_yd` with event-level player yards and reconciliation.
- Implement `fg_ret_yd` only if missed/blocked-field-goal returns are complete;
  otherwise keep Genesis and Drive explicitly blocked.
- Expected additional unlock without `fg_ret_yd`: six signatures covering
  eight leagues, subject to exact source coverage.

### Phase E5 — long-play rules

- Implement the 40/50-yard completion, rush, reception, and touchdown counters
  with the documented stacking rules.
- This targets Crazy Tryhards and, together with return/field-goal-return
  evidence, Genesis.

### Phase E6 — real replay closure

- Rerun 2019–2025 for every signature and position.
- Publish exact rows, row-level blocker counts, reconciliation mismatches, and
  league/signature coverage.
- Only exact signature/position/horizon pairs may proceed to same-season label
  construction. Partial profiles remain useful diagnostics but provide no
  training labels.

## Acceptance and preservation

Implementation must prove:

- the existing dense roster/schedule ledger and same-season target contract
  remain unchanged;
- all-play fumbles include special-teams cases and never use a name fallback;
- a pick-six stacks with the ordinary interception penalty;
- QB rushing-TD adjustment is QB-only and stacks once with `rush_td`;
- 50-yard TD bonuses stack with 40-yard TD bonuses;
- penalty/no-play events never score;
- individual and team special-teams fields cannot double count one event;
- incomplete event attribution produces null plus a typed blocker, never zero;
- source and reconciliation hashes are present in every build receipt;
- no legacy M5 artifact, M9 production forecast, app/runtime ranking,
  recommendation, or transaction path changes.

After exact label replay, model training and any promotion decision still
follow the previously approved Waiver-v2 forecast/ranking/recommendation/
transaction gates. This design authorizes data and exact-scoring work only.
