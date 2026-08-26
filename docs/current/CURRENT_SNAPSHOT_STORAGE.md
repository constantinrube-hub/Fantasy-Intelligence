# Current Snapshot Storage

## Purpose

`milestone5_current.json` is logically league-specific because exact scoring changes weekly fantasy projections. The previous repository layout stored the entire current player payload once per league, even though almost every player field was identical across leagues.

FIE 9.2.1 keeps the **same hydrated Milestone 5 current contract** while changing the physical storage layout.

## New layout

Each league keeps a small manifest:

```text
data/research/leagues/<league_id>/current/milestone5_current.json
```

The manifest contains league-specific metadata and references shared artifacts:

```text
data/research/shared/current/
  player_base.<content_hash>.json
  scoring/
    <scoring_signature>.<content_hash>.json
```

### Shared player base

The player base contains invariant current-player fields such as:

- player identity;
- team and position model;
- current features and model evidence;
- risk bands and activation state;
- predicted statistics;
- source lineage.

It deliberately excludes the two fields that were empirically found to vary with league scoring in the current repository:

- `decision_weekly_projection`;
- `sleeper_weekly_projection`.

### Scoring overlay

A scoring overlay contains:

- the scoring signature;
- the exact Sleeper scoring settings;
- non-default scoring-dependent projection pairs keyed by player ID;
- a `[0.0, 0.0]` default for omitted rows.

Leagues with the same compatible scoring signature reuse the same overlay.

### League manifest

The namespaced `milestone5_current.json` remains the canonical league URL. It stores:

- league ID and format;
- profile fingerprints;
- scoring signature;
- season/week metadata;
- source health and guardrails;
- summary and activation metadata;
- references to the shared player base and scoring overlay;
- a small exclusion list when that league intentionally has a narrower entity set.

The large `players` array and duplicate `scoring_settings` object are no longer repeated in every league directory.

## Runtime hydration

Browser owner: `app/current-snapshot-store.js`.

The hydrator:

1. loads the league manifest;
2. loads the referenced shared player base;
3. loads the referenced scoring overlay;
4. applies the league include/exclude contract;
5. restores `decision_weekly_projection` and `sleeper_weekly_projection`;
6. returns the same object shape that existing M5, D/ST and Kicker Intelligence code expects.

The browser-facing M5 contract therefore does **not** change.

`index.html`, `app/dst-intelligence.js`, and `app/kicker-intelligence.js` all use the same hydrator.

## Current repository result

Migration of the 19 managed league snapshots produced:

- 19 lightweight league manifests;
- 1 shared full player base;
- 17 unique scoring overlays for 19 leagues;
- exact logical hydration equivalence for all 19 original snapshots.

Storage changed from approximately:

```text
154.2 MB  league current snapshots before
  5.85 MB split current storage after
148.3 MB  reduction
~96%      reduction
```

The 19 league manifests themselves total only about 153 KB.

## Cloudflare `dist/` optimization

Source reproducibility and browser delivery have different needs. The source shared base retains all current rows, while `tools/build_dist.py` applies the existing relevance rule before deployment.

Across the current 19-league portfolio, only about 975 unique player/entity rows are required by at least one league after runtime compaction. The build therefore emits a second deduplicated runtime store under:

```text
dist/data/research/shared/current/
```

The shared runtime current store is approximately **808 KB**, and the complete deployed current-snapshot footprint including all 19 lightweight league manifests is approximately **0.98 MB**, instead of about **6.63 MB** of per-league compact snapshots.

Each deployed league still receives its exact compact row order and scoring behavior after hydration.

## Refresh workflow

`build_current_snapshot.py` still produces a normal full logical snapshot. This keeps the model producer simple and independently inspectable.

After all requested league snapshots are built, run:

```bash
python research/deduplicate_current_snapshots.py
```

Then build governance. The GitHub current-season and bulk-onboarding workflows now do this automatically in the correct order:

```text
build full current snapshots
        ↓
deduplicate shared storage
        ↓
build governance manifests
        ↓
production audit
        ↓
commit league + shared artifacts
```

Governance hashes therefore refer to the final lightweight league manifest rather than to a temporary full file.

## Integrity guarantees

`research/integrity_current_storage_test.py` verifies:

- every namespaced current snapshot uses split storage;
- league manifests no longer contain duplicate player/scoring payloads;
- all shared references exist;
- hydration restores the expected player count and scoring signature;
- compatible equal scoring signatures deduplicate;
- no unreferenced shared current files remain;
- source storage stays within a bounded size;
- all browser M5/D/ST/Kicker loaders use the shared hydrator.

`research/integrity_dist_hygiene_test.py` additionally hydrates the deployed manifests and verifies the existing position-aware runtime compaction rules.

## Content-addressed safety

Shared files are content-addressed. A future refresh that changes invariant current-player data can create a new player-base hash without corrupting older league manifests. Once every manifest has moved to the new shared artifact, the deduplication script removes unreferenced versions.

This is intentionally safer than one mutable global `player_base.json`.

## Operational rule

Do not manually put a full `players` array back into each league's `current/milestone5_current.json`.

If a manual current build produces a full snapshot, finish the operation with:

```bash
python research/deduplicate_current_snapshots.py
```

before committing or building the release.
