# Multi-League Deployment Steps

## 1. Commit this repository update
Replace/add the files from this package in the existing GitHub repository, preserving the directory structure, then commit to `main`.

Cloudflare Pages should redeploy automatically from GitHub as before.

## 2. Preserve the existing Redraft historical profile
After the code commit is live, open GitHub:

**Actions → Migrate Existing FIE Profile to League Namespace → Run workflow**

Use:
- League ID: `1313697754907697152`
- Format: `REDRAFT`

That League ID comes from the committed M1 bundle's own Sleeper provenance. The workflow refuses a different ID unless it matches the historical source artifact.

The migration is non-destructive. It does not remove or rewrite the legacy global M1-M6 files.

## 3. Refresh Redraft current-season data
The currently committed global current snapshot does not share the historical M5 scoring signature, so its governance is already fail-closed. After migration run:

**Actions → Refresh FIE Current Season → Run workflow**

Use:
- League ID: `1313697754907697152`
- Season: blank
- Week: blank
- Governance mode: `AUTO`

This creates a fresh namespaced current snapshot and correct namespaced governance.

## 4. Validate Redraft in the app
Load the Redraft league and check Milestone 6 / governance. The desired state is:
- `global_operator_auto` PASS
- `operator_auto` PASS
- `league_id_match` PASS
- `profile_fingerprint_match` PASS
- `current_profile_live_match` PASS
- `format_match` PASS
- `artifact_scope_match` PASS
- M4/M5/M6 complete PASS
- scoring signature match PASS
- fresh snapshot PASS
- eligible players PASS
- SHA-256 hashes verified

If one of these fails, the app remains on its safe fallback path.

## 5. Add the Chopped league only after Redraft is preserved
Run:

**Actions → Build FIE Research Milestones 1-6**

Use:
- League ID: your Chopped League ID
- League format: `CHOPPED`
- Full raw cache: normally `false`

This writes only to `data/research/leagues/<CHOPPED_ID>/` and cannot replace the Redraft namespace.

## 6. Activate the Chopped current profile
After its M1-M6 workflow succeeds, run:

**Actions → Refresh FIE Current Season**

Use:
- League ID: the same Chopped League ID
- Season/week: blank
- Governance mode: `AUTO`

## 7. Switching thereafter
No GitHub workflow is required when switching between already-generated leagues.

The browser resolves:

`loaded Sleeper League ID → matching research directory → matching current snapshot → matching governance`

So Redraft → Chopped → Redraft should restore each league's own research automatically.

## Scheduled refresh behavior
The scheduled Current Season workflow reads `data/research/leagues/registry.json` and refreshes every enabled league with `current_refresh=true`. Historical M1-M6 research is not rerun on every switch or scheduled current refresh.

## Emergency rollback
- Per league: set that league's `governance/operator_override.json` to `CONTROL`, or run Current Season for that league with governance mode `CONTROL`.
- Every league: set global `data/research/governance/operator_override.json` to `CONTROL`.

The existing V8.2.2 fallback remains available when empirical governance is closed.
