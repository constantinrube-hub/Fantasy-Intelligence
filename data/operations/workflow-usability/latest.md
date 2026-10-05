# FIE automatic workflow usability — rolling 14 days

Generated: `2026-10-05T17:06:50.977280+00:00`

Runs: **273**; usable: **12**; investigate: **251**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 12 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 10 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 0 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 187 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 1 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 63 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 52 | 4 | 0 | 0 | 17 | 0 | 31 | 48 |
| Build FIE Window 1C Weekly Actions | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 6 |
| Build FIE Window 1D Optimal Waiver | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 4 |
| Build FIE Window 2A Trench Evidence | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 2 |
| Capture Daily FIE Availability Evidence | 14 | 1 | 0 | 0 | 13 | 0 | 0 | 13 |
| Capture FIE M10 Prospective Research Evidence | 61 | 0 | 5 | 0 | 40 | 0 | 16 | 56 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 49 | 3 | 0 | 0 | 46 | 0 | 0 | 46 |
| Capture FIE PR2 Weekly Lineup Evidence | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 9 | 0 | 0 | 0 | 9 | 0 | 0 | 9 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| Capture FIE Waiver Evidence | 28 | 1 | 0 | 0 | 20 | 0 | 7 | 27 |
| Capture FIE Pregame Weather Evidence | 42 | 3 | 0 | 0 | 30 | 0 | 9 | 39 |
| Evaluate FIE PR2 Weekly Lineup Capture | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
| 2026-10-04T15:31:46Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#37213343310](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37213343310) |
| 2026-10-04T12:51:09Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37203537071](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37203537071) |
| 2026-10-04T12:50:42Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37203513700](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37203513700) |
| 2026-10-04T12:44:58Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37203175989](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37203175989) |
| 2026-10-04T12:30:24Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37202336329](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37202336329) |
| 2026-10-04T11:55:09Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37200338991](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37200338991) |
| 2026-10-04T11:07:11Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37197638713](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37197638713) |
| 2026-10-04T06:20:50Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37182538171](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37182538171) |
| 2026-10-04T06:20:01Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37182494225](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37182494225) |
| 2026-10-04T04:48:26Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37178058208](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37178058208) |
| 2026-10-04T02:39:38Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37171735395](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37171735395) |
| 2026-10-03T23:34:01Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37162186242](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37162186242) |
| 2026-10-03T21:45:34Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37156211064](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37156211064) |
| 2026-10-03T21:44:52Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37156177116](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37156177116) |
| 2026-10-03T20:42:48Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37152523976](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37152523976) |
| 2026-10-03T19:50:36Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37149356070](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37149356070) |
| 2026-10-03T16:41:32Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37137782296](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37137782296) |
| 2026-10-03T16:41:06Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37137755457](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37137755457) |
| 2026-10-03T15:08:01Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37132156982](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37132156982) |
| 2026-10-03T14:04:51Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37128384211](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37128384211) |
| 2026-10-03T13:36:28Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37126753426](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37126753426) |
| 2026-10-03T11:59:26Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37121402537](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37121402537) |
| 2026-10-03T11:58:57Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37121376852](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37121376852) |
| 2026-10-03T10:23:14Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37116247746](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37116247746) |
| 2026-10-03T08:42:19Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37110591104](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37110591104) |
| 2026-10-03T05:42:51Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37100706347](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37100706347) |
| 2026-10-03T05:41:53Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37100654195](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37100654195) |
| 2026-10-03T02:52:33Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37091311413](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37091311413) |
| 2026-10-03T01:55:04Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37087901475](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37087901475) |
| 2026-10-02T22:31:59Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37072991020](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37072991020) |
| 2026-10-02T22:31:23Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37072939689](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37072939689) |
| 2026-10-02T21:34:05Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#37067598866](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37067598866) |
| 2026-10-02T21:18:29Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37066041449](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37066041449) |
| 2026-10-02T17:01:08Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#37037858041](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37037858041) |
| 2026-10-02T16:37:00Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37035136477](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37035136477) |
| 2026-10-02T14:52:52Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37022983530](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37022983530) |
| 2026-10-02T13:08:04Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37010987272](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37010987272) |
| 2026-10-02T13:07:01Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#37010872337](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37010872337) |
| 2026-10-02T11:04:54Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36999028393](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36999028393) |
| 2026-10-02T09:08:57Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36988108710](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36988108710) |
| 2026-10-02T06:09:05Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36972182190](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36972182190) |
| 2026-10-02T06:07:48Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36972085197](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36972085197) |
| 2026-10-02T02:12:22Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36954537925](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36954537925) |
| 2026-10-02T00:19:16Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36945391045](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36945391045) |
| 2026-10-01T23:52:16Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36943077816](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36943077816) |
| 2026-10-01T22:53:28Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36937727429](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36937727429) |
| 2026-10-01T22:52:59Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36937680731](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36937680731) |
| 2026-10-01T21:47:50Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36931022228](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36931022228) |
| 2026-10-01T19:58:01Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36918132555](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36918132555) |
| 2026-10-01T19:30:45Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36914824783](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36914824783) |
| 2026-10-01T15:34:18Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36885299314](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36885299314) |
| 2026-10-01T13:51:41Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36871845914](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36871845914) |
| 2026-10-01T13:50:57Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36871755177](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36871755177) |
| 2026-10-01T13:07:59Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36866453768](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36866453768) |
| 2026-10-01T12:02:21Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36859150863](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36859150863) |
| 2026-10-01T11:35:32Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36856327153](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36856327153) |
| 2026-10-01T06:30:26Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36825136233](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36825136233) |
| 2026-10-01T06:29:28Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36825046114](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36825046114) |
| 2026-10-01T05:47:29Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36821479661](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36821479661) |
| 2026-10-01T03:03:27Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36808730536](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36808730536) |
| 2026-10-01T02:07:05Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36804303384](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36804303384) |
| 2026-09-30T23:46:13Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36792792269](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36792792269) |
| 2026-09-30T22:35:29Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36786449672](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36786449672) |
| 2026-09-30T22:34:13Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36786327062](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36786327062) |
| 2026-09-30T21:39:06Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36780783311](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36780783311) |
| 2026-09-30T21:24:45Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36779252278](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36779252278) |
| 2026-09-30T19:16:42Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36764542550](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36764542550) |
| 2026-09-30T17:12:55Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36749789947](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36749789947) |
| 2026-09-30T16:49:07Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36746969861](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36746969861) |
| 2026-09-30T16:48:26Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36746888314](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36746888314) |
| 2026-09-30T15:05:46Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36734104226](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36734104226) |
| 2026-09-30T12:58:40Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36718345485](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36718345485) |
| 2026-09-30T12:58:15Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36718296653](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36718296653) |
| 2026-09-30T12:32:08Z | Build FIE Window 1D Optimal Waiver | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36715359764](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36715359764) |
| 2026-09-30T12:30:23Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36715161633](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36715161633) |
| 2026-09-30T12:26:37Z | Build FIE Window 1C Weekly Actions | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36714752016](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36714752016) |
| 2026-09-30T11:21:46Z | Build FIE Window 2A Trench Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36708070111](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36708070111) |
| 2026-09-30T11:08:47Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36706720819](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36706720819) |
| 2026-09-30T09:16:12Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36695032754](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36695032754) |
| 2026-09-30T05:56:38Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36675755581](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36675755581) |
| 2026-09-30T05:55:47Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36675688026](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36675688026) |
| 2026-09-30T05:28:46Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36673586797](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36673586797) |
| 2026-09-30T02:57:19Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36662198205](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36662198205) |
| 2026-09-30T02:05:13Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36658181834](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36658181834) |
| 2026-09-29T23:41:09Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36646509190](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36646509190) |
| 2026-09-29T22:34:44Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36640393171](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36640393171) |
| 2026-09-29T22:19:34Z | Build FIE Window 1D Optimal Waiver | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36638890556](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36638890556) |
| 2026-09-29T21:38:20Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36634602131](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36634602131) |
| 2026-09-29T21:23:11Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36632910995](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36632910995) |
| 2026-09-29T19:24:07Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36618974389](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36618974389) |
| 2026-09-29T18:18:04Z | Build FIE Window 1C Weekly Actions | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36611075570](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36611075570) |
| 2026-09-29T17:14:52Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36603580644](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36603580644) |
| 2026-09-29T16:53:23Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36600992918](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36600992918) |
| 2026-09-29T14:56:49Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36586399914](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36586399914) |
| 2026-09-29T13:17:54Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36574055240](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36574055240) |
| 2026-09-29T12:48:18Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36570581801](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36570581801) |
| 2026-09-29T12:40:17Z | Build FIE Window 1C Weekly Actions | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36569666697](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36569666697) |
| 2026-09-29T11:20:42Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36561150558](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36561150558) |
| 2026-09-29T09:15:24Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36547980239](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36547980239) |
| 2026-09-29T06:09:50Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36529665902](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36529665902) |
| 2026-09-29T05:40:38Z | Capture FIE Waiver Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36527288820](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36527288820) |
| 2026-09-29T02:33:48Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36513188677](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36513188677) |
| 2026-09-29T00:43:53Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36504510681](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36504510681) |
| 2026-09-28T23:29:15Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36498251919](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36498251919) |
| 2026-09-28T23:28:39Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36498206001](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36498206001) |
| 2026-09-28T22:31:26Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36492896207](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36492896207) |
| 2026-09-28T18:56:10Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36468698222](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36468698222) |
| 2026-09-28T18:35:47Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36466303277](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36466303277) |
| 2026-09-28T16:52:35Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36454166602](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36454166602) |
| 2026-09-28T14:26:04Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36435932246](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36435932246) |
| 2026-09-28T14:25:09Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36435813350](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36435813350) |
| 2026-09-28T11:39:25Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36416949646](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36416949646) |
| 2026-09-28T09:06:10Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36401365337](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36401365337) |
| 2026-09-28T05:48:57Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36383539202](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36383539202) |
| 2026-09-28T05:48:10Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36383484061](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36383484061) |
| 2026-09-28T02:32:03Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36370183082](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36370183082) |
| 2026-09-28T01:37:42Z | Refresh FIE Current Season | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36366701605](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36366701605) |
| 2026-09-27T23:28:58Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36358834293](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36358834293) |
| 2026-09-27T21:35:14Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36352270388](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36352270388) |
| 2026-09-27T21:34:27Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36352224585](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36352224585) |
| 2026-09-27T20:07:51Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36346886388](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36346886388) |
| 2026-09-27T18:45:31Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36341830281](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36341830281) |
| 2026-09-27T17:15:48Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36336278760](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36336278760) |
| 2026-09-27T17:15:20Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36336248315](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36336248315) |
| 2026-09-27T15:39:29Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36330363683](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36330363683) |
| 2026-09-27T15:38:27Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36330301548](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36330301548) |
| 2026-09-27T14:24:06Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36325772310](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36325772310) |
| 2026-09-27T14:10:47Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36324975862](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36324975862) |
| 2026-09-27T12:24:55Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36318902554](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36318902554) |
| 2026-09-27T12:24:24Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36318874548](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36318874548) |
| 2026-09-27T10:32:01Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36312838441](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36312838441) |
| 2026-09-27T08:41:54Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36307011593](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36307011593) |
| 2026-09-27T05:41:57Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36297948347](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36297948347) |
| 2026-09-27T05:41:13Z | Capture FIE Pregame Weather Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36297913957](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36297913957) |
| 2026-09-27T02:28:30Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36288614078](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36288614078) |
| 2026-09-27T01:24:18Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36285426520](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36285426520) |
| 2026-09-26T23:14:11Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36278799078](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36278799078) |
| 2026-09-26T21:31:41Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36273240815](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36273240815) |
| 2026-09-26T21:30:46Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36273185844](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36273185844) |
| 2026-09-26T19:49:18Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36267365549](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36267365549) |
| 2026-09-26T18:09:43Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36261558545](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36261558545) |
| 2026-09-26T16:44:07Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36256513857](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36256513857) |
| 2026-09-26T16:44:03Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36256508982](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36256508982) |
| 2026-09-26T14:58:04Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36250293726](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36250293726) |
| 2026-09-26T14:58:03Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36250292346](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36250292346) |
| 2026-09-26T13:28:04Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36245258942](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36245258942) |
| 2026-09-26T13:17:27Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36244671042](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36244671042) |
| 2026-09-26T11:44:33Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36239763133](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36239763133) |
| 2026-09-26T11:43:49Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36239727605](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36239727605) |
| 2026-09-26T09:50:32Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36233988219](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36233988219) |
| 2026-09-26T08:05:55Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36228760258](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36228760258) |
| 2026-09-26T05:25:29Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36220752851](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36220752851) |
| 2026-09-26T05:24:30Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36220704568](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36220704568) |
| 2026-09-26T02:31:03Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36211941415](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36211941415) |
| 2026-09-26T01:30:46Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36208674440](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36208674440) |
| 2026-09-25T23:41:13Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36201972072](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36201972072) |
| 2026-09-25T21:48:44Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36193539027](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36193539027) |
| 2026-09-25T21:48:00Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36193476770](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36193476770) |
| 2026-09-25T20:28:04Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36185936817](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36185936817) |
| 2026-09-25T19:01:26Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36177104189](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36177104189) |
| 2026-09-25T17:31:10Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36167629452](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36167629452) |
| 2026-09-25T17:30:45Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36167583416](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36167583416) |
| 2026-09-25T15:49:08Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36156728599](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36156728599) |
| 2026-09-25T15:48:03Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36156609092](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36156609092) |
| 2026-09-25T14:17:49Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36146523707](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36146523707) |
| 2026-09-25T14:02:56Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36144886511](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36144886511) |
| 2026-09-25T12:10:26Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36133423023](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36133423023) |
| 2026-09-25T12:09:13Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36133307580](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36133307580) |
| 2026-09-25T10:09:53Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36122471252](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36122471252) |
| 2026-09-25T08:19:09Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36112267084](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36112267084) |
| 2026-09-25T05:21:42Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36098235236](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36098235236) |
| 2026-09-25T05:20:21Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36098142642](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36098142642) |
| 2026-09-25T02:27:48Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36086352958](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36086352958) |
| 2026-09-25T01:27:28Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36082092006](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36082092006) |
| 2026-09-25T00:32:20Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36077997555](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36077997555) |
| 2026-09-24T23:40:13Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_CANCELLED, USABILITY_ARTIFACT_UNAVAILABLE | [#36073881195](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36073881195) |
| 2026-09-24T21:45:50Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36063503707](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36063503707) |
| 2026-09-24T21:45:48Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36063499528](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36063499528) |
| 2026-09-24T21:28:46Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36061731342](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36061731342) |
| 2026-09-24T20:28:44Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36055129758](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36055129758) |
| 2026-09-24T18:44:35Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_CANCELLED, USABILITY_ARTIFACT_UNAVAILABLE | [#36043348334](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36043348334) |
| 2026-09-24T17:31:38Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36034922163](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36034922163) |
| 2026-09-24T17:31:10Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36034868960](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36034868960) |
| 2026-09-24T17:07:25Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36032097611](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36032097611) |
| 2026-09-24T15:48:55Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36022929775](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36022929775) |
| 2026-09-24T15:48:17Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#36022851849](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36022851849) |
| 2026-09-24T13:53:49Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_CANCELLED, USABILITY_ARTIFACT_UNAVAILABLE | [#36008856238](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36008856238) |
| 2026-09-24T13:41:19Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#36007377022](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/36007377022) |
| 2026-09-24T12:10:07Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35997356704](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35997356704) |
| 2026-09-24T12:09:22Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35997283107](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35997283107) |
| 2026-09-24T11:41:23Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35994478386](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35994478386) |
| 2026-09-24T09:57:36Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35984395681](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35984395681) |
| 2026-09-24T07:56:25Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | RUN_CANCELLED, USABILITY_ARTIFACT_UNAVAILABLE | [#35972368128](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35972368128) |
| 2026-09-24T05:20:48Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35959530443](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35959530443) |
| 2026-09-24T05:19:37Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35959440586](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35959440586) |
| 2026-09-24T04:45:32Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35957007000](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35957007000) |
| 2026-09-24T02:10:43Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35946135799](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35946135799) |
| 2026-09-24T01:21:47Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35942577575](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35942577575) |
| 2026-09-23T23:19:15Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35932994708](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35932994708) |
| 2026-09-23T22:56:09Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35931006864](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35931006864) |
| 2026-09-23T21:45:13Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35924360032](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35924360032) |
| 2026-09-23T21:44:51Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35924323183](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35924323183) |
| 2026-09-23T20:18:42Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35915078196](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35915078196) |
| 2026-09-23T18:43:38Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35904456460](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35904456460) |
| 2026-09-23T18:23:02Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35902071402](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35902071402) |
| 2026-09-23T17:26:30Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35895611659](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35895611659) |
| 2026-09-23T17:26:00Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35895555876](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35895555876) |
| 2026-09-23T15:26:57Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35881627812](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35881627812) |
| 2026-09-23T15:26:17Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35881548161](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35881548161) |
| 2026-09-23T13:57:13Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35870674768](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35870674768) |
| 2026-09-23T13:46:13Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35869392382](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35869392382) |
| 2026-09-23T13:36:58Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35868304433](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35868304433) |
| 2026-09-23T12:05:27Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35858335176](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35858335176) |
| 2026-09-23T12:04:20Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35858220442](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35858220442) |
| 2026-09-23T11:33:29Z | Build FIE Window 1D Optimal Waiver | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35855228689](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35855228689) |
| 2026-09-23T11:25:40Z | Build FIE Window 1C Weekly Actions | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35854467419](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35854467419) |
| 2026-09-23T10:17:11Z | Build FIE Window 2A Trench Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35847909840](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35847909840) |
| 2026-09-23T09:56:52Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35845906940](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35845906940) |
| 2026-09-23T08:05:31Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35835176973](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35835176973) |
| 2026-09-23T07:43:36Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35833226521](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35833226521) |
| 2026-09-23T05:08:24Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35821177330](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35821177330) |
| 2026-09-23T05:07:39Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35821125859](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35821125859) |
| 2026-09-23T02:22:55Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35810119302](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35810119302) |
| 2026-09-23T01:28:33Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35806430141](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35806430141) |
| 2026-09-23T00:29:28Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35802284843](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35802284843) |
| 2026-09-22T23:22:17Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35797080760](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35797080760) |
| 2026-09-22T21:38:43Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35787871118](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35787871118) |
| 2026-09-22T21:22:52Z | Build FIE Window 1D Optimal Waiver | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35786283321](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35786283321) |
| 2026-09-22T21:15:54Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35785558930](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35785558930) |
| 2026-09-22T20:10:43Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35778564428](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35778564428) |
| 2026-09-22T18:24:25Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35766936029](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35766936029) |
| 2026-09-22T17:19:11Z | Build FIE Window 1C Weekly Actions | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35759896077](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35759896077) |
| 2026-09-22T17:15:12Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35759460733](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35759460733) |
| 2026-09-22T16:54:52Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35757237924](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35757237924) |
| 2026-09-22T15:31:06Z | Capture Daily FIE Sleeper Season Projections / ADP | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35747915663](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35747915663) |
| 2026-09-22T15:30:31Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35747843325](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35747843325) |
| 2026-09-22T13:45:42Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35735631555](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35735631555) |
| 2026-09-22T13:34:05Z | Capture Daily FIE Availability Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35734311874](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35734311874) |
| 2026-09-22T12:01:21Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35724727232](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35724727232) |
| 2026-09-22T11:33:59Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35722154284](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35722154284) |
| 2026-09-22T11:26:07Z | Build FIE Window 1C Weekly Actions | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35721425460](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35721425460) |
| 2026-09-22T09:54:55Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35713063934](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35713063934) |
| 2026-09-22T08:02:56Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35702696379](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35702696379) |
| 2026-09-22T05:20:52Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35690345655](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35690345655) |
| 2026-09-22T04:51:16Z | Capture FIE Waiver Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35688450930](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35688450930) |
| 2026-09-22T02:22:31Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35679225585](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35679225585) |
| 2026-09-22T01:35:30Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35676326150](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35676326150) |
| 2026-09-21T22:11:13Z | Capture Immutable FIE Sleeper Weekly Benchmark | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35661341541](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35661341541) |
| 2026-09-21T22:10:17Z | Capture FIE Pregame Weather Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35661259860](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35661259860) |
| 2026-09-21T21:23:03Z | Capture FIE M10 Prospective Research Evidence | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#35656842149](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35656842149) |
| 2026-09-21T21:02:02Z | Refresh FIE Current Season | INFRASTRUCTURE | RUN_FAILURE, USABILITY_ARTIFACT_UNAVAILABLE | [#35654740451](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/35654740451) |

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
| 2026-10-05T14:37:35Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37326211877](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37326211877) |
| 2026-10-05T13:53:58Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37320370773](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37320370773) |
| 2026-10-05T05:39:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37268733323](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37268733323) |
| 2026-10-05T04:38:42Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37264416224](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37264416224) |
| 2026-10-04T23:55:10Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37245476278](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37245476278) |
| 2026-10-04T21:24:36Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37235973435](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37235973435) |
| 2026-10-04T20:58:55Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37234196928](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37234196928) |
| 2026-10-04T17:14:05Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37219727724](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37219727724) |
| 2026-10-04T16:50:40Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37218262249](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37218262249) |
| 2026-10-04T16:36:20Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37217382296](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37217382296) |

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
