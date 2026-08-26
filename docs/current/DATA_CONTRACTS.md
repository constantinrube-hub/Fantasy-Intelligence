# Data Contracts

## League profile

A league profile contains both full Sleeper settings and a structural identity contract.

### Identity-affecting

- league ID;
- resolved format;
- scoring settings;
- roster positions;
- total rosters;
- stable structural settings;
- season / season type;
- explicit research cohort constraints.

### Diagnostic only

Volatile operational settings such as current leg, last Chopped leg, and waiver-run timestamps do not belong in the fingerprint.

## Scoring contract

Source: `config/contracts/runtime-contracts.json`.

Each scoring family defines:

- match rule;
- affected fantasy positions/entities;
- whether it is team D/ST, individual special teams, offense, IDP or kicker related.

Unknown keys remain conservative and must appear in Data Quality rather than being silently ignored.

## Player identity

Sleeper player ID is canonical wherever available.

Synthetic IDs are allowed only for entities that genuinely have no Sleeper identity and must be namespaced.

## Current player features

The research-generated bridge may expose:

```text
snap_share
target_share
carry_share
qb_rush_share
red_zone_target_share
red_zone_carry_share
inside_10_carry_share
inside_5_carry_share
opportunity_change_score
competition / environment features
```

Each row carries lineage and activation eligibility. Feature existence does not imply production permission.

## Model config

`config/model-config.json` controls production promotion of candidate decision logic.

Production code must never infer promotion from the presence of a model file.

## Release descriptor

`config/release.json` is the canonical human-readable release identity. Generated browser/function descriptors derive from it.

## Current snapshot storage contract

The logical hydrated `milestone5_current` object remains the consumer contract. Physical storage may use `fie-current-split-v1`, where a namespaced league manifest references a content-addressed shared player base and a scoring overlay. Consumers must load through `app/current-snapshot-store.js` in the browser or `research/current_snapshot_storage.py` in Python when player rows are required. Top-level league metadata remains directly readable from the manifest for governance/readiness checks.

Do not assume `players` or `scoring_settings` are physically embedded in the league manifest.
