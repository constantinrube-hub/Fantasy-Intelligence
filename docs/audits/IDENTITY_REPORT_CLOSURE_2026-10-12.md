# Roster identity and report continuity closure

Base main: `c61c911a`, including PR80. This tranche combines four compatible
source/presentation fixes; it does not retrain models or promote waiver gates.

## Steps completed

1. Trace all four partial roster surfaces to exact Sleeper IDs. Kansas City
   (`KC`) and Carolina (`CAR`) are valid team entities absent from the current
   forecast universe. `14086` is a rostered, provider-confirmed Terrelle Smith
   record with no NFL team; it is excluded by the active-team catalog filter.
   Missing forecasts and missing team are not missing provider identities.
2. Preserve no-team identities in a separate `identity_only_players` catalog
   map, leaving the browser's active-team `players` map intact. Validate source
   key/ID agreement, NFL sport, disjoint maps, and every retained record. The
   observed real catalog retains 2,758 active-team rows plus 9,231 separate
   identity-only rows and remains under the existing 8 MB compact-file limit
   (approximately 3 MB total).
3. Bind the roster surface's catalog fallback through the existing app-index
   hash and observation cutoff. Only exact provider IDs can bind missing
   forecast rows; D/ST retains the existing team canonical entity. Forecasts,
   intervals and activation gates stay missing/off for identity-only rows.
   Source/catalog/index hashes travel with the surface. Unknown provider IDs,
   source drift, collisions and future observations remain blocked.
4. Give newly published Window 1C reports an actual producer issuance clock,
   separate from their input as-of timestamp. Older archives retain unknown
   issuance. Enable PR80's Basic/Expanded/Advanced views in the existing 1D
   decision-ledger publication step. Every view preserves the original advice,
   confidence, impact and authority.

## Evidence and limits

The three full provider records are preserved at
`data/operations/identity-closure/2026/2026-10-12/provider-source.json` with their
actual observation time. This newly obtained source cannot repair an older
pregame capture. The reported roster is an observation; an old/no-team provider
record does not establish player availability, correct manager intent, roster
legality or a zero projection. No stored owner output was rewritten or made
fresh by changing its timestamp.

Existing reports remain immutable. The next real refresh regenerates the
catalog; its manual 1C/1D chain can then verify the live identity coverage and
new ledger presentation. The patch itself does not dispatch workflows.

## Why offensive waiver eligibility stays blocked

The previously replayed 2019–2025 event source still has two conflicting
fumble-loss roles, six recovery-touchdown attribution blockers, thirteen
kick-return and two punt-return semantic blockers, and two long-play
reconciliation blockers. Exact dataset completeness was not asserted by that
diagnostic run. The established scorer correctly rejects unsupported exact
rules. Current offensive projections also depend on the separate M5 model and
format/position activation gates, not just a restored player identity.

Neither ignoring rare scoring rules nor relabeling a current Sleeper mean as
an eligible FIE waiver forecast repairs those sources. These remaining tasks
require authoritative event evidence followed by the established exact-label,
evaluation and governed-model checkpoints. Distribution/calibration and FAAB
economics require their separate design boundary. No valid source correction
for those conflicts was found in this bounded tranche.

## Verification

Focused checks cover actual catalog compaction, no-team identity preservation,
wrong-sport and conflicting-ID rejection, null forecasts and false activation,
catalog hash/cutoff tampering, existing exact-row precedence, real issuance
versus input-as-of, and preservation of old unknown issuance. Existing owner
report and decision-view tests remain required. Closure uses the deterministic
personal release gate and synchronized generated manifests/dist.
