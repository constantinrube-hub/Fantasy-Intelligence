# Tranche 2B — Responsive Decision / Action Correctness

## Scope

This tranche combines C10-002 with closure of the now-historical Tranche-1 auto-trigger. It changes presentation behavior only. No football model, scoring, projection, replacement, ADP, research-promotion or statistical threshold is changed.

## Responsive correction

The former responsive implementation hid every table column from ordinal 9 onward at <=1150px and from ordinal 7 onward at <=760px. That could remove the actual Decision or Action from Start/Sit, Waivers, D/ST and Kicker surfaces.

Tranche 2B removes those global ordinal rules. Tables remain horizontally accessible, but primary outputs receive semantic persistence:

- Start/Sit Decision is pinned and never hidden.
- Waiver Action is pinned; FAAB remains adjacent and visible.
- Any renderTable surface with an Action key inherits the same primary-action protection.
- D/ST and Kicker main-board actions are pinned.
- D/ST and Kicker Week 1–18 drawer actions are pinned.
- Lower-priority context columns are selectively collapsed at tablet/mobile widths instead of hiding by raw ordinal globally.

## Tranche-1 workflow closure

The Tranche-1 characterization workflow is retained for recoverability but no longer runs on every later tranche. It is workflow_dispatch-only and checks out the frozen validated Tranche-1 commit `309aebf047ee2f250d8a7612aedb0bf6ff5c4455`. This prevents expected later implementation changes from producing misleading red baseline checks.

## Validation

The 2B workflow must preserve Tranche 2A six-format target behavior, pass the responsive target contract, keep unrelated Tranche-1 gaps frozen, and retain `DEPLOYABLE_SOURCE`.

Because `config/build-manifest.json` is deterministic and includes the CSS hash, the first target run is allowed to regenerate exactly two manifest files and uploads them as a sync artifact. No other source or dist drift is allowed. After those two generated manifests are committed, rerunning 2B must finish with a completely clean generated tree.
