# Tranche 3C Player Identity Preflight — Harness Correction

## Why this correction exists

GitHub run `33775902008` was displayed as successful, but the identity
characterization itself failed with:

`AssertionError: missing function synthesizePlayerId`

The production source was not at fault. The first characterization assumed that
the synthetic fallback lived in a separate `synthesizePlayerId()` function.
Current Core actually implements the fallback inline inside `playerId()`.

The workflow also used:

`node ... | tee ...`

without Bash `pipefail`, so the successful `tee` process masked the failing Node
exit status.

That green run therefore must **not** be accepted as a completed 3C preflight.

## Revision 2

The corrected characterization tests the actual current source:

- Core `playerId()`:
  `sleeperId -> player_id -> playerId -> id -> synthetic:position:team:name`
- Core `PlayerIdentity.byId()`:
  `sleeperId -> player_id`
- current-player-features:
  research `sleeper_id` -> live `sleeperId`
- current-snapshot-store:
  `sleeper_id` -> `canonical:<canonical_player_id>`
- Value Finder:
  Sleeper-ID lookup -> normalized-name fallback

It also freezes a direct conflict fixture in which Core selects `player_id`
while current-snapshot storage selects `sleeper_id`.

Expected valid baseline output:

`KNOWN_GAP_REPRODUCED player identity is fragmented across stable IDs, synthetic IDs and display-name fallback`

## Workflow hardening

All characterization pipelines now use:

`set -euo pipefail`

Therefore a failing producer process cannot be hidden by `tee`.

The workflow additionally greps the produced log for the exact expected
KNOWN_GAP marker before source capture proceeds.

## Lifecycle correction

Tranche 3A is already complete. Its active push workflow still expected the
pre-3B DataClient bug and therefore produced a false red status on later
manifest commits.

The replacement 3A workflow is manual-only and tests only preserved 3A target
contracts. It no longer requires subsequently fixed defects to remain broken.

## Scope

No production runtime file changes in this correction.

C10-007 production implementation remains blocked until this revised preflight
is genuinely green.
