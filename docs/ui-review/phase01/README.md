# Phase 1 review evidence

Compare the `baseline` and `candidate` first-screen PNGs at 1440px and 375px.
`comparison.json` records the frozen baseline commit and measurements. Both runs
block external provider requests identically. These images verify the offline
shell and disclosure behavior; they do not validate live league data or forecasts.

Open `disclosure-preview.html` for a standalone interactive review of the actual
shared component implementation. It embeds the candidate component CSS/JS and the
explicitly fictional fixture page. It is a generated review artifact, not a second
application renderer or a data source. The canonical files are in `app/ui/`.

Browser checks passed for all eight preserved sections, visible league selector
and scoring health, setup and coverage disclosure reachability, desktop and mobile
navigation, Back/Forward, reload deep links, one-row expansion, direct Advanced,
Escape/focus restoration, visible waiver blockers and no page-level horizontal
overflow. No new uncaught browser errors appeared relative to the frozen baseline.

The candidate deliberately retains existing specialized content. Weekly results,
Draft lifecycle views, actual waiver evidence binding and the overarching document
library are subsequent tab phases, requiring separate user review.

## Reproduce

Run the personal release build first: `python tools/release_build.py --mode personal`.
For a configured Playwright installation with Chromium:

```sh
node research/editorial_browser_qa.js /path/to/frozen-baseline/dist dist
```

Use `FIE_UI_PLAYWRIGHT` to supply the Playwright module path and `FIE_UI_QA_OUTPUT`
for output location. The read-only `validate-fie-editorial-ui.yml` workflow installs
its own pinned browser dependency and retains the comparison as a CI artifact.

## Publication blocker

The local candidate is committed on `ui/editorial-p01-shell`. Repository ownership
and administrator access were verified through the connected GitHub account.
Shell Git credentials are absent; the connector's Git-tree write returned HTTP 403,
`Resource not accessible by integration`. Consequently no remote review branch,
draft PR or hosted candidate was created. Main and production were not changed.
