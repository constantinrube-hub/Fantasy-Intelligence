# FIE automatic workflow usability — rolling 14 days

Generated: `2026-11-12T17:36:48.934275+00:00`

Runs: **369**; usable: **132**; investigate: **18**; known gaps: **49**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 132 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 170 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 51 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 5 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 2 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 9 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 40 | 36 | 0 | 1 | 0 | 0 | 3 | 4 |
| Build FIE Window 1C Weekly Actions | 40 | 0 | 30 | 10 | 0 | 0 | 0 | 0 |
| Build FIE Window 1D Optimal Waiver | 40 | 0 | 30 | 10 | 0 | 0 | 0 | 0 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE M10 Prospective Research Evidence | 45 | 1 | 44 | 0 | 0 | 0 | 0 | 0 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 33 | 25 | 8 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE PR2 Weekly Lineup Evidence | 45 | 1 | 44 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Capture FIE Waiver Evidence | 26 | 23 | 2 | 1 | 0 | 0 | 0 | 1 |
| Capture FIE Pregame Weather Evidence | 29 | 29 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Weekly Research Preparation | 28 | 0 | 0 | 23 | 5 | 0 | 0 | 5 |
| FIE Component Forecast and Weekly Evaluation | 13 | 1 | 6 | 0 | 0 | 0 | 6 | 6 |
| Evaluate FIE PR2 Weekly Lineup Capture | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
| 2026-11-12T13:45:44Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43230388633](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43230388633) |
| 2026-11-12T07:39:44Z | FIE Component Forecast and Weekly Evaluation | INFRASTRUCTURE | JOB_FAILURE | [#43176904489](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43176904489) |
| 2026-11-12T01:38:41Z | FIE Component Forecast and Weekly Evaluation | INFRASTRUCTURE | JOB_FAILURE | [#43135909808](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43135909808) |
| 2026-11-11T23:27:38Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43119979549](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43119979549) |
| 2026-11-11T18:51:04Z | FIE Component Forecast and Weekly Evaluation | INFRASTRUCTURE | JOB_FAILURE | [#43081650182](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43081650182) |
| 2026-11-11T11:24:43Z | FIE Component Forecast and Weekly Evaluation | INFRASTRUCTURE | JOB_FAILURE | [#43011723683](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43011723683) |
| 2026-11-11T02:57:33Z | FIE Component Forecast and Weekly Evaluation | INFRASTRUCTURE | JOB_FAILURE | [#42949500898](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42949500898) |
| 2026-11-10T23:40:25Z | FIE Component Forecast and Weekly Evaluation | INFRASTRUCTURE | JOB_FAILURE | [#42925285278](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42925285278) |
| 2026-11-08T17:17:59Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#42504255762](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42504255762) |
| 2026-11-08T11:56:05Z | Refresh FIE Current Season | PARTIAL | CURRENT_REFRESH_PORTFOLIO_INCOMPLETE | [#42477898449](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42477898449) |
| 2026-11-05T13:12:19Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#42033689823](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42033689823) |
| 2026-11-04T18:39:57Z | Capture FIE Waiver Evidence | PARTIAL | PARTIAL_SOURCE_FAILURE | [#41889380874](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41889380874) |
| 2026-11-01T17:18:22Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#41330790593](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41330790593) |
| 2026-10-31T21:27:51Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#41243700029](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41243700029) |
| 2026-10-31T12:17:41Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#41200451509](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41200451509) |
| 2026-10-30T22:14:34Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#41136797012](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41136797012) |
| 2026-10-30T12:46:30Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#41057890752](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41057890752) |
| 2026-10-29T19:34:41Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40941348700](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40941348700) |

## Known gaps

PARTIAL by design: every reason is declared in `known_gap_reasons` in the monitor config. Counted here, not under investigate. A new reason code moves a run back to the table above.

| Workflow | Known-gap runs | Declared reasons |
|---|---:|---|
| Build FIE Window 1C Weekly Actions | 10 | OPERATIONAL_READINESS_PARTIAL |
| Build FIE Window 1D Optimal Waiver | 10 | OPERATIONAL_READINESS_PARTIAL |
| Capture FIE Weekly Research Preparation | 23 | OPERATIONAL_READINESS_PARTIAL |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 6 | OPERATIONAL_READINESS_PARTIAL |

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
| 2026-11-12T17:24:44Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43269145286](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43269145286) |
| 2026-11-12T16:13:23Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#43256281281](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43256281281) |
| 2026-11-12T15:08:20Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43244533746](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43244533746) |
| 2026-11-12T15:05:13Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43243970798](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43243970798) |
| 2026-11-12T11:07:37Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43206419466](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43206419466) |
| 2026-11-12T06:13:06Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43166576299](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43166576299) |
| 2026-11-12T00:43:04Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43129315760](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43129315760) |
| 2026-11-12T00:36:14Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43128483247](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43128483247) |
| 2026-11-12T00:34:09Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43128226810](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43128226810) |
| 2026-11-11T21:46:22Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43105986623](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43105986623) |
| 2026-11-11T19:51:06Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#43091016248](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43091016248) |
| 2026-11-11T17:07:19Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43065025249](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43065025249) |
| 2026-11-11T15:36:57Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#43050126099](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43050126099) |
| 2026-11-11T13:44:06Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43031799657](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43031799657) |
| 2026-11-11T07:06:01Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#42977025968](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42977025968) |
| 2026-11-11T06:18:18Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42971487873](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42971487873) |
| 2026-11-11T05:08:34Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42963772486](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42963772486) |
| 2026-11-10T22:56:23Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42919051828](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42919051828) |
| 2026-11-10T22:30:39Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#42915210019](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42915210019) |
| 2026-11-10T21:17:25Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42903573910](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42903573910) |
| 2026-11-10T19:59:39Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#42890789152](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42890789152) |
| 2026-11-10T16:50:24Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42858651262](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42858651262) |
| 2026-11-10T14:52:17Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42838489874](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42838489874) |
| 2026-11-10T07:43:49Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#42777320767](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42777320767) |
| 2026-11-10T06:23:07Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42768143295](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42768143295) |
| 2026-11-10T03:33:28Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42750211323](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42750211323) |
| 2026-11-10T01:27:08Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42735872792](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42735872792) |
| 2026-11-10T01:23:28Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42735448336](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42735448336) |
| 2026-11-09T22:01:36Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42707996508](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42707996508) |
| 2026-11-09T19:48:35Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42686887959](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42686887959) |
| 2026-11-09T15:12:24Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42642287490](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42642287490) |
| 2026-11-09T15:08:13Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42641563269](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42641563269) |
| 2026-11-09T11:00:27Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42605475605](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42605475605) |
| 2026-11-09T06:26:10Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42573005716](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42573005716) |
| 2026-11-09T03:21:22Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42555944971](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42555944971) |
| 2026-11-09T03:17:14Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42555550021](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42555550021) |
| 2026-11-09T00:36:19Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42541091513](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42541091513) |
| 2026-11-08T22:05:02Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42528407816](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42528407816) |
| 2026-11-08T22:04:02Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42528319927](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42528319927) |
| 2026-11-08T22:01:21Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42528087543](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42528087543) |
| 2026-11-08T19:22:40Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42514734191](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42514734191) |
| 2026-11-08T18:36:32Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42510860191](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42510860191) |
| 2026-11-08T17:55:27Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42507364460](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42507364460) |
| 2026-11-08T12:54:40Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42482429467](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42482429467) |
| 2026-11-08T12:51:19Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42482176198](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42482176198) |
| 2026-11-08T12:47:58Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42481918724](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42481918724) |
| 2026-11-08T10:21:40Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42471098474](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42471098474) |
| 2026-11-08T04:57:50Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42448867373](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42448867373) |
| 2026-11-08T03:37:08Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42443476765](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42443476765) |
| 2026-11-08T03:33:37Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42443225839](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42443225839) |
| 2026-11-08T00:34:56Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42430395436](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42430395436) |
| 2026-11-07T21:47:28Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42417521207](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42417521207) |
| 2026-11-07T21:43:24Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42417202176](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42417202176) |
| 2026-11-07T21:33:05Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42416393953](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42416393953) |
| 2026-11-07T19:25:16Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42406121145](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42406121145) |
| 2026-11-07T17:33:13Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42396879444](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42396879444) |
| 2026-11-07T12:59:58Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42374910527](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42374910527) |
| 2026-11-07T12:59:26Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42374875123](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42374875123) |
| 2026-11-07T12:56:18Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42374662250](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42374662250) |
| 2026-11-07T09:42:26Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42360857290](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42360857290) |
| 2026-11-07T05:57:27Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42344875404](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42344875404) |
| 2026-11-07T04:05:48Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42336910647](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42336910647) |
| 2026-11-07T04:02:17Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42336637596](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42336637596) |
| 2026-11-07T00:40:22Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42319636223](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42319636223) |
| 2026-11-06T23:07:29Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42309710114](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42309710114) |
| 2026-11-06T22:50:15Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42307650148](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42307650148) |
| 2026-11-06T22:45:36Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42307107032](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42307107032) |
| 2026-11-06T19:00:06Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42275723280](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42275723280) |
| 2026-11-06T16:45:17Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42255302081](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42255302081) |
| 2026-11-06T15:09:17Z | Capture FIE Waiver Evidence | POLICY_NOT_DUE | [#42240374220](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42240374220) |
| 2026-11-06T13:52:49Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42229065937](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42229065937) |
| 2026-11-06T13:48:45Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42228512514](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42228512514) |
| 2026-11-06T10:29:33Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42203067892](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42203067892) |
| 2026-11-06T06:44:01Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42176307546](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42176307546) |
| 2026-11-06T04:45:08Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42164340772](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42164340772) |
| 2026-11-06T04:40:48Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42163923632](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42163923632) |
| 2026-11-06T01:24:16Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42143608107](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42143608107) |
| 2026-11-05T23:57:48Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42133299092](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42133299092) |
| 2026-11-05T23:53:50Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#42132841226](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42132841226) |
| 2026-11-05T23:37:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42130856886](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42130856886) |
| 2026-11-05T19:38:27Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#42095810885](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42095810885) |
| 2026-11-05T17:23:20Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#42074129320](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42074129320) |
| 2026-11-05T16:44:53Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#42067613621](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42067613621) |
| 2026-11-05T15:48:07Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#42058652642](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42058652642) |
| 2026-11-05T14:17:39Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#42043599168](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42043599168) |
| 2026-11-05T14:15:24Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#42043234145](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/42043234145) |
| 2026-11-05T07:19:15Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#41986395803](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41986395803) |
| 2026-11-05T06:45:41Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41982592756](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41982592756) |
| 2026-11-05T01:20:53Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41947894191](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41947894191) |
| 2026-11-05T00:29:49Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#41941739018](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41941739018) |
| 2026-11-04T23:39:28Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41935439655](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41935439655) |
| 2026-11-04T20:01:32Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#41902586842](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41902586842) |
| 2026-11-04T19:28:42Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41897298262](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41897298262) |
| 2026-11-04T18:50:35Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#41891095729](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41891095729) |
| 2026-11-04T17:13:59Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41875552651](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41875552651) |
| 2026-11-04T15:45:39Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#41861078194](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41861078194) |
| 2026-11-04T10:35:13Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41815168917](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41815168917) |
| 2026-11-04T06:57:53Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#41788987581](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41788987581) |
| 2026-11-04T06:21:10Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41784940462](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41784940462) |
| 2026-11-04T03:10:37Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE_UNTIL_RECAPTURE | [#41765458779](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41765458779) |
| 2026-11-04T01:04:57Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41751523634](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41751523634) |
| 2026-11-03T23:37:56Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE_UNTIL_RECAPTURE | [#41740678239](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41740678239) |
| 2026-11-03T23:22:31Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41738646149](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41738646149) |
| 2026-11-03T22:30:10Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#41731338197](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41731338197) |
| 2026-11-03T20:47:52Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41715858818](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41715858818) |
| 2026-11-03T19:47:39Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#41706563575](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41706563575) |
| 2026-11-03T17:02:11Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41680214664](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41680214664) |
| 2026-11-03T13:46:43Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41647385888](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41647385888) |
| 2026-11-03T07:13:50Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#41594929756](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41594929756) |
| 2026-11-03T06:45:54Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41591949311](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41591949311) |
| 2026-11-03T05:43:53Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41585606506](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41585606506) |
| 2026-11-03T01:08:51Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41557781876](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41557781876) |
| 2026-11-03T01:05:11Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41557363842](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41557363842) |
| 2026-11-02T21:42:29Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41530795397](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41530795397) |
| 2026-11-02T21:29:15Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41528771978](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41528771978) |
| 2026-11-02T14:46:40Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41465173703](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41465173703) |
| 2026-11-02T14:42:45Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41464543963](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41464543963) |
| 2026-11-02T11:04:58Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41433898569](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41433898569) |
| 2026-11-02T10:39:57Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41430621285](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41430621285) |
| 2026-11-02T03:32:09Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41383625531](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41383625531) |
| 2026-11-02T03:28:51Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41383328348](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41383328348) |
| 2026-11-02T00:44:03Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41368726638](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41368726638) |
| 2026-11-02T00:22:38Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41366814224](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41366814224) |
| 2026-11-01T21:53:41Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41354316834](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41354316834) |
| 2026-11-01T21:50:40Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41354072726](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41354072726) |
| 2026-11-01T19:39:08Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41342805610](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41342805610) |
| 2026-11-01T19:24:05Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41341540044](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41341540044) |
| 2026-11-01T18:42:37Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41337995595](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41337995595) |
| 2026-11-01T13:23:15Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41311010499](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41311010499) |
| 2026-11-01T13:06:00Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41309602357](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41309602357) |
| 2026-11-01T13:02:47Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41309338220](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41309338220) |
| 2026-11-01T12:49:39Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41308322486](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41308322486) |
| 2026-11-01T06:03:30Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41279270164](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41279270164) |
| 2026-11-01T04:54:06Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41274839485](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41274839485) |
| 2026-11-01T03:06:58Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41267849507](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41267849507) |
| 2026-11-01T03:03:41Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41267632129](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41267632129) |
| 2026-11-01T00:07:14Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41255328718](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41255328718) |
| 2026-10-31T21:08:21Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41242165296](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41242165296) |
| 2026-10-31T21:05:51Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41241966390](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41241966390) |
| 2026-10-31T21:02:57Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41241730166](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41241730166) |
| 2026-10-31T19:17:02Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41233472607](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41233472607) |
| 2026-10-31T17:21:28Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41224136516](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41224136516) |
| 2026-10-31T17:18:19Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41223871805](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41223871805) |
| 2026-10-31T16:57:29Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41222151445](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41222151445) |
| 2026-10-31T12:27:53Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41201217296](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41201217296) |
| 2026-10-31T11:50:19Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41198503955](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41198503955) |
| 2026-10-31T11:37:51Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41197651574](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41197651574) |
| 2026-10-31T11:34:33Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41197420242](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41197420242) |
| 2026-10-31T05:39:44Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41173482246](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41173482246) |
| 2026-10-31T04:34:06Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41169097905](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41169097905) |
| 2026-10-31T03:08:32Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41163057072](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41163057072) |
| 2026-10-31T03:05:26Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41162829064](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41162829064) |
| 2026-10-30T22:46:38Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41140326344](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41140326344) |
| 2026-10-30T22:43:03Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41139939105](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41139939105) |
| 2026-10-30T22:19:07Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41137310124](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41137310124) |
| 2026-10-30T21:59:56Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41135054794](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41135054794) |
| 2026-10-30T18:00:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41103074985](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41103074985) |
| 2026-10-30T17:48:24Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41101643545](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41101643545) |
| 2026-10-30T14:17:52Z | Capture FIE Waiver Evidence | POLICY_NOT_DUE | [#41070624305](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41070624305) |
| 2026-10-30T12:41:46Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#41057275034](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41057275034) |
| 2026-10-30T12:38:32Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#41056871005](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41056871005) |
| 2026-10-30T09:59:50Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#41037454712](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41037454712) |
| 2026-10-30T09:42:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#41035399515](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/41035399515) |
| 2026-10-30T03:28:45Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40997597976](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40997597976) |
| 2026-10-30T03:25:39Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40997313323](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40997313323) |
| 2026-10-30T00:58:41Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40983024917](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40983024917) |
| 2026-10-30T00:39:44Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40981078204](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40981078204) |
| 2026-10-29T22:52:59Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40969178802](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40969178802) |
| 2026-10-29T22:50:02Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40968823022](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40968823022) |
| 2026-10-29T18:09:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40928145717](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40928145717) |

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
