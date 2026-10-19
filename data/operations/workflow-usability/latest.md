# FIE automatic workflow usability — rolling 14 days

Generated: `2026-10-19T15:38:05.050262+00:00`

Runs: **393**; usable: **152**; investigate: **50**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 152 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 191 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 26 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 5 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 2 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 17 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 47 | 31 | 0 | 1 | 0 | 0 | 15 | 16 |
| Build FIE Window 1C Weekly Actions | 49 | 0 | 36 | 10 | 3 | 0 | 0 | 13 |
| Build FIE Window 1D Optimal Waiver | 53 | 0 | 34 | 15 | 2 | 0 | 2 | 19 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE M10 Prospective Research Evidence | 52 | 2 | 50 | 0 | 0 | 0 | 0 | 0 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 46 | 33 | 13 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE PR2 Weekly Lineup Evidence | 53 | 2 | 51 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Capture FIE Waiver Evidence | 28 | 27 | 1 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Pregame Weather Evidence | 41 | 41 | 0 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE PR2 Weekly Lineup Capture | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
| 2026-10-18T14:11:14Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#39134856163](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39134856163) |
| 2026-10-17T18:20:05Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39057627268](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39057627268) |
| 2026-10-17T18:17:40Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39057456438](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39057456438) |
| 2026-10-17T09:21:52Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#39020837925](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39020837925) |
| 2026-10-17T01:19:38Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38990370248](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38990370248) |
| 2026-10-16T19:57:30Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38958709050](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38958709050) |
| 2026-10-16T15:22:37Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#38923420308](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38923420308) |
| 2026-10-15T09:55:04Z | Refresh FIE Current Season | PARTIAL | CURRENT_REFRESH_PORTFOLIO_INCOMPLETE | [#38716469791](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38716469791) |
| 2026-10-15T02:13:53Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38669884451](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38669884451) |
| 2026-10-15T02:12:13Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38669740689](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38669740689) |
| 2026-10-14T21:30:37Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38640812669](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38640812669) |
| 2026-10-14T21:28:38Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38640555765](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38640555765) |
| 2026-10-14T16:44:54Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38600697349](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38600697349) |
| 2026-10-14T16:43:20Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38600478120](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38600478120) |
| 2026-10-14T15:22:19Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38588716978](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38588716978) |
| 2026-10-14T15:20:29Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#38588442719](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38588442719) |
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

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
| 2026-10-19T13:13:58Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39258389769](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39258389769) |
| 2026-10-19T12:27:10Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39252159447](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39252159447) |
| 2026-10-19T11:36:44Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39245891275](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39245891275) |
| 2026-10-19T11:34:40Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39245635285](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39245635285) |
| 2026-10-19T04:39:44Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39200586108](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39200586108) |
| 2026-10-19T03:42:58Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39195994895](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39195994895) |
| 2026-10-19T02:30:54Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39190323189](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39190323189) |
| 2026-10-19T02:28:48Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39190152655](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39190152655) |
| 2026-10-18T23:12:03Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39175501632](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39175501632) |
| 2026-10-18T22:50:20Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39173962823](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39173962823) |
| 2026-10-18T20:42:25Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39164531196](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39164531196) |
| 2026-10-18T20:15:44Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39162496581](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39162496581) |
| 2026-10-18T20:14:34Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39162404559](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39162404559) |
| 2026-10-18T20:13:18Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39162308216](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39162308216) |
| 2026-10-18T16:18:57Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39144434598](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39144434598) |
| 2026-10-18T15:51:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39142398397](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39142398397) |
| 2026-10-18T15:47:15Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39142046925](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39142046925) |
| 2026-10-18T15:45:16Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39141901953](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39141901953) |
| 2026-10-18T15:32:07Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39140918560](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39140918560) |
| 2026-10-18T11:03:58Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39121729010](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39121729010) |
| 2026-10-18T10:50:08Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39120813002](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39120813002) |
| 2026-10-18T10:48:08Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39120682639](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39120682639) |
| 2026-10-18T10:33:26Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39119722361](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39119722361) |
| 2026-10-18T04:33:01Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39097483670](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39097483670) |
| 2026-10-18T03:32:00Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39093959168](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39093959168) |
| 2026-10-18T01:52:10Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39088026290](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39088026290) |
| 2026-10-18T01:49:59Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39087894406](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39087894406) |
| 2026-10-17T23:07:51Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39077809411](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39077809411) |
| 2026-10-17T22:55:31Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39077005989](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39077005989) |
| 2026-10-17T20:36:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39067412274](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39067412274) |
| 2026-10-17T20:16:12Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39065991082](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39065991082) |
| 2026-10-17T20:12:51Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39065755617](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39065755617) |
| 2026-10-17T20:10:54Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39065619966](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39065619966) |
| 2026-10-17T15:34:16Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39045629315](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39045629315) |
| 2026-10-17T15:26:02Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39045018351](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39045018351) |
| 2026-10-17T15:24:02Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39044872593](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39044872593) |
| 2026-10-17T15:09:41Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39043824973](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39043824973) |
| 2026-10-17T10:43:25Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39025982850](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39025982850) |
| 2026-10-17T10:17:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39024341276](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39024341276) |
| 2026-10-17T09:58:53Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39023148404](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39023148404) |
| 2026-10-17T09:57:34Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#39023070734](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39023070734) |
| 2026-10-17T04:24:57Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39002477756](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39002477756) |
| 2026-10-17T03:25:51Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38998747156](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38998747156) |
| 2026-10-17T02:32:25Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38995321035](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38995321035) |
| 2026-10-17T02:31:12Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38995238963](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38995238963) |
| 2026-10-16T23:35:03Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38982200750](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38982200750) |
| 2026-10-16T23:17:31Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38980635544](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38980635544) |
| 2026-10-16T21:10:12Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38967469785](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38967469785) |
| 2026-10-16T21:08:55Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38967319730](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38967319730) |
| 2026-10-16T21:07:30Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38967151466](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38967151466) |
| 2026-10-16T20:37:25Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38963571547](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38963571547) |
| 2026-10-16T16:39:00Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38933606244](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38933606244) |
| 2026-10-16T16:37:00Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38933346233](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38933346233) |
| 2026-10-16T16:35:43Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#38933182865](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38933182865) |
| 2026-10-16T16:15:23Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38930494573](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38930494573) |
| 2026-10-16T11:23:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38893502907](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38893502907) |
| 2026-10-16T10:55:48Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38890443799](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38890443799) |
| 2026-10-16T10:36:22Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38888332234](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38888332234) |
| 2026-10-16T10:34:40Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38888144697](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38888144697) |
| 2026-10-16T04:31:41Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38851081192](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38851081192) |
| 2026-10-16T03:35:54Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38846316157](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38846316157) |
| 2026-10-16T02:09:55Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38839003600](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38839003600) |
| 2026-10-16T02:08:22Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38838873643](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38838873643) |
| 2026-10-15T21:22:21Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38809345358](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38809345358) |
| 2026-10-15T21:09:53Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38807740946](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38807740946) |
| 2026-10-15T21:08:10Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38807522158](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38807522158) |
| 2026-10-15T21:02:15Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38806740570](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38806740570) |
| 2026-10-15T16:48:25Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38772056333](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38772056333) |
| 2026-10-15T16:46:47Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38771837017](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38771837017) |
| 2026-10-15T16:30:03Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38769505133](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38769505133) |
| 2026-10-15T12:06:19Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#38732142564](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38732142564) |
| 2026-10-15T11:28:24Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38727572387](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38727572387) |
| 2026-10-15T10:42:23Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#38722159199](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38722159199) |
| 2026-10-15T10:40:55Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#38721986837](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38721986837) |
| 2026-10-15T05:10:37Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38685370079](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38685370079) |
| 2026-10-15T04:38:21Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38682514204](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38682514204) |
| 2026-10-15T03:39:32Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38677402193](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38677402193) |
| 2026-10-14T23:45:17Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38656000810](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38656000810) |
| 2026-10-14T21:55:48Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38643971211](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38643971211) |
| 2026-10-14T21:40:49Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38642096745](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38642096745) |
| 2026-10-14T19:12:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38621716568](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38621716568) |
| 2026-10-14T17:36:15Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#38608052645](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38608052645) |
| 2026-10-14T17:09:48Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#38604290058](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38604290058) |
| 2026-10-14T14:22:56Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#38580004843](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38580004843) |
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

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
