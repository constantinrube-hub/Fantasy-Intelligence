# In-Season Intelligence PR2 — Weekly Lineup Decision Support Design

## Authorized boundary

This document is the Sol design boundary for a bounded Terra implementation of
portfolio-wide weekly lineup decision support.  It extends Window 1C; it does
not replace the production browser decision engine, change M9/M10 governance,
alter canonical rankings, execute a Sleeper lineup change, or treat an
uncalibrated simulation as a calibrated probability.

The current Window 1C producer intentionally emits only submitted-lineup
positive-delta alerts.  That is useful triage, but it is not a full lineup
optimizer: a pairwise comparison cannot prove the globally optimal assignment
when fixed slots, FLEX, Superflex, IDP flex, K and D/ST compete for the same
players.  PR2 adds an exact, auditable lineup layer while preserving the old
alerts as a compatibility view.

## 1. Canonical owners and evidence

The implementation must consume, not recreate, these owners:

- roster-slot eligibility and position aliases:
  `config/contracts/runtime-contracts.json`;
- scoring/profile identity: each league's stored `profile.json`, live app
  manifest/core and exact `scoring_signature`;
- managed roster and submitted starters: the SHA-256-verified app core;
- weekly football value: the hydrated current snapshot's existing
  `decision_weekly_projection`;
- governed uncertainty: `p10`/`p90` only when
  `weekly_activation_eligible=true`;
- player identity: canonical/Sleeper IDs, never display-name joins;
- injury/status labels: the app core's referenced Sleeper player catalog;
- opponent identity: a captured Sleeper `/matchups/<week>` response;
- game locks: the existing nflverse schedule owner, captured with source hash
  and observation time.

The Python producer may expose a small adapter for the canonical runtime
contract, but it must not carry a second hand-maintained slot or alias map.
Every output binds the profile fingerprint, scoring signature, current-snapshot
hashes, runtime-contract hash, roster-state hash, matchup hash and schedule
hash.

`decision_weekly_projection` is already league-scored.  PR2 must not rescore
the same player independently or combine rows across scoring signatures.
Missing projections remain missing and never become zero.

## 2. Exact legal assignment

Managed-lineup formats use a deterministic maximum-weight bipartite assignment
between concrete starter-slot instances and the managed roster's eligible
players.  A player can be selected at most once.  Fixed slots and flexible
slots are solved simultaneously; no greedy fixed-slot-first or pairwise-swap
algorithm is permitted.

The solver returns:

- every concrete slot instance and its assigned canonical player ID;
- filled and unfilled slots;
- selected and bench player IDs;
- lineup objective total;
- submitted-lineup total when it is fully scoreable;
- exact improvement versus the submitted lineup;
- the minimum set of `START`, `BENCH`, and `MOVE_SLOT` changes;
- deterministic tie information.

Input players and equal-valued assignments are ordered by canonical player ID,
then concrete slot index.  Repeated execution on identical evidence must
produce byte-equivalent decision content apart from explicitly volatile
capture metadata.

An `OPTIMAL_LINEUP` claim is allowed only when all potentially material active
roster candidates have a real decision projection and the complete starter
assignment is fillable.  Otherwise the league returns a typed blocker or a
clearly labelled partial comparison; it must not call a reduced candidate set
globally optimal.

## 3. Format policy

### Managed Redraft and Dynasty

The primary objective is maximum sum of `decision_weekly_projection` under the
exact league slots.  Dynasty future/market value is irrelevant to a weekly
start/sit choice and cannot enter this objective.

### Managed Chopped

Maximum expected points remains the primary executable lineup.  When every
material candidate has governed P10 evidence, the report also returns a
`SURVIVAL_FLOOR_ADVISORY` lineup maximizing summed P10 with mean projection as
the first tie-break.  This is a downside lens, not a calibrated chop
probability, and cannot silently replace the primary lineup.

### Best Ball and hybrid Best Ball

`REDRAFT_BESTBALL`, `DYNASTY_BESTBALL`, and `CHOPPED_BESTBALL` return
`NOT_APPLICABLE_AUTOMATIC_LINEUP` for manual Start/Sit.  They may record a
pregame exact legal mean/floor/ceiling lineup for later automatic-lineup
capture evaluation, but must not present a user lineup action.

### Specialist and custom slots

Superflex, IDP, K, D/ST and every supported custom slot use the canonical
runtime contract.  If a stored slot is absent from that contract, the league
fails with `BLOCKED_UNKNOWN_ROSTER_SLOT`; exact-position guessing is forbidden.

## 4. Availability and injury scenarios

PR2 does not invent an injury probability or apply an unvalidated projection
haircut.

- Official `OUT`, `IR`, `PUP`, `SUSPENDED`, `INACTIVE`, or `NA` rows are
  excluded from the active scenario and create an urgent submitted-starter
  action when relevant.
- `QUESTIONABLE` and `DOUBTFUL` players retain their unmodified projection in
  the active scenario.
- A questionable/doubtful material player also triggers an inactive
  contingency solve with that player removed.
- The report states the latest safe decision time from the player's scheduled
  kickoff and flags a contingency whose replacement locks earlier.
- Unknown status or schedule evidence never becomes an assumed active/inactive
  probability.

The primary output therefore distinguishes `ACTIVE_BASELINE`,
`INACTIVE_CONTINGENCY`, and official-unavailable evidence instead of blending
them into one opaque number.

## 5. Locks and partial-week behavior

The existing Window 1C first-kickoff downgrade is preserved until player-level
locks are proven.  PR2 may replace it only when the captured schedule maps each
rostered entity to a verified kickoff.

With verified player-level locks:

- a player whose game has started is fixed to the submitted starter/bench
  state observed at capture;
- an already-started player stays in the exact submitted slot instance;
- unlocked players may be optimized only over unlocked slots;
- no action is emitted for a locked player;
- a stale or incomplete schedule produces `BLOCKED_LOCK_STATE_UNRESOLVED`.

D/ST uses its team schedule.  A free agent, bye-week player, unresolved team or
postponed game must retain a typed schedule state.

## 6. Uncertainty and opponent context

The exact max-mean lineup is the only primary recommendation initially.
Governed P10/P90 evidence may add two deterministic advisory lineups:

- `FLOOR_ADVISORY`: maximize summed P10, tie by mean;
- `CEILING_ADVISORY`: maximize summed P90, tie by mean.

Opponent context includes the opponent's exact max-mean legal lineup, projected
mean margin, coverage diagnostics and the source-captured matchup ID.  It does
not change the primary lineup merely because the team is projected ahead or
behind.

The existing browser's max-win simulation remains directional and explicitly
uncalibrated.  PR2 must not publish an opponent-aware lineup as an executable
recommendation until prospective start/sit evaluation validates the method.
An optional `DIRECTIONAL_RISK_LENS` may select the floor advisory when ahead or
the ceiling advisory when behind, but it must be labelled advisory, expose the
mean-points sacrifice and never display a calibrated win-probability claim.

This avoids importing the browser's position-CV fallbacks, hand-set teammate
correlation shock, or normal approximation into a governed research decision.

## 7. Confidence and explanations

Confidence is evidence accounting, not a new learned score.  Each league
reports:

- projection-source counts for all rostered players and selected starters;
- governed interval coverage;
- missing-projection and unresolved-identity IDs;
- scoring/profile/source hashes;
- injury and schedule observation ages;
- whether the recommendation differs under injury contingencies;
- exact projected gain and changed slots;
- the closest legal alternative per changed slot when calculable.

The human explanation should lead with actions, then evidence and caveats.  It
must state when a recommendation is driven by league scoring, FLEX/Superflex
assignment, an official status, or an injury contingency.

## 8. Portfolio and cross-league output

The portfolio is dynamic over the enabled registry rather than hard-coded to
23.  Historical/retired leagues remain preserved but are absent from current
actions.  An eliminated Chopped roster may remain in research history while
returning `NOT_APPLICABLE_ELIMINATED_ROSTER` for current Start/Sit.

The portfolio summary includes:

- leagues ready, blocked, automatic-lineup, eliminated and needing action;
- total projected points recoverable from submitted-lineup changes;
- player exposure in recommended starters, submitted starters and benches;
- injury concentration across leagues;
- cross-league decision conflicts, with league scoring signature and slot
  context preserved;
- priority ordering for AEF, live Chopped leagues, Genesis Dynasty, Genesis 4
  and Dynasty Prime when those configured leagues are present.

A cross-league conflict is informational.  One league's lineup can never be
copied into another league or used as a scoring fallback.

## 9. Outputs and point-in-time evaluation

Canonical research outputs are:

- `data/research/evaluation/<season>/weeks/week-<week>/lineups/portfolio-latest.json`;
- `data/research/evaluation/<season>/weeks/week-<week>/lineups/portfolio-latest.md`;
- `data/research/evaluation/<season>/weeks/week-<week>/lineups/captures/portfolio-<capture_id>.json`.

The latest files are operational views.  Each accepted pregame run also writes
an immutable content-bound capture.  A same-evidence rerun is idempotent.
Later evaluation declares one capture and one outcome revision; it never uses
a post-kickoff revision as if it were the original recommendation.

Evaluation preserves the existing `start_sit` contract:

- lineup regret;
- best-legal-player hit rate;
- points lost versus hindsight best legal lineup;
- submitted versus recommended realized points;
- coverage and blocker rates by format, position, source class and league;
- contingency usefulness, without scoring an injury scenario as chosen unless
  the capture marked it active before lock.

At least 300 eligible rows and eight temporal periods remain required before a
new opponent-aware or risk-aware method can be considered for promotion.

## 10. Terra implementation order

1. Add a Python adapter that reads the canonical runtime contract and an exact
   deterministic assignment service with synthetic legality tests.
2. Add the research producer over hydrated current snapshots and verified app
   manifests, retaining Window 1C as an additive compatibility view.
3. Add status scenarios, schedule capture and player-level lock tests.
4. Add matchup capture, opponent max-mean context and advisory floor/ceiling
   views without an actionable max-win claim.
5. Add portfolio/cross-league summaries and immutable capture storage.
6. Add a manual workflow first; activate scheduled writes only after a green
   controlled run proves path allowlisting and idempotence.
7. Run targeted integrity tests, the current-storage preservation test and one
   deterministic personal release gate at tranche closure.
8. Preview-smoke the research/app consumer before any later app integration.

## 11. Required preservation tests

The implementation must prove at minimum:

1. a FLEX/Superflex fixture where pairwise greedy is suboptimal but exact
   assignment is correct;
2. a player is never assigned twice;
3. IDP, K and D/ST use canonical slot aliases;
4. A -> B -> A league processing reproduces A byte-for-byte and preserves
   scoring-signature isolation;
5. missing material projections fail closed;
6. best-ball produces no manual action;
7. Chopped floor output is advisory and disappears when P10 coverage is
   incomplete;
8. OUT exclusion and Q/D active/inactive contingencies are deterministic;
9. verified game locks freeze only affected players/slots;
10. matchup absence blocks opponent context but not a valid max-mean lineup;
11. retired/eliminated leagues do not leak into current actions;
12. immutable capture reruns are idempotent;
13. target-week realized statistics are absent from every input path; and
14. current storage, Window 1C, Window 1D and release invariants remain green.

## 12. Governance preserved

- M9 remains production champion.
- M10 prospective evidence remains research-only.
- No football model is trained, reweighted or promoted.
- No canonical player rank is changed.
- ADP/market does not enter lineup value.
- No Sleeper transaction or lineup mutation is executed.
- The production browser optimizer remains unchanged in this tranche.
- App integration requires a separate consumer contract and preview smoke.

