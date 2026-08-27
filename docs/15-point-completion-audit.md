# FIE 15-Point Completion Audit

Baseline: live GitHub `main`, V9.3.2 browser-QA/ranking-integrity line, audited 2026-08-27.

## Final classification

| # | Item | V9.3.2 audit | Consolidated result |
|---|---|---|---|
| 1 | Native Sleeper Chopped detection (`settings.type == 3`) | Complete | Preserved + regression gate |
| 2 | Position-aware scoring coverage/governance | Complete | Preserved + regression gate |
| 3 | Cross-position QB/TE calibration, avoid correlated double counting | Partial | Completed: explicit scarcity term removed when valid VOR already carries replacement scarcity; scarcity remains fallback if VOR absent |
| 4 | Separate active/selected league IDs + stale async protection | Complete | Preserved + regression gate |
| 5 | Technical diagnostics kept out of primary consumer flow / Lab-oriented | Functionally complete in V9.3.2 consolidation | Preserved + regression gate |
| 6 | Format precedence | Complete | Preserved + regression gate |
| 7 | Marginal roster utility for QB/TE valuation | Complete | Preserved + regression gate |
| 8 | User-facing eligibility/causal explanation rather than raw technical rule text | Complete in V9.3.2 Basic drawer and League Interpretation | Preserved + regression gate |
| 9 | Clickable Draft Player Report | Complete | Preserved + regression gate |
| 10 | Recommendation separated from roster condition | Complete | Preserved + regression gate |
| 11 | Truthful status semantics for loaded vs active/runtime-eligible evidence | Complete at runtime contract level | Preserved + regression gate |
| 12 | Sleeper 3RR via `draft.settings.reversal_round` | Complete | Preserved + regression gate |
| 13 | Web Worker, progressive/cancellable Monte Carlo | Complete | Preserved + regression gate |
| 14 | Value Finder calculation caching | Complete | Preserved + regression gate |
| 15 | Staged league loading / critical-path reduction | Partial before patch | Completed with league core snapshots, persistent cache, two-wide idle prefetch, live non-blocking overlay, last-known-good fallback |

## Calibration rule for item 3

VOR is already a replacement-level measure. The previous canonical Draft Base Value also gave a separate structural scarcity term 7-15% weight depending on format. In leagues where replacement level is unusually low, especially Superflex/QB or scarce TE structures, these signals are correlated and can double reward the same structural fact.

The completion guard therefore applies this rule:

- valid VOR present: remove the explicit scarcity contribution and renormalize the remaining canonical score;
- VOR absent: retain structural scarcity as the fallback;
- exact league roster slots still determine replacement/VOR, so Superflex, 2QB and TE-premium structural differences are retained rather than flattened;
- market ADP remains excluded from canonical player quality.

## Item 15 fast-switch behavior

Normal league navigation becomes:

1. hydrate compact prebuilt league/core state when available;
2. render through the existing loader contract;
3. refresh Sleeper league/roster/user state asynchronously with `no-store`;
4. prefetch other enabled league cores only after initial page load/idle time, max two at once;
5. disable broad prefetch under Save Data, limit it on very slow connections;
6. historical transactions remain lazy/manual;
7. failed scheduled snapshot refresh preserves the last known-good artifact.

The legacy network loader remains the fallback whenever a valid league snapshot is not available.
