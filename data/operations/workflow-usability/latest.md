# FIE automatic workflow usability — rolling 14 days

Generated: `2026-11-09T19:48:15.141312+00:00`

Runs: **390**; usable: **138**; investigate: **26**; known gaps: **38**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 138 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 188 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 40 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 16 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 2 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 6 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 42 | 35 | 0 | 1 | 0 | 0 | 6 | 7 |
| Build FIE Window 1C Weekly Actions | 45 | 0 | 36 | 9 | 0 | 0 | 0 | 0 |
| Build FIE Window 1D Optimal Waiver | 45 | 0 | 36 | 9 | 0 | 0 | 0 | 0 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE M10 Prospective Research Evidence | 46 | 1 | 45 | 0 | 0 | 0 | 0 | 0 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 37 | 26 | 11 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE PR2 Weekly Lineup Evidence | 47 | 1 | 46 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Capture FIE Waiver Evidence | 30 | 27 | 2 | 1 | 0 | 0 | 0 | 1 |
| Capture FIE Pregame Weather Evidence | 31 | 31 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Weekly Research Preparation | 28 | 0 | 0 | 17 | 11 | 0 | 0 | 11 |
| FIE Component Forecast and Weekly Evaluation | 9 | 1 | 6 | 0 | 2 | 0 | 0 | 2 |
| Evaluate FIE PR2 Weekly Lineup Capture | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 6 | 0 | 0 | 3 | 3 | 0 | 0 | 3 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
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
| 2026-10-29T14:44:00Z | Evaluate FIE Prospective Three-Week Waiver Evidence | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40894420449](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40894420449) |
| 2026-10-29T12:52:58Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40876971081](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40876971081) |
| 2026-10-28T19:29:33Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40754769959](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40754769959) |
| 2026-10-28T14:39:49Z | Evaluate FIE Prospective Three-Week Waiver Evidence | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40708164188](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40708164188) |
| 2026-10-28T12:43:02Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40690107994](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40690107994) |
| 2026-10-28T11:30:06Z | FIE Component Forecast and Weekly Evaluation | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#40680432702](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40680432702) |
| 2026-10-28T11:20:32Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40679195439](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40679195439) |
| 2026-10-28T02:15:28Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40619855587](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40619855587) |
| 2026-10-27T21:29:35Z | Evaluate FIE Prospective Three-Week Waiver Evidence | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40587229743](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40587229743) |
| 2026-10-27T21:19:53Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40585861965](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40585861965) |
| 2026-10-27T19:24:03Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40568755310](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40568755310) |
| 2026-10-27T16:39:01Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40542987042](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40542987042) |
| 2026-10-27T12:01:53Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40500589660](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40500589660) |
| 2026-10-27T10:47:59Z | FIE Component Forecast and Weekly Evaluation | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#40491263097](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40491263097) |
| 2026-10-27T10:34:32Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#40489539871](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40489539871) |
| 2026-10-26T22:36:41Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40413756982](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40413756982) |

## Known gaps

PARTIAL by design: every reason is declared in `known_gap_reasons` in the monitor config. Counted here, not under investigate. A new reason code moves a run back to the table above.

| Workflow | Known-gap runs | Declared reasons |
|---|---:|---|
| Build FIE Window 1C Weekly Actions | 9 | OPERATIONAL_READINESS_PARTIAL |
| Build FIE Window 1D Optimal Waiver | 9 | OPERATIONAL_READINESS_PARTIAL |
| Capture FIE Weekly Research Preparation | 17 | OPERATIONAL_READINESS_PARTIAL |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 3 | OPERATIONAL_READINESS_PARTIAL |

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
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
| 2026-10-29T14:38:42Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#40893545127](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40893545127) |
| 2026-10-29T12:09:10Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40870929721](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40870929721) |
| 2026-10-29T12:06:10Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#40870533356](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40870533356) |
| 2026-10-29T09:57:25Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40853680810](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40853680810) |
| 2026-10-29T09:31:50Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40850351575](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40850351575) |
| 2026-10-29T00:55:57Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40797235544](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40797235544) |
| 2026-10-29T00:38:52Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40795414564](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40795414564) |
| 2026-10-28T22:50:31Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#40783003574](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40783003574) |
| 2026-10-28T20:34:28Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40764490530](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40764490530) |
| 2026-10-28T20:32:36Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40764212521](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40764212521) |
| 2026-10-28T20:16:00Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#40761717754](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40761717754) |
| 2026-10-28T20:07:00Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#40760361640](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40760361640) |
| 2026-10-28T17:17:37Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#40734308764](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40734308764) |
| 2026-10-28T17:09:33Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#40733003907](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40733003907) |
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

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
