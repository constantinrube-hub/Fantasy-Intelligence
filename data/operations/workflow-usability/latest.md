# FIE automatic workflow usability — rolling 14 days

Generated: `2026-10-14T14:12:30.296477+00:00`

Runs: **317**; usable: **95**; investigate: **105**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 95 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 117 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 15 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 68 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 2 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 20 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 46 | 20 | 0 | 0 | 13 | 0 | 13 | 26 |
| Build FIE Window 1C Weekly Actions | 27 | 0 | 19 | 5 | 3 | 0 | 0 | 8 |
| Build FIE Window 1D Optimal Waiver | 31 | 0 | 17 | 10 | 2 | 0 | 2 | 14 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 15 | 10 | 0 | 0 | 5 | 0 | 0 | 5 |
| Capture FIE M10 Prospective Research Evidence | 49 | 1 | 32 | 0 | 12 | 0 | 4 | 16 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 42 | 19 | 10 | 0 | 13 | 0 | 0 | 13 |
| Capture FIE PR2 Weekly Lineup Evidence | 34 | 1 | 33 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Capture FIE Waiver Evidence | 26 | 18 | 1 | 0 | 6 | 0 | 1 | 7 |
| Capture FIE Pregame Weather Evidence | 37 | 24 | 0 | 0 | 13 | 0 | 0 | 13 |
| Evaluate FIE PR2 Weekly Lineup Capture | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
| 2026-10-14T10:13:13Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38548023568](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38548023568) |
| 2026-10-14T01:54:40Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38498235694](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38498235694) |
| 2026-10-13T21:50:55Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38473622863](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38473622863) |
| 2026-10-13T12:43:03Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38399352230](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38399352230) |
| 2026-10-11T21:53:05Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38178185103](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38178185103) |
| 2026-10-11T21:51:56Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38178108768](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38178108768) |
| 2026-10-11T16:26:25Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#38155466128](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38155466128) |
| 2026-10-09T00:40:55Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37866004683](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37866004683) |
| 2026-10-09T00:39:33Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37865889604](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37865889604) |
| 2026-10-08T23:11:06Z | Build FIE Window 1D Optimal Waiver | INFRASTRUCTURE | JOB_FAILURE | [#37857984751](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37857984751) |
| 2026-10-08T22:04:23Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37851100965](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37851100965) |
| 2026-10-08T13:31:17Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37784994394](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37784994394) |
| 2026-10-08T13:29:59Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37784814632](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37784814632) |
| 2026-10-08T12:56:57Z | Build FIE Window 1D Optimal Waiver | INFRASTRUCTURE | JOB_FAILURE | [#37780567872](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37780567872) |
| 2026-10-08T12:04:37Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37774336604](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37774336604) |
| 2026-10-08T12:02:10Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37774057494](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37774057494) |
| 2026-10-08T08:39:40Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37751307277](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37751307277) |
| 2026-10-08T03:26:11Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37722707913](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37722707913) |
| 2026-10-08T03:24:55Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37722605082](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37722605082) |
| 2026-10-08T01:01:07Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37710771825](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37710771825) |
| 2026-10-08T00:31:00Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37708175810](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37708175810) |
| 2026-10-07T23:57:52Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37705178993](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37705178993) |
| 2026-10-07T23:08:28Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37700507721](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37700507721) |
| 2026-10-07T23:07:11Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#37700388476](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37700388476) |
| 2026-10-07T21:58:35Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37693100533](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37693100533) |
| 2026-10-07T13:20:17Z | Build FIE Window 1D Optimal Waiver | BLOCKED | OPERATIONAL_READINESS_BLOCKED | [#37627690200](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37627690200) |
| 2026-10-07T13:11:46Z | Build FIE Window 1C Weekly Actions | BLOCKED | OPERATIONAL_READINESS_BLOCKED | [#37626600180](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37626600180) |
| 2026-10-07T11:47:32Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37616488606](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37616488606) |
| 2026-10-07T02:23:41Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37561768981](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37561768981) |
| 2026-10-06T22:40:21Z | Build FIE Window 1D Optimal Waiver | BLOCKED | OPERATIONAL_READINESS_BLOCKED | [#37542053857](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37542053857) |
| 2026-10-06T21:37:37Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37535207391](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37535207391) |
| 2026-10-06T18:37:19Z | Build FIE Window 1C Weekly Actions | BLOCKED | OPERATIONAL_READINESS_BLOCKED | [#37512719057](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37512719057) |
| 2026-10-06T13:12:16Z | Build FIE Window 1C Weekly Actions | BLOCKED | OPERATIONAL_READINESS_BLOCKED | [#37468955630](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37468955630) |
| 2026-10-06T12:02:06Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#37460408800](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37460408800) |
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

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
| 2026-10-14T12:21:56Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38563242290](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38563242290) |
| 2026-10-14T12:21:28Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#38563184478](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38563184478) |
| 2026-10-14T11:51:30Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38559541890](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38559541890) |
| 2026-10-14T11:22:04Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38556061492](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38556061492) |
| 2026-10-14T11:21:16Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38555972192](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38555972192) |
| 2026-10-14T08:28:37Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38535368357](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38535368357) |
| 2026-10-14T05:22:49Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38516312801](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38516312801) |
| 2026-10-14T04:52:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38513688003](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38513688003) |
| 2026-10-14T02:28:18Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38501188581](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38501188581) |
| 2026-10-14T02:27:17Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38501099575](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38501099575) |
| 2026-10-14T00:10:54Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38488668528](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38488668528) |
| 2026-10-13T23:07:07Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38482236981](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38482236981) |
| 2026-10-13T22:44:24Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38479778526](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38479778526) |
| 2026-10-13T22:34:52Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38478735087](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38478735087) |
| 2026-10-13T22:34:08Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38478658077](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38478658077) |
| 2026-10-13T21:32:16Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#38471357728](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38471357728) |
| 2026-10-13T20:32:16Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38463599811](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38463599811) |
| 2026-10-13T16:56:42Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38434624811](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38434624811) |
| 2026-10-13T14:33:59Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38414452761](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38414452761) |
| 2026-10-13T13:53:03Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38408629676](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38408629676) |
| 2026-10-13T13:52:13Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38408515150](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38408515150) |
| 2026-10-13T13:45:29Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38407576650](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38407576650) |
| 2026-10-13T06:46:45Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38358650348](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38358650348) |
| 2026-10-13T05:54:37Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38353828061](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38353828061) |
| 2026-10-13T00:13:47Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38326197149](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38326197149) |
| 2026-10-13T00:12:30Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38326093395](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38326093395) |
| 2026-10-12T21:16:00Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38309540850](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38309540850) |
| 2026-10-12T21:01:18Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38307978343](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38307978343) |
| 2026-10-12T13:54:14Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38258986466](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38258986466) |
| 2026-10-12T13:52:50Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38258818054](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38258818054) |
| 2026-10-12T10:48:31Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38238631797](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38238631797) |
| 2026-10-12T10:23:50Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38236059878](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38236059878) |
| 2026-10-12T03:30:40Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38200031355](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38200031355) |
| 2026-10-12T03:29:27Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38199943359](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38199943359) |
| 2026-10-12T00:32:03Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38188370048](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38188370048) |
| 2026-10-12T00:16:23Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38187369250](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38187369250) |
| 2026-10-11T22:24:13Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38180280565](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38180280565) |
| 2026-10-11T22:23:07Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38180209084](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38180209084) |
| 2026-10-11T19:33:27Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38168525921](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38168525921) |
| 2026-10-11T19:22:58Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38167774874](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38167774874) |
| 2026-10-11T17:52:19Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38161443045](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38161443045) |
| 2026-10-11T12:49:22Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38140731913](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38140731913) |
| 2026-10-11T12:30:40Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38139531977](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38139531977) |
| 2026-10-11T12:29:40Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38139459677](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38139459677) |
| 2026-10-11T12:17:21Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38138694357](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38138694357) |
| 2026-10-11T05:45:53Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38115844079](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38115844079) |
| 2026-10-11T04:37:09Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38112156836](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38112156836) |
| 2026-10-11T02:59:25Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38106924400](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38106924400) |
| 2026-10-11T02:58:08Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38106856037](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38106856037) |
| 2026-10-10T21:43:48Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38088733204](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38088733204) |
| 2026-10-10T21:17:10Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38087028330](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38087028330) |
| 2026-10-10T21:16:41Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38086996048](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38086996048) |
| 2026-10-10T21:15:34Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38086924546](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38086924546) |
| 2026-10-10T17:20:43Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38071350375](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38071350375) |
| 2026-10-10T17:04:39Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38070256844](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38070256844) |
| 2026-10-10T16:57:32Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38069764325](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38069764325) |
| 2026-10-10T16:56:19Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38069683684](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38069683684) |
| 2026-10-10T12:17:19Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38051409408](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38051409408) |
| 2026-10-10T12:16:12Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38051342980](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38051342980) |
| 2026-10-10T09:50:03Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38042782582](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38042782582) |
| 2026-10-10T09:32:29Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38041752018](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38041752018) |
| 2026-10-10T03:28:04Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38020653533](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38020653533) |
| 2026-10-10T03:26:41Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38020572548](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38020572548) |
| 2026-10-10T00:50:33Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38010767858](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38010767858) |
| 2026-10-10T00:31:52Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38009449768](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38009449768) |
| 2026-10-09T22:26:10Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#37999197313](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37999197313) |
| 2026-10-09T22:24:58Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#37999085993](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37999085993) |
| 2026-10-09T18:21:05Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37972661230](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37972661230) |
| 2026-10-09T18:05:27Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37970851557](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37970851557) |
| 2026-10-09T13:26:01Z | Capture FIE Waiver Evidence | POLICY_NOT_DUE | [#37936799729](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37936799729) |
| 2026-10-09T13:00:25Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#37933810633](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37933810633) |
| 2026-10-09T12:59:13Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#37933670775](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37933670775) |
| 2026-10-09T10:32:56Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37918276732](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37918276732) |
| 2026-10-09T10:11:11Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37916032762](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37916032762) |
| 2026-10-09T04:02:11Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#37882001919](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37882001919) |
| 2026-10-09T04:00:57Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#37881904824](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37881904824) |
| 2026-10-09T01:13:14Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37868702667](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37868702667) |
| 2026-10-09T01:01:34Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37867723128](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37867723128) |
| 2026-10-08T23:10:21Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#37857913412](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37857913412) |
| 2026-10-08T18:34:34Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37825350411](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37825350411) |
| 2026-10-08T14:00:33Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#37788931631](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37788931631) |
| 2026-10-08T12:56:16Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#37780482794](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37780482794) |
| 2026-10-08T10:34:17Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37764339434](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37764339434) |
| 2026-10-08T01:00:05Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37710668135](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37710668135) |
| 2026-10-08T00:45:53Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37709456535](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37709456535) |
| 2026-10-07T23:18:29Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#37701512613](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37701512613) |
| 2026-10-07T20:37:16Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37683396954](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37683396954) |
| 2026-10-07T18:35:43Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37668030000](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37668030000) |
| 2026-10-07T13:54:41Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#37632300727](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37632300727) |
| 2026-10-07T13:54:19Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#37632251096](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37632251096) |
| 2026-10-07T13:22:45Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37628009453](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37628009453) |
| 2026-10-07T09:57:30Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37604141263](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37604141263) |
| 2026-10-07T06:27:02Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#37581556299](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37581556299) |
| 2026-10-07T05:58:50Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37579031445](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37579031445) |
| 2026-10-07T00:25:16Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37551867476](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37551867476) |
| 2026-10-06T22:47:34Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#37542797757](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37542797757) |
| 2026-10-06T22:39:18Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37541943641](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37541943641) |
| 2026-10-06T21:13:13Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#37532295048](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37532295048) |
| 2026-10-06T20:01:21Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37523277480](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37523277480) |
| 2026-10-06T18:36:28Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#37512610991](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37512610991) |
| 2026-10-06T15:57:01Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37491768990](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37491768990) |
| 2026-10-06T12:56:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37466972280](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37466972280) |
| 2026-10-06T06:50:49Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#37426064665](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37426064665) |
| 2026-10-06T06:20:00Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37423138989](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37423138989) |
| 2026-10-06T05:22:52Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37418238852](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37418238852) |
| 2026-10-05T22:00:53Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#37379689590](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37379689590) |
| 2026-10-05T21:51:59Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#37378706225](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/37378706225) |
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
