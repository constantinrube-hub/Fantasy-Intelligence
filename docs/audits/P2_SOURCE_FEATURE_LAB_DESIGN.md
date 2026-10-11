# P2 source and feature laboratory — 2026-10-11

## Boundary

This protocol precedes implementation. Continue under the user's overnight
instruction; no production feature or model promotion is authorized. Existing
context, performance, identity and scoring owners remain authoritative.
New tables are deterministic research derivations with input content hashes.

## Sources and time

Archive unchanged nflverse CSV bytes for PBP, PFR snap counts and schedules.
Capture time means observed locally, never original historical availability.
Raw bytes and receipt are first-write files under content-addressed captures.
Readers recheck SHA256, target, endpoint and observation cutoff. A new download
cannot repair a historical point-in-time gap. Target and later weeks are
excluded from feature history; explicit missing inputs stay missing.
The approved endpoints are the existing nflverse owners' endpoints.

## Deterministic tables

PBP: unique game/play keys; REG plays only; no-play penalties excluded from
scrimmage opportunities. Group team/week for rush/pass attempts, EPA, success,
and neutral pass rate (first three quarters, score difference at most seven).
Sacks count in passing attempts via provider pass_attempt. EPA/success use only
observed finite inputs and report denominator coverage. Do not call this PROE
or pressure rate. Group fixed drives by game/team, use provider transition and
start yard line; unavailable transition remains UNKNOWN. Describe drive yards,
first downs, touchdowns without converting them into calibrated probabilities.
Red zone is yardline_100 <=20, goal line <=5; rushing_attempt and named receiver
IDs define observed opportunities. Neither charted routes nor end-zone targets
are inferred. Source GSIS IDs retain namespace; canonical joins are separate.

Snaps: preserve PFR keys, counts and provider percentage values. No name join.
Percentage units stay provider units until a source-specific scale contract is
verified. Routes/alignment remain unsupported. An external canonical mapping
requires its own governed identity owner and is not inferred here.
Rest: use existing normalized schedule kickoff timestamps, source observations
and team identity. Calculate prior-game kickoff gaps and consecutive away games;
unknown travel coordinates and international flags remain missing. Kickoff gaps
are not physiological rest or a fitted performance effect.

Role changes: deterministic descriptive target/rush-share history. Exclude
same/future week and records observed after cutoff. Compare last two available
games with preceding three; require denominators and a team-consistent source
identity. Report both deltas and whether both recent games move the same way.
These windows are a research diagnostic, not a validated waiver trigger.

## Experiments

Each of the nine existing research IDs gets a predeclared source/target/cutoff/
ablation contract. The runner accepts stored candidate and baseline forecasts,
checks content-bound evidence and chronological evaluation after training,
and reports paired errors by scoring signature/week. It neither trains models
nor promotes a result. Missing evaluation rows produce BLOCKED_MISSING_INPUTS.
D/ST/kicker strategy testing still needs immutable availability universes and
preseason hold definitions; weather needs realized counterpart observations.
Field position/red zone/team tables are descriptive until out-of-sample and
prospective incremental evidence exists. Negative results are retained.

## References

- https://nflreadr.nflverse.com/articles/dictionary_snap_counts.html
- https://nflfastr.com/reference/field_descriptions.html
- Existing research/fie_research.py and window2a_trench_evidence.py source owners.

## Acceptance

Hash/time/path tampering, duplicate play IDs, target leakage, missing metrics,
snap ID duplication, team changes, unknown role denominators and future feature
observations fail or produce explicit blockers. Each source and result is
immutable. Formal results and promotion stages remain pending real evidence.
