# FIE Chopped + Best Ball Support — 2026-08-31

## Purpose

One-time fail-closed migration that:

- adds `CHOPPED_BESTBALL` as a sixth canonical format;
- resolves Sleeper `settings.type == 3` + `best_ball` to the hybrid;
- composes existing Chopped downside and Best Ball spike evidence by intersection;
- upgrades newly built M5 bundles to contract revision 5 while preserving revision 1-4 validation;
- adds three new managed leagues:
  - `1399128582088835072` → `REDRAFT`
  - `1399318410818519040` → `CHOPPED_BESTBALL`
  - `1396507356048658438` → `CHOPPED`
- adds hybrid browser draft utility using VOR + lower-tail surplus + spike surplus;
- updates workflow choices and deterministic integrity tests.

## Installation

Upload these two files at their exact repository paths:

- `tools/apply_chopped_bestball_support.py`
- `.github/workflows/apply-fie-chopped-bestball-support.yml`

Commit them to `main`, then run:

**Actions → Apply FIE Chopped + Best Ball Support → Run workflow**

The workflow runs integrity tests, commits the actual migration atomically, and removes the two one-time helper files from the repository.

## After migration succeeds

Use the existing onboarding/research flow for the three new leagues. `AUTO` is preferred. The hybrid league must resolve to `CHOPPED_BESTBALL`.

Do not introduce an independent hybrid projection model. The hybrid is deliberately a fail-closed policy composition of the existing evidence streams.
