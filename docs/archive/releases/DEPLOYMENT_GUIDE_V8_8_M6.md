# Fantasy Intelligence Engine V8.8-M6 — Final Deployment & Operations Guide

**Verified deployment design:** 23 August 2026  
**Target:** GitHub-connected Cloudflare Pages project  
**Runtime:** Static `index.html` + Cloudflare Pages Functions + GitHub Actions generated research/current JSON

---

# 1. What you are deploying

V8.8-M6 is no longer only a single HTML file. The complete production system contains four layers:

1. **Browser application** — `index.html`
2. **Cloudflare Pages Functions** — `/functions`
3. **Historical research/model pipeline** — `/research` + M1–M6 JSON bundles
4. **Current-season automation and governance** — GitHub Actions + `/data/research/current` + `/data/research/governance`

The standalone HTML is useful for inspection, but **the ZIP/repository tree is the deployable product**.

---

# 2. Required repository tree

After extracting the final ZIP, the **repository root** should directly contain:

```text
/
├── index.html
├── _routes.json
├── wrangler.toml
├── functions/
│   └── api/
│       ├── health.js
│       └── data/
│           └── [[path]].js
├── data/
│   └── research/
│       ├── milestone1.json
│       ├── milestone2.json
│       ├── milestone3.json
│       ├── milestone4.json
│       ├── milestone5.json
│       ├── milestone6.json
│       ├── current/
│       │   └── milestone5_current.json
│       ├── governance/
│       │   ├── active_release.json
│       │   └── operator_override.json
│       └── market/
│           └── sleeper/
├── research/
│   ├── fie_research.py
│   ├── fie_m2.py
│   ├── fie_m3.py
│   ├── fie_m4.py
│   ├── fie_m5.py
│   ├── fie_m6.py
│   ├── build_current_snapshot.py
│   ├── fie_governance.py
│   ├── ...validators/tests...
│   └── requirements.txt
└── .github/
    └── workflows/
        ├── build-fie-research.yml
        └── build-fie-current.yml
```

## Important

Do **not** upload the folder `FIE_V8_8_M6` as one nested folder inside the existing repo while leaving Cloudflare's root directory at the repository root.

Either:

- place the **contents** shown above directly in the existing repository root, which is recommended; or
- deliberately configure Cloudflare's Root directory to the nested folder.

For your existing setup, keep it simple: **the contents belong at repository root**.

---

# 3. Before replacing the current version

Recommended safe workflow:

1. In GitHub, create a branch such as `v8-8-m6-final`.
2. Put the full package contents into that branch.
3. Confirm the repository tree matches Section 2.
4. Let Cloudflare create a preview deployment for the branch if preview deployments are enabled.
5. Check the preview page loads and `/api/health` responds.
6. Merge the branch into your production branch, normally `main`.

Cloudflare Pages Git integration automatically builds/deploys pushes to configured production/preview branches, so the branch-first approach gives you a clean preview before production.

---

# 4. Cloudflare Pages settings

For the final package, use these settings:

| Setting | Value |
|---|---|
| Framework preset | None / no framework |
| Production branch | `main` (or your actual production branch) |
| Root directory | leave empty if package contents are at repository root |
| Build command | `exit 0` |
| Build output directory | `.` |

## Why `exit 0` rather than a frontend build command?

There is nothing to compile for the static app. Cloudflare's static HTML guidance recommends `exit 0` when no build is required and Pages Functions are used.

## Pages Functions

The `/functions` directory must remain at the **root of the Pages project**. Do not move `health.js` or `[[path]].js` next to `index.html` without their folder structure.

The proxy route depends on:

```text
functions/api/data/[[path]].js
```

and the health endpoint depends on:

```text
functions/api/health.js
```

---

# 5. First production deployment

After merging/pushing the full package to `main`:

1. Open **Cloudflare → Workers & Pages → your Pages project → Deployments**.
2. Confirm the latest deployment completed successfully.
3. Open the production site.
4. Confirm the normal V8.8-M6 interface loads.
5. Open:

```text
https://YOUR-DOMAIN/api/health
```

Expected key fields:

```json
{
  "ok": true,
  "app": "Fantasy Intelligence Engine",
  "version": "V8.8-M6",
  "runtime": "Cloudflare Pages Functions"
}
```

At this point **M6 should still be fail-closed**. That is correct. The distributed package intentionally contains placeholder research/current files rather than fabricated NFL findings.

---

# 6. GitHub Actions permissions

The two supplied workflows need to commit generated JSON artifacts back to the repository.

They explicitly request:

```yaml
permissions:
  contents: write
```

Before the first run:

1. Open **GitHub repository → Settings → Actions → General**.
2. Confirm GitHub Actions is enabled.
3. Under **Workflow permissions**, ensure repository/organization policy does not prevent the workflow's requested write access.

If the repository has branch protection/rulesets that reject bot pushes to `main`, the build can finish successfully but fail at `git push`. In that case you must either allow the repository's GitHub Actions token/bot to update the production branch, or adapt the supplied workflows to commit through a permitted branch/PR process.

For a normal personal repository without restrictive branch rules, no extra secret or personal access token should be required.

---

# 7. Generate the real M1–M6 historical research

This is the first workflow you should run after the code itself is deployed.

## GitHub steps

1. Open the repository.
2. Tap/click **Actions**.
3. Select:

**Build FIE Research Milestones 1-6**

4. Select **Run workflow**.
5. Use the production/default branch.
6. Enter your primary Sleeper league ID in `league_id`.
7. Leave `full_raw_cache` as **false** for the normal first build.
8. Run the workflow.

## Why enter the league ID?

The historical raw football models are reusable, but historical fantasy scoring and decision validation must be evaluated under an exact fantasy scoring profile.

Using the Sleeper league ID lets the pipeline pull the scoring settings and create a scoring signature. That signature is later checked against the current-season snapshot.

## What the workflow does

It automatically:

1. installs the research dependencies;
2. runs deterministic M1–M6 integrity tests;
3. builds M1 historical backbone;
4. builds M2 opportunity/xFP research;
5. builds M3 advanced/young-player research;
6. builds M4 feature governance/raw-stat models/market benchmark;
7. builds M5 Draft/Waiver/Weekly/format decision policies;
8. builds M6 second-wave research;
9. rebuilds governance in fail-closed state;
10. validates every bundle;
11. commits updated M1–M6 JSON files and governance back to GitHub.

Because your Cloudflare Pages project is Git-connected, that repository update should create a new Pages deployment.

## Expected state afterward

In **Lab → M6 Production**:

- M1–M6 research should show empirical output rather than `pipeline_ready_not_run`.
- Step 28 can show validated/diagnostic/blocked results.
- Runtime can still remain on V8.2.2 because the current-season snapshot has not yet been created.

That is expected.

---

# 8. Generate the first current-season snapshot

Next run the second workflow.

1. GitHub → **Actions**.
2. Select:

**Refresh FIE Current Season**

3. Select **Run workflow**.
4. Recommended inputs for the first run:

| Input | Recommendation |
|---|---|
| `league_id` | same Sleeper league used for M1–M6 |
| `season` | leave blank unless you deliberately want an override |
| `week` | leave blank unless you deliberately want an override |
| `governance_mode` | `AUTO` |

5. Run the workflow.

## What Step 29 does

The workflow builds the current pregame snapshot using only information from **before the target week**.

It:

- identifies the target season/week;
- fetches current historical-to-date data;
- removes all realized stats from the target week;
- recreates the required M4 model features;
- predicts raw stats;
- scores those stats using the matching league scoring settings;
- uses a validated Sleeper blend only when historical evidence supports it;
- applies only the M5 decision gates that passed their own tests;
- captures an immutable Sleeper projection snapshot when pregame-eligible;
- rebuilds the Step 30 governance manifest.

The resulting current file is:

```text
data/research/current/milestone5_current.json
```

It is intentionally still named `milestone5_current.json` because V8.7-M5 defines the browser decision contract; V8.8-M6 is the producer/governance layer around that contract.

---

# 9. When M6 is allowed to activate

AUTO mode does **not** mean “always use FIE.”

The active manifest permits M5 decision overrides only if all of the following pass:

- M4 complete;
- M5 complete;
- M6 complete;
- current snapshot complete/ready/active;
- current snapshot produced by V8.8-M6;
- M5 browser-contract version matches;
- historical/current scoring signatures match;
- snapshot age ≤18 hours;
- target-week realized stats exclusion is confirmed;
- at least one player has enough history/feature coverage to be activation-eligible.

A current FIE player additionally requires:

- a historically validated weekly position model;
- at least **2 completed previous games**;
- at least **45% required feature coverage**;
- a finite FIE projection.

The individual Draft/Waiver/Weekly/format gates from M5 remain separate.

Therefore, even when global governance is green, one player/position/decision may use FIE while another continues using the V8.2.2 fallback.

---

# 10. Early-season behavior

Do not be alarmed if M6 remains inactive at the start of the season.

The current builder requires at least two completed prior games for current FIE activation. Therefore:

- preseason / Week 1: generally fallback;
- after Week 1: generally still fallback;
- Week 3 onward: eligible positions/players can begin activating if research gates, feature coverage and governance all pass.

This is intentional protection against pretending the historical model has enough 2026 role evidence when it does not.

---

# 11. Automatic current-season refresh

The supplied workflow is scheduled four times per day in the NFL/preseason months:

```yaml
cron: "17 5,11,17,23 * 1,2,8-12 *"
```

The file comments and schedule use UTC.

Each successful scheduled run can:

- refresh current nflverse/Sleeper-derived inputs;
- create a first-write immutable Sleeper market snapshot;
- rebuild current projections;
- rebuild governance;
- commit changed artifacts to GitHub.

Because the Cloudflare project is Git-integrated, those committed changes can generate a new production deployment.

## GitHub schedule behavior to know

- Scheduled workflows run from the default branch.
- The workflow file must exist on the default branch.
- GitHub can delay scheduled runs during heavy load.
- On public repositories, scheduled workflows can be disabled after 60 days without repository activity.

Before each NFL season, confirm that **Refresh FIE Current Season** is still enabled in GitHub Actions.

---

# 12. Normal weekly operating routine

After the initial setup, you should normally need to do almost nothing.

### Automated

- current-season refreshes;
- current projections;
- current Sleeper snapshots;
- governance checks;
- GitHub commits;
- Cloudflare redeploys.

### Manual historical rebuild recommended when

Run **Build FIE Research Milestones 1-6** again when:

- the full prior NFL season has been added to the historical sample;
- you make research/model-code changes;
- a new source materially expands historical coverage;
- you deliberately change the primary empirical Sleeper scoring profile;
- enough new immutable Sleeper projection history exists that you want to recalibrate FIE-vs-Sleeper blend evidence.

Do **not** run the expensive M1–M6 historical rebuild four times per day. The current workflow exists specifically so the model can update without retraining the historical stack.

---

# 13. Using multiple leagues/scoring systems

V8.8-M6 is safe with multiple loaded Sleeper leagues, but the empirical research stack is generated for **one exact scoring signature at a time**.

### Matching league

If the loaded league's scoring matches the active research/current scoring signature:

- M6 may activate eligible M5 decision components.

### Different scoring league

If the scoring profile materially differs:

- the scoring-compatibility guard rejects the research override;
- the app falls back to the existing V8.2.2 league-specific logic.

Nothing is silently cross-applied.

### If you want M6 active for a different league

Run the full **Build FIE Research Milestones 1-6** workflow using that league's Sleeper ID, then run **Refresh FIE Current Season** using the same league.

Current design intentionally maintains one promoted empirical scoring profile at a time rather than mixing incompatible historical validation results.

---

# 14. Verify that production is healthy

Use these checks after the two first workflows.

## A. Cloudflare

Latest production deployment should be successful.

## B. Health endpoint

`/api/health` should report:

- `ok: true`
- `version: V8.8-M6`
- `runtime: Cloudflare Pages Functions`

## C. M6 Production panel

Open:

**Lab → M6 Production**

Check:

- research bundle loaded;
- current season/week are correct;
- current snapshot age is sensible;
- `target_week_leakage_guard` passes;
- scoring signature passes;
- operator mode is AUTO;
- governance explains either `runtime enabled` or the exact fallback reason.

## D. Governance file

The generated:

```text
data/research/governance/active_release.json
```

contains:

- exact active/control build;
- all promotion checks;
- current snapshot age;
- decision gates;
- model lineage;
- artifact SHA-256 hashes;
- rollback rule.

## E. League sanity check

Load your Sleeper league and inspect a handful of players:

- positions with no validated gate should behave exactly as the legacy model;
- active M5/M6 players should identify the current projection source;
- Draft-only, Waiver-only and Weekly-only activations should remain separated.

---

# 15. Emergency model rollback — fastest option

If you distrust the new research outputs but the website itself is healthy, **do not roll back the entire codebase first**.

Use the model-governance rollback.

## Steps

1. GitHub → Actions.
2. Open **Refresh FIE Current Season**.
3. Run workflow manually.
4. Set:

```text
governance_mode = CONTROL
```

5. Other inputs can remain blank unless you want to refresh the current snapshot at the same time.
6. Let the workflow commit the governance update.
7. Let Cloudflare deploy the resulting commit.

## Result

- M5/M6 research-driven decision overrides are disabled.
- The app stays on V8.8-M6 code/UI.
- Live decision scoring reverts to the frozen **V8.2.2 fallback path**.
- No model code edits are necessary.

## Re-enable later

Run the same workflow with:

```text
governance_mode = AUTO
```

AUTO does not force activation. It merely allows the normal evidence/freshness/compatibility gates to decide again.

---

# 16. Full Cloudflare deployment rollback

Use this when the **code/deployment itself** is bad, not merely when you distrust a model output.

Cloudflare Pages supports rollback to any previous successfully built production deployment.

## Steps

1. Cloudflare → Workers & Pages.
2. Open the Fantasy Intelligence Engine Pages project.
3. Open **Deployments**.
4. Find the previous successful production deployment.
5. Open its **three-dot menu**.
6. Select **Rollback to this deployment**.
7. Confirm.

This changes the production deployment immediately to that prior successful build.

Preview deployments are not rollback targets, so select a prior successful **production** deployment.

---

# 17. Git rollback vs Cloudflare rollback

They solve different problems.

### Governance CONTROL
Use for:
- suspicious projections;
- unexpected research behavior;
- wanting to compare against the old model;
- current model-data quality concerns.

Result: newest code remains deployed, V8.2.2 decision path becomes live.

### Cloudflare deployment rollback
Use for:
- broken JavaScript/UI;
- broken Pages Function;
- bad repository deployment;
- production page does not load.

Result: entire website deployment returns to a previous production build.

### Git revert
After an emergency Cloudflare rollback, you should still fix/revert the bad commit in GitHub. Otherwise a later push can deploy the bad repository state again.

---

# 18. If GitHub Action cannot push its generated files

Symptom:

- analysis completes;
- workflow fails only at `git push`.

Check:

1. Repository → Settings → Actions → General → Workflow permissions.
2. Repository branch protection/rulesets.
3. Organization policies if the repository belongs to an organization.

The workflows already request `contents: write`; however, repository/organization branch rules can still prohibit a direct push.

For the supplied configuration, the simplest operating model is a production repository where the two FIE workflows are allowed to commit generated data artifacts to the default branch.

---

# 19. If Cloudflare does not redeploy after an Action commit

Check:

1. Did the GitHub workflow actually commit and push a changed file?
2. Is Cloudflare Pages still connected to this exact repository?
3. Is `main` still the configured production branch?
4. Is automatic production-branch deployment enabled?
5. In Cloudflare → Settings → Builds, inspect branch control.
6. Check the GitHub/Cloudflare installation status if Cloudflare reports an SCM warning.

Cloudflare allows automatic production/preview branch deployments to be disabled. Make sure production deployment is enabled if you expect generated-data commits to deploy automatically.

---

# 20. If `/api/health` gives 404

Most likely cause: incorrect repository/build structure.

Confirm:

```text
functions/api/health.js
```

is present at the **Pages project root**, with the full `/functions` hierarchy preserved.

Also confirm you deployed through Git integration/normal Pages deployment. Cloudflare's dashboard Direct Upload does not support Pages Functions.

---

# 21. If research says `pipeline_ready_not_run`

That is the shipped placeholder state.

Run:

**Actions → Build FIE Research Milestones 1-6**

If the workflow failed, inspect the failed GitHub Action step rather than editing the JSON manually.

---

# 22. If runtime remains on fallback after successful research

Open **Lab → M6 Production** and look at the failed Step 30 checks.

Common legitimate reasons:

- no fresh current snapshot;
- current snapshot older than 18 hours;
- target Week 1/2 with insufficient completed games;
- no activation-eligible players;
- loaded/research scoring mismatch;
- M4/M5/M6 validation did not produce an eligible gate;
- operator mode remains CONTROL.

Do not manually force `runtime_enabled=true` in the JSON. Fix the failed input/check or accept the fallback.

---

# 23. Recommended production sequence, condensed

Use this exact order:

1. **Back up current repo / use a new branch.**
2. **Place the complete V8.8-M6 package contents at repo root.**
3. **Preview branch in Cloudflare.**
4. **Merge/push to `main`.**
5. **Verify Cloudflare deployment + `/api/health`.**
6. **GitHub Actions → Build FIE Research Milestones 1-6**, using primary Sleeper league ID.
7. **Wait for its committed research bundle to deploy.**
8. **GitHub Actions → Refresh FIE Current Season**, same league, governance `AUTO`.
9. **Wait for current/governance commit to deploy.**
10. **Open Lab → M6 Production and verify every relevant governance check.**
11. **Load the target Sleeper league and inspect player decisions.**
12. **Leave scheduled current refresh enabled.**

---

# 24. Exact Cloudflare values for your current repository layout

If the repository root looks like Section 2, enter:

```text
Production branch: main
Root directory:    [leave empty]
Build command:     exit 0
Build output:      .
```

The dot means **the repository/project root itself**. No spaces are required.

Do not enter words such as `repository root` into the Root directory field.

---

# 25. Files you should normally edit vs not edit

## Normal operator-controlled file

`data/research/governance/operator_override.json`

Normally do not edit this manually; use the supplied current-season workflow's AUTO/CONTROL input so the change is timestamped and committed consistently.

## Generated files — do not hand-edit

- `data/research/milestone1.json` through `milestone6.json`
- `data/research/current/milestone5_current.json`
- `data/research/governance/active_release.json`
- immutable Sleeper market snapshots

These should be produced by the pipelines.

## Code changes

- `index.html`
- `/research/*.py`
- `/functions/**`
- workflow YAML

Changes here should go through a normal branch/preview/review cycle.

---

# 26. Long-term maintenance

### During season
- Keep scheduled current workflow enabled.
- Check M6 Production if recommendations suddenly revert to legacy; the reason should be explicit.
- Do not weaken freshness/coverage guards merely to make more players activate.

### End of season
- Add the completed season to historical research.
- Run the full M1–M6 workflow.
- Re-evaluate feature graduation, M4 models, M5 decision policies and FIE/Sleeper blending.

### Before next season
- Confirm GitHub scheduled workflow remains enabled.
- Confirm Cloudflare Git connection still works.
- Run health endpoint.
- Run full historical workflow after all prior-season data are available.
- Run a manual current snapshot once the new season/preseason source feeds exist.

---

# 27. Final production principle

The intended behavior is:

```text
New data
  ↓
Historical validation
  ↓
Position-specific gate
  ↓
Decision-specific gate
  ↓
Fresh current snapshot
  ↓
Matching league scoring
  ↓
AUTO governance
  ↓
M5/M6 override allowed
```

If any arrow breaks:

```text
→ V8.2.2 fallback
```

That fail-closed behavior is intentional and should be preserved in future versions.

---

# Current official references used to verify this guide

- Cloudflare Pages, Git integration: https://developers.cloudflare.com/pages/configuration/git-integration/
- Cloudflare Pages, Static HTML deployment: https://developers.cloudflare.com/pages/framework-guides/deploy-anything/
- Cloudflare Pages Functions, Get started: https://developers.cloudflare.com/pages/functions/get-started/
- Cloudflare Pages rollbacks: https://developers.cloudflare.com/pages/configuration/rollbacks/
- GitHub Actions schedule event: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- GitHub Actions `GITHUB_TOKEN`: https://docs.github.com/en/actions/concepts/security/github_token
- GitHub Actions repository settings: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
