# Window 1A — Prospective Evidence Backbone + 2026 Baseline Freeze

## Closed scope

Window 1A adds research-only, point-in-time acquisition and does not change M9, M10 activation, app/runtime behavior, rankings, waiver recommendations, or any predictive feature.

The branch was reconciled without reset or history loss. `origin/audit-implementation-2026-09` at `35afc3c` was a direct ancestor of `origin/main`; the local audit branch was fast-forwarded to the live merged head `c2e9f51` before implementation.

## Canonical evidence owners

- `research/point_in_time_capture.py` owns canonical JSON identity, payload hashes, observed-time parsing, cutoff selection, and collision-safe first writes under `fie-point-in-time-source-envelope-v1`.
- `research/capture_fie_availability.py` and its daily workflow remain byte/schema compatible and unchanged. The Window 1A characterization fixture proves its compact row shape is preserved.
- `research/capture_fie_waivers.py` owns raw Sleeper source envelopes, normalized transaction evidence, cycle state, descriptive behavior features, and the portfolio visibility audit.
- `research/capture_fie_weather.py` owns pregame Open-Meteo response envelopes and normalized research-only context evidence. It records exact `observed_at`; because the selected Forecast endpoint does not expose model initialization time, `forecast_run_at` remains null with `NOT_EXPOSED_BY_PROVIDER` rather than being invented.
- `research/freeze_fie_2026_baseline.py` owns the immutable versioned season baseline manifest and references existing governed league/profile/current/ranking artifacts by SHA-256.

## Existing waiver consumer trace

The producer of `state.transactions.profiles` is `index.html::loadLeagueTransactions()` followed by `index.html::buildTransactionProfiles()`.

The existing loader filters to `status === "complete"`, so failed/rejected claims never reached the current beta FAAB context. Window 1A preserves this production path and creates a separate research evidence chain. No app consumer is switched in this tranche.

## Live prospective evidence

- 22 enabled leagues and both Sleeper rounds 0 and 1 were observed at the current point in time: 44 immutable source envelopes and 1,612 returned transactions.
- 11 league/week observations exposed at least one failed/rejected waiver claim, including source-provided failure reasons and bids where present.
- 2 observations exposed completed waiver winners without a failed claim in the same response.
- 31 observations did not establish losing-claim visibility.
- The audit therefore never asserts `COMPLETE_OBSERVED` and never treats absent claims as losses or zero bids.
- One league returned 404 for league/roster context while its transaction endpoints remained observable. The context errors are retained separately; its cycle state is `SOURCE_UNAVAILABLE`, while its returned transaction payload remains immutable evidence.

Round 0 is retained only as a current observation of the provider's preseason/offseason endpoint. It is not relabeled as a regular-season week and is not normalized into the week-1 transaction schema.

## Weather and baseline

- Week 1 contains 16 future games and 16 immutable Open-Meteo provider responses.
- The normalized context cutoff is the first regular-season kickoff at `2026-09-10T00:20:00+00:00`.
- The versioned baseline contains all 22 enabled leagues and all six formats.
- Its latest governed source timestamp is `2026-09-01T10:08:06.043444+00:00`, before the first kickoff, so it is truthfully classified `PRESEASON_ELIGIBLE`.
- Per-league runtime/current readiness remains exactly as recorded in each governed active release; the baseline does not upgrade blocked or empty states.

## Scheduled lifecycle

- Availability retains its existing daily cadence unchanged.
- Waiver evidence uses an independent Tuesday-through-Thursday cadence to preserve multiple status observations around processing windows.
- Weather uses an independent game-window cadence to retain multiple lead times without overwriting earlier forecasts.
- Both new thin callers use one reusable first-write workflow and commit only their authorized `data/research` paths on `main`.

## Boundaries preserved

- M9 remains production champion.
- Tranche 7D remains the separate research-only M10 prospective workflow.
- No backfill, tuning, selection, promotion, shadow integration, probability model, optimization, report UI, Weekly Actions, Trench, or Context predictive feature was added.
- ADP/market remains outside the football model.
