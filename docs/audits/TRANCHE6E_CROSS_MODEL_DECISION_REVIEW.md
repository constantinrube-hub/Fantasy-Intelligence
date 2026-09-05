# Tranche 6E — Cross-Model and Decision Review

## Decision

Retain M9 as champion. No M10 position or horizon is approved for Tranche 6F shadow integration, app integration, promotion review, or production activation.

QB M10-HGB is preserved as a promising research lead, not an approved model. In the deterministic 6D fixture it beat M9 MAE in all four held-out seasons, averaged a 4.41% relative MAE lift, and produced an exhaustive four-season bootstrap interval whose lower bound remained positive. That isolated point-forecast signal is insufficient to satisfy the complete promotion gate.

## Paired evidence review

| Position | Candidate | Weighted MAE | Mean fold lift vs M9 | Fold wins | 95% outer-season bootstrap interval | Point gate |
|---|---:|---:|---:|---:|---:|---|
| QB | M10 Linear | 5.370 | -0.56% | 1/4 | -1.70% to 0.72% | Fail |
| QB | M10 HGB | 5.103 | 4.41% | 4/4 | 1.73% to 8.08% | Pass, research lead only |
| RB | M10 Linear | 2.929 | 2.63% | 2/4 | -1.33% to 9.00% | Fail |
| RB | M10 HGB | 3.051 | -1.65% | 1/4 | -8.92% to 6.76% | Fail |
| WR | M10 Linear | 2.717 | -0.65% | 1/4 | -1.04% to -0.13% | Fail |
| WR | M10 HGB | 2.727 | -0.90% | 2/4 | -3.13% to 1.32% | Fail |
| TE | M10 Linear | 3.087 | 1.60% | 3/4 | -1.59% to 4.56% | Fail |
| TE | M10 HGB | 3.115 | 0.98% | 3/4 | -5.10% to 5.27% | Fail |

The review preserves the 6D paired fold metrics, including bias, Spearman rank correlation, pinball loss, and P10–P90 coverage/width. It does not reinterpret a point-gate pass as a promotion decision.

## Why promotion and shadow approval remain blocked

The validated evidence is a deterministic synthetic fixture. Its `scoring_signature` is null and it does not replay all applicable profiles across the 22 enabled leagues and six formats. The aggregate artifact does not retain row-level paired predictions, so player-level disagreement, top-k overlap, calibration bands, and decision regret cannot be reconstructed honestly.

Only position and outer season are available as subgroups. Week range, team change, rookie/young-player status, participation band, scoring format, and league capability are absent. There are no legal-lineup, start/sit, draft, trade, or waiver decision traces. Consequently the review records `MISSING_SOURCE`, `INSUFFICIENT_HISTORY`, `CALIBRATION_FAILURE`, `DECISION_UTILITY_FAILURE`, and `GOVERNANCE_BLOCKED`.

## Required next evidence

Further M10 consideration requires real point-in-time paired row-level predictions, row-level model-disagreement analysis, material-subgroup and probability-band calibration, all-applicable scoring-profile replay, and downstream decision-utility traces. Prospective evidence collection must continue without historical reconstruction from current endpoints.

No ensemble is authorized. No 6F shadow namespace may be created from this result. M9 remains the production authority.

## Controlled validation lifecycle

The target validated successfully at `b248c7387f5ae3c9aa7b7c64ee0076f85cc96924` in GitHub Actions run `33951332941` (1m 37s, `DEPLOYABLE_SOURCE`). Its release artifact SHA-256 is `ce9f3c819fc7144768c0b6a2b4930f1ef06d899170e2a2495ab3fa837a819b56`; the verified generated synchronization is limited to `config/build-manifest.json`, `config/release-gate.json`, and `dist/config/build-manifest.json`.

The reviewer has returned to the repository-wide manual-only historical-validation policy. No new controlled audit target is authorized unless material new prospective evidence changes the 6E blockers.
