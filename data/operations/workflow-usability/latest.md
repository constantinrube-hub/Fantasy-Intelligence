# FIE automatic workflow usability — rolling 14 days

Generated: `2026-10-28T16:02:35.131303+00:00`

Runs: **440**; usable: **175**; investigate: **37**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 175 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 228 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 25 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 0 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 2 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 10 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 53 | 43 | 0 | 1 | 0 | 0 | 9 | 10 |
| Build FIE Window 1C Weekly Actions | 55 | 0 | 43 | 12 | 0 | 0 | 0 | 12 |
| Build FIE Window 1D Optimal Waiver | 55 | 0 | 43 | 12 | 0 | 0 | 0 | 12 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE M10 Prospective Research Evidence | 60 | 2 | 58 | 0 | 0 | 0 | 0 | 0 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 54 | 35 | 18 | 0 | 0 | 0 | 1 | 1 |
| Capture FIE PR2 Weekly Lineup Evidence | 62 | 2 | 60 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Capture FIE Waiver Evidence | 31 | 31 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Pregame Weather Evidence | 46 | 46 | 0 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE PR2 Weekly Lineup Capture | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
| 2026-10-28T11:20:32Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40679195439](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40679195439) |
| 2026-10-28T02:15:28Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40619855587](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40619855587) |
| 2026-10-27T21:19:53Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40585861965](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40585861965) |
| 2026-10-27T16:39:01Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40542987042](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40542987042) |
| 2026-10-27T10:34:32Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40489539871](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40489539871) |
| 2026-10-26T05:16:31Z | Capture Immutable FIE Sleeper Weekly Benchmark | INFRASTRUCTURE | JOB_FAILURE | [#40273335866](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40273335866) |
| 2026-10-25T14:37:35Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#40203113217](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40203113217) |
| 2026-10-22T02:48:32Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39713398043](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39713398043) |
| 2026-10-22T02:46:12Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39713193736](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39713193736) |
| 2026-10-21T21:57:13Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39682841059](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39682841059) |
| 2026-10-21T21:54:23Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39682479593](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39682479593) |
| 2026-10-21T17:13:37Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39641886181](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39641886181) |
| 2026-10-21T17:10:58Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39641489881](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39641489881) |
| 2026-10-21T11:00:35Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39588744602](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39588744602) |
| 2026-10-21T10:58:00Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39588431329](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39588431329) |
| 2026-10-21T02:16:45Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39532121821](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39532121821) |
| 2026-10-21T02:14:01Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39531862691](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39531862691) |
| 2026-10-20T21:31:39Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39501080281](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39501080281) |
| 2026-10-20T21:28:56Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39500705321](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39500705321) |
| 2026-10-20T16:32:43Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39458378054](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39458378054) |
| 2026-10-20T16:30:07Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39457986983](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39457986983) |
| 2026-10-20T10:46:14Z | Build FIE Window 1D Optimal Waiver | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39410273310](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39410273310) |
| 2026-10-20T10:43:49Z | Build FIE Window 1C Weekly Actions | PARTIAL | OPERATIONAL_READINESS_PARTIAL | [#39409990458](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39409990458) |
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

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
| 2026-10-28T14:29:50Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#40706495099](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40706495099) |
| 2026-10-28T13:31:16Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40697172437](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40697172437) |
| 2026-10-28T12:54:11Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40691678073](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40691678073) |
| 2026-10-28T12:18:11Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40686690816](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40686690816) |
| 2026-10-28T12:13:58Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40686120188](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40686120188) |
| 2026-10-28T12:12:19Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40685902222](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40685902222) |
| 2026-10-28T06:16:24Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40642848439](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40642848439) |
| 2026-10-28T05:41:50Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40639487801](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40639487801) |
| 2026-10-28T04:34:42Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40633109665](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40633109665) |
| 2026-10-28T03:30:26Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40627073701](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40627073701) |
| 2026-10-28T03:28:43Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40626904428](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40626904428) |
| 2026-10-27T22:36:41Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40596137656](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40596137656) |
| 2026-10-27T22:14:19Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40593250744](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40593250744) |
| 2026-10-27T22:13:46Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40593176191](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40593176191) |
| 2026-10-27T22:12:37Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40593019610](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40593019610) |
| 2026-10-27T21:54:21Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40590594094](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40590594094) |
| 2026-10-27T21:28:34Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#40587091163](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40587091163) |
| 2026-10-27T18:18:34Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40558755192](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40558755192) |
| 2026-10-27T17:52:15Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40554624251](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40554624251) |
| 2026-10-27T17:42:58Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40553184933](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40553184933) |
| 2026-10-27T15:21:00Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40530079012](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40530079012) |
| 2026-10-27T15:11:04Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40528438686](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40528438686) |
| 2026-10-27T12:39:45Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40505523372](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40505523372) |
| 2026-10-27T11:37:34Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40497548816](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40497548816) |
| 2026-10-27T11:35:31Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40497296473](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40497296473) |
| 2026-10-27T08:59:00Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40477353545](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40477353545) |
| 2026-10-27T08:44:08Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40475578745](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40475578745) |
| 2026-10-27T05:35:13Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40456157852](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40456157852) |
| 2026-10-27T03:01:07Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40441779466](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40441779466) |
| 2026-10-27T02:58:29Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40441517016](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40441517016) |
| 2026-10-27T00:25:26Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40426296907](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40426296907) |
| 2026-10-27T00:15:29Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40425234423](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40425234423) |
| 2026-10-26T20:28:52Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40396006922](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40396006922) |
| 2026-10-26T20:19:58Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40394676378](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40394676378) |
| 2026-10-26T18:44:37Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40380440504](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40380440504) |
| 2026-10-26T18:41:24Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40379955642](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40379955642) |
| 2026-10-26T13:01:30Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40327093876](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40327093876) |
| 2026-10-26T12:26:20Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40322533847](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40322533847) |
| 2026-10-26T12:24:47Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40322332901](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40322332901) |
| 2026-10-26T12:21:56Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40321967932](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40321967932) |
| 2026-10-26T04:46:16Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40270767292](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40270767292) |
| 2026-10-26T03:43:39Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40265482511](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40265482511) |
| 2026-10-26T02:25:23Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40259015152](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40259015152) |
| 2026-10-26T02:22:46Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40258799704](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40258799704) |
| 2026-10-25T23:16:07Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40243976099](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40243976099) |
| 2026-10-25T23:02:47Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40242955616](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40242955616) |
| 2026-10-25T20:52:36Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40232817344](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40232817344) |
| 2026-10-25T20:50:28Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40232651089](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40232651089) |
| 2026-10-25T20:49:51Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40232599004](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40232599004) |
| 2026-10-25T20:30:37Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40231103293](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40231103293) |
| 2026-10-25T16:55:52Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40214022050](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40214022050) |
| 2026-10-25T16:18:09Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40211020374](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40211020374) |
| 2026-10-25T16:11:35Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40210498844](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40210498844) |
| 2026-10-25T16:09:08Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40210303398](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40210303398) |
| 2026-10-25T15:42:45Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40208234316](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40208234316) |
| 2026-10-25T11:28:02Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40188978162](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40188978162) |
| 2026-10-25T10:55:54Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40186774250](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40186774250) |
| 2026-10-25T10:40:04Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40185709885](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40185709885) |
| 2026-10-25T10:37:34Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40185545335](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40185545335) |
| 2026-10-25T04:40:20Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40162732244](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40162732244) |
| 2026-10-25T03:40:25Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40159078032](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40159078032) |
| 2026-10-25T02:23:35Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40154266176](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40154266176) |
| 2026-10-25T02:21:05Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40154113131](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40154113131) |
| 2026-10-24T23:13:52Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40141869824](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40141869824) |
| 2026-10-24T22:57:23Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40140717887](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40140717887) |
| 2026-10-24T20:48:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40131467359](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40131467359) |
| 2026-10-24T20:24:34Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40129644176](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40129644176) |
| 2026-10-24T20:15:30Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40128967020](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40128967020) |
| 2026-10-24T20:13:13Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40128797882](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40128797882) |
| 2026-10-24T15:56:24Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40109246224](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40109246224) |
| 2026-10-24T15:32:57Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40107480687](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40107480687) |
| 2026-10-24T15:10:59Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40105801718](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40105801718) |
| 2026-10-24T15:08:39Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40105623985](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40105623985) |
| 2026-10-24T10:58:57Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40088042862](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40088042862) |
| 2026-10-24T10:49:15Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40087420747](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40087420747) |
| 2026-10-24T10:46:36Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40087251941](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40087251941) |
| 2026-10-24T10:28:39Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40086060740](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40086060740) |
| 2026-10-24T04:35:43Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40062961593](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40062961593) |
| 2026-10-24T03:42:13Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40059382699](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40059382699) |
| 2026-10-24T02:50:02Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40055809287](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40055809287) |
| 2026-10-24T02:47:14Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40055620911](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40055620911) |
| 2026-10-23T21:24:15Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40026507436](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40026507436) |
| 2026-10-23T21:19:24Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40025909298](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40025909298) |
| 2026-10-23T21:16:31Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40025553427](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40025553427) |
| 2026-10-23T21:07:09Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40024391465](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40024391465) |
| 2026-10-23T17:06:16Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39992320097](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39992320097) |
| 2026-10-23T16:42:04Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39988950718](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39988950718) |
| 2026-10-23T16:39:42Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39988626169](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39988626169) |
| 2026-10-23T16:38:56Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39988522839](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39988522839) |
| 2026-10-23T11:38:23Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39947483228](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39947483228) |
| 2026-10-23T11:22:54Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39945668315](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39945668315) |
| 2026-10-23T11:15:57Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39944867847](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39944867847) |
| 2026-10-23T11:10:44Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39944259028](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39944259028) |
| 2026-10-23T04:48:31Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39902294623](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39902294623) |
| 2026-10-23T03:48:04Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39896930906](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39896930906) |
| 2026-10-23T02:45:34Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39891320740](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39891320740) |
| 2026-10-23T02:43:05Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39891089861](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39891089861) |
| 2026-10-22T21:48:08Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39860145754](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39860145754) |
| 2026-10-22T21:45:24Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39859792585](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39859792585) |
| 2026-10-22T21:35:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39858460037](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39858460037) |
| 2026-10-22T21:17:30Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39856038962](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39856038962) |
| 2026-10-22T16:47:44Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39816982085](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39816982085) |
| 2026-10-22T16:47:06Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39816877672](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39816877672) |
| 2026-10-22T16:44:40Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39816506035](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39816506035) |
| 2026-10-22T12:23:22Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#39777929804](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39777929804) |
| 2026-10-22T11:51:44Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39773775461](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39773775461) |
| 2026-10-22T11:30:53Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39771148805](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39771148805) |
| 2026-10-22T11:28:21Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39770826699](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39770826699) |
| 2026-10-22T05:20:40Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39727479053](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39727479053) |
| 2026-10-22T04:44:10Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39724027366](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39724027366) |
| 2026-10-22T03:43:37Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39718423081](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39718423081) |
| 2026-10-21T21:58:13Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39682967744](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39682967744) |
| 2026-10-21T21:42:26Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39680943323](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39680943323) |
| 2026-10-21T21:22:11Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39678217775](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39678217775) |
| 2026-10-21T17:38:51Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39645642572](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39645642572) |
| 2026-10-21T17:11:45Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39641603433](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39641603433) |
| 2026-10-21T16:47:28Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39637934497](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39637934497) |
| 2026-10-21T12:24:01Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39599280420](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39599280420) |
| 2026-10-21T12:23:20Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#39599193707](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39599193707) |
| 2026-10-21T11:48:21Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39594679391](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39594679391) |
| 2026-10-21T11:21:10Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39591308409](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39591308409) |
| 2026-10-21T05:17:51Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39548748705](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39548748705) |
| 2026-10-21T04:45:35Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39545794349](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39545794349) |
| 2026-10-21T03:43:49Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39540169939](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39540169939) |
| 2026-10-20T23:52:09Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39517766255](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39517766255) |
| 2026-10-20T23:39:49Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39516476048](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39516476048) |
| 2026-10-20T21:51:46Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39503750102](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39503750102) |
| 2026-10-20T20:07:43Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#39489329891](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39489329891) |
| 2026-10-20T19:16:42Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39482076080](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39482076080) |
| 2026-10-20T19:00:01Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39479639432](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39479639432) |
| 2026-10-20T17:30:44Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39466720484](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39466720484) |
| 2026-10-20T14:18:20Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39438001636](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39438001636) |
| 2026-10-20T14:09:28Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39436693826](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39436693826) |
| 2026-10-20T12:10:30Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39420267520](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39420267520) |
| 2026-10-20T08:32:03Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39394087085](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39394087085) |
| 2026-10-20T08:15:56Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39392147817](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39392147817) |
| 2026-10-20T05:16:07Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#39373981370](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39373981370) |
| 2026-10-20T02:27:55Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39359047649](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39359047649) |
| 2026-10-20T02:25:38Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39358839462](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39358839462) |
| 2026-10-20T00:19:35Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39346965087](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39346965087) |
| 2026-10-20T00:08:22Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39345843932](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39345843932) |
| 2026-10-19T20:34:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#39320496511](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39320496511) |
| 2026-10-19T20:24:46Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#39319084108](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39319084108) |
| 2026-10-19T18:42:31Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#39304776921](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39304776921) |
| 2026-10-19T18:40:25Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#39304478895](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39304478895) |
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

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
