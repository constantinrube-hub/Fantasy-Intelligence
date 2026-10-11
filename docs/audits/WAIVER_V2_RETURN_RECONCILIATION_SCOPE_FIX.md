# Waiver-v2 return reconciliation scope correction

The shared E4 event ledger includes individual returners at every position.
The offensive outcome table deliberately filters QB/RB/WR/TE. Comparing those
universes produced nine kickoff and five punt player-week mismatches from six
CBs in the real observed 2026 source. Their published raw return yards agree
with the PBP values; missing defensive rows were incorrectly treated as zero.

Within the existing approved exact-scoring extension contract, event runs now
write an additional hash-bound all-position reconciliation table. E5 passes it
to E4; offensive targets and QB sack reconciliation retain their original
source. Null/missing aggregates, duplicate keys, unresolved identities and
conflicting values fail closed. Legacy callers retain the older input and
cannot silently certify absent aggregates. No activation or scoring weights,
model horizon, M9 authority, app behavior or transaction gate changes.

The partial-2026 before/after source replay preserves 1,415 event rows and
removes all 14 return mismatches. One multiple-fumble and three lateral-play
blocker records remain; field-goal-return roles remain unavailable. This does
not validate a completed season, historical availability, models or forecasts.
Rebuild historical evidence in a new namespace; never overwrite prior reports.
