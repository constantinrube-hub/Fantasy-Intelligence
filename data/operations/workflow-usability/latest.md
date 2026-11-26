# FIE automatic workflow usability — rolling 14 days

Generated: `2026-11-26T19:03:20.934658+00:00`

Runs: **332**; usable: **113**; investigate: **20**; known gaps: **50**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 113 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 149 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 51 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 0 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 2 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 17 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 35 | 21 | 0 | 0 | 0 | 0 | 14 | 14 |
| Build FIE Window 1C Weekly Actions | 36 | 0 | 28 | 8 | 0 | 0 | 0 | 0 |
| Build FIE Window 1D Optimal Waiver | 35 | 0 | 27 | 8 | 0 | 0 | 0 | 0 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE M10 Prospective Research Evidence | 39 | 1 | 35 | 0 | 0 | 0 | 3 | 3 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 29 | 23 | 6 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE PR2 Weekly Lineup Evidence | 41 | 3 | 38 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| Capture FIE Waiver Evidence | 23 | 21 | 1 | 1 | 0 | 0 | 0 | 1 |
| Capture FIE Pregame Weather Evidence | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Weekly Research Preparation | 28 | 0 | 0 | 28 | 0 | 0 | 0 | 0 |
| FIE Component Forecast and Weekly Evaluation | 11 | 3 | 8 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE PR2 Weekly Lineup Capture | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
| 2026-11-26T11:58:59Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | JOB_FAILURE | [#45815411392](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45815411392) |
| 2026-11-26T01:39:42Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | JOB_FAILURE | [#45737247971](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45737247971) |
| 2026-11-25T16:55:09Z | Capture FIE M10 Prospective Research Evidence | INFRASTRUCTURE | JOB_FAILURE | [#45659113564](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45659113564) |
| 2026-11-22T18:44:47Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#45056810852](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45056810852) |
| 2026-11-18T11:50:25Z | Capture FIE Waiver Evidence | PARTIAL | PARTIAL_SOURCE_FAILURE | [#44298305191](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44298305191) |
| 2026-11-17T14:24:11Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#44102710227](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44102710227) |
| 2026-11-17T00:48:12Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43990563828](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43990563828) |
| 2026-11-16T13:39:32Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43877885605](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43877885605) |
| 2026-11-16T02:43:46Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43793909021](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43793909021) |
| 2026-11-15T21:49:11Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43765780471](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43765780471) |
| 2026-11-15T18:03:35Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#43744568284](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43744568284) |
| 2026-11-15T12:44:15Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43715352904](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43715352904) |
| 2026-11-15T02:39:20Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43668792682](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43668792682) |
| 2026-11-14T21:29:40Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43643095286](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43643095286) |
| 2026-11-14T12:11:31Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43593580891](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43593580891) |
| 2026-11-14T03:15:20Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43550664626](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43550664626) |
| 2026-11-13T22:37:38Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43520812217](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43520812217) |
| 2026-11-13T13:06:51Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43430842978](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43430842978) |
| 2026-11-13T03:24:59Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43358806066](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43358806066) |
| 2026-11-12T22:43:40Z | Refresh FIE Current Season | INFRASTRUCTURE | JOB_FAILURE | [#43322544608](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43322544608) |

## Known gaps

PARTIAL by design: every reason is declared in `known_gap_reasons` in the monitor config. Counted here, not under investigate. A new reason code moves a run back to the table above.

| Workflow | Known-gap runs | Declared reasons |
|---|---:|---|
| Build FIE Window 1C Weekly Actions | 8 | OPERATIONAL_READINESS_PARTIAL |
| Build FIE Window 1D Optimal Waiver | 8 | OPERATIONAL_READINESS_PARTIAL |
| Capture FIE Weekly Research Preparation | 28 | OPERATIONAL_READINESS_PARTIAL |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 6 | OPERATIONAL_READINESS_PARTIAL |

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
| 2026-11-26T17:53:12Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#45871458987](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45871458987) |
| 2026-11-26T16:53:27Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45862879965](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45862879965) |
| 2026-11-26T16:32:42Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#45859742880](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45859742880) |
| 2026-11-26T16:26:20Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#45858765230](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45858765230) |
| 2026-11-26T08:51:25Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#45786710659](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45786710659) |
| 2026-11-26T03:33:55Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45749725870](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45749725870) |
| 2026-11-26T02:24:46Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#45742236985](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45742236985) |
| 2026-11-25T18:10:31Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#45672400036](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45672400036) |
| 2026-11-25T18:08:47Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#45672102138](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45672102138) |
| 2026-11-25T08:32:34Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45577192705](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45577192705) |
| 2026-11-25T03:58:38Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45543600773](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45543600773) |
| 2026-11-25T01:35:26Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#45526859596](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45526859596) |
| 2026-11-24T23:53:34Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45513719390](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45513719390) |
| 2026-11-24T22:45:20Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#45503861136](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45503861136) |
| 2026-11-24T19:59:43Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45476044677](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45476044677) |
| 2026-11-24T13:41:42Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45406078974](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45406078974) |
| 2026-11-24T10:24:40Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#45374532536](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45374532536) |
| 2026-11-24T08:53:39Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45360090945](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45360090945) |
| 2026-11-24T04:24:22Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#45326162337](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45326162337) |
| 2026-11-24T04:14:32Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#45324999148](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45324999148) |
| 2026-11-24T02:12:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45310630244](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45310630244) |
| 2026-11-23T23:39:42Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45290733562](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45290733562) |
| 2026-11-23T16:58:55Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#45222550649](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45222550649) |
| 2026-11-23T16:53:19Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#45221529059](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45221529059) |
| 2026-11-23T12:38:05Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45176163276](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45176163276) |
| 2026-11-23T11:56:22Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45169636270](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45169636270) |
| 2026-11-23T04:34:50Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#45112698103](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45112698103) |
| 2026-11-23T04:29:11Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#45112122723](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45112122723) |
| 2026-11-23T01:41:40Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45095992784](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45095992784) |
| 2026-11-23T01:26:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45094598193](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45094598193) |
| 2026-11-22T23:12:22Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#45081966260](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45081966260) |
| 2026-11-22T23:07:23Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#45081498587](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45081498587) |
| 2026-11-22T20:32:57Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45067050665](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45067050665) |
| 2026-11-22T19:38:45Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45061928851](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45061928851) |
| 2026-11-22T19:10:45Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45059269325](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45059269325) |
| 2026-11-22T14:14:03Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#45031700449](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45031700449) |
| 2026-11-22T14:08:47Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#45031208170](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45031208170) |
| 2026-11-22T11:23:28Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#45017088405](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45017088405) |
| 2026-11-22T10:49:42Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#45014307599](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/45014307599) |
| 2026-11-22T04:39:21Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44986003150](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44986003150) |
| 2026-11-22T04:34:13Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44985633463](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44985633463) |
| 2026-11-22T01:18:09Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44970805843](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44970805843) |
| 2026-11-22T01:00:14Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44969344596](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44969344596) |
| 2026-11-21T23:04:31Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44959959156](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44959959156) |
| 2026-11-21T22:57:31Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44959369476](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44959369476) |
| 2026-11-21T19:14:47Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44939887562](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44939887562) |
| 2026-11-21T18:48:32Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44937526349](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44937526349) |
| 2026-11-21T14:50:04Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44915966295](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44915966295) |
| 2026-11-21T14:44:52Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44915517980](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44915517980) |
| 2026-11-21T10:59:43Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44896927687](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44896927687) |
| 2026-11-21T10:44:05Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44895735605](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44895735605) |
| 2026-11-21T05:01:02Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44868841222](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44868841222) |
| 2026-11-21T04:54:07Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44868308286](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44868308286) |
| 2026-11-21T02:13:21Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44854666866](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44854666866) |
| 2026-11-21T01:59:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44853340152](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44853340152) |
| 2026-11-20T23:54:27Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44840156835](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44840156835) |
| 2026-11-20T23:50:04Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44839645035](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44839645035) |
| 2026-11-20T20:17:23Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44809989261](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44809989261) |
| 2026-11-20T19:42:27Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44804634163](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44804634163) |
| 2026-11-20T16:13:38Z | Capture FIE Waiver Evidence | POLICY_NOT_DUE | [#44771206244](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44771206244) |
| 2026-11-20T14:50:55Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44757401734](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44757401734) |
| 2026-11-20T14:45:42Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44756556523](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44756556523) |
| 2026-11-20T11:38:21Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44729233732](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44729233732) |
| 2026-11-20T10:59:47Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44723863374](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44723863374) |
| 2026-11-20T02:18:59Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44659894073](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44659894073) |
| 2026-11-20T02:03:27Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44658042597](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44658042597) |
| 2026-11-20T00:28:13Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44646106778](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44646106778) |
| 2026-11-20T00:23:10Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44645432764](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44645432764) |
| 2026-11-19T20:06:13Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44605182169](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44605182169) |
| 2026-11-19T17:36:31Z | FIE Component Forecast and Weekly Evaluation | OUTSIDE_WINDOW_OR_CALENDAR | [#44579007158](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44579007158) |
| 2026-11-19T16:46:55Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#44569955392](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44569955392) |
| 2026-11-19T15:31:31Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44555759690](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44555759690) |
| 2026-11-19T15:27:08Z | Build FIE Window 1C Weekly Actions | PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY | [#44554932761](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44554932761) |
| 2026-11-19T11:38:29Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44516633226](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44516633226) |
| 2026-11-19T07:51:49Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#44482883549](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44482883549) |
| 2026-11-19T02:33:46Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44445218863](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44445218863) |
| 2026-11-19T02:19:59Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44443522220](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44443522220) |
| 2026-11-18T22:40:31Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE | [#44413819243](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44413819243) |
| 2026-11-18T20:52:56Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#44395646483](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44395646483) |
| 2026-11-18T20:29:55Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44391633002](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44391633002) |
| 2026-11-18T20:06:30Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44387495032](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44387495032) |
| 2026-11-18T16:43:03Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#44350440826](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44350440826) |
| 2026-11-18T11:40:36Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44296841467](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44296841467) |
| 2026-11-18T11:15:20Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44293001496](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44293001496) |
| 2026-11-18T07:55:28Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#44262666858](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44262666858) |
| 2026-11-18T04:40:21Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE_UNTIL_RECAPTURE | [#44238933319](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44238933319) |
| 2026-11-18T02:45:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44225586097](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44225586097) |
| 2026-11-18T01:15:31Z | FIE Component Forecast and Weekly Evaluation | ALREADY_DONE_UNTIL_RECAPTURE | [#44214400071](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44214400071) |
| 2026-11-18T00:57:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44211995169](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44211995169) |
| 2026-11-17T23:56:47Z | Evaluate FIE PR2 Weekly Lineup Capture | NO_IMMUTABLE_CAPTURE | [#44203710470](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44203710470) |
| 2026-11-17T21:19:33Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#44178609329](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44178609329) |
| 2026-11-17T18:14:56Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44145768667](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44145768667) |
| 2026-11-17T15:58:58Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44120506865](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44120506865) |
| 2026-11-17T15:10:06Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44111195494](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44111195494) |
| 2026-11-17T15:07:07Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#44110633370](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44110633370) |
| 2026-11-17T08:28:20Z | Capture Immutable FIE Sleeper Weekly Benchmark | NO_REPOSITORY_CHANGE | [#44047004784](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44047004784) |
| 2026-11-17T06:59:22Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#44035244798](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44035244798) |
| 2026-11-17T03:52:44Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#44013247565](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44013247565) |
| 2026-11-17T02:10:34Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#44001028063](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44001028063) |
| 2026-11-17T02:07:33Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#44000656353](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/44000656353) |
| 2026-11-16T21:43:56Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43963030083](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43963030083) |
| 2026-11-16T19:35:47Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43940975384](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43940975384) |
| 2026-11-16T14:37:15Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43887632549](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43887632549) |
| 2026-11-16T14:34:09Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43887087126](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43887087126) |
| 2026-11-16T10:44:40Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43851564267](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43851564267) |
| 2026-11-16T06:27:34Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43816881831](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43816881831) |
| 2026-11-16T03:38:09Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43799363783](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43799363783) |
| 2026-11-16T00:49:03Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43782600239](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43782600239) |
| 2026-11-15T23:09:52Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43773291822](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43773291822) |
| 2026-11-15T23:06:42Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43772998738](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43772998738) |
| 2026-11-15T22:47:25Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43771229071](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43771229071) |
| 2026-11-15T19:30:41Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43752819103](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43752819103) |
| 2026-11-15T18:35:23Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43747607503](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43747607503) |
| 2026-11-15T16:20:46Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43734955557](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43734955557) |
| 2026-11-15T13:32:53Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43719563502](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43719563502) |
| 2026-11-15T13:30:31Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43719350529](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43719350529) |
| 2026-11-15T10:29:14Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43704295948](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43704295948) |
| 2026-11-15T06:30:12Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43685724571](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43685724571) |
| 2026-11-15T03:23:09Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43672122189](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43672122189) |
| 2026-11-15T03:20:14Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43671895610](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43671895610) |
| 2026-11-15T00:49:32Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43660096278](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43660096278) |
| 2026-11-14T22:27:11Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43648165642](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43648165642) |
| 2026-11-14T22:24:11Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43647907206](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43647907206) |
| 2026-11-14T22:23:32Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43647849519](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43647849519) |
| 2026-11-14T19:46:59Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43633945842](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43633945842) |
| 2026-11-14T17:59:56Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43624104679](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43624104679) |
| 2026-11-14T13:07:55Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43598207730](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43598207730) |
| 2026-11-14T13:07:35Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43598178835](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43598178835) |
| 2026-11-14T13:05:44Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43598020134](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43598020134) |
| 2026-11-14T10:24:38Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43585147578](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43585147578) |
| 2026-11-14T05:25:26Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43561457506](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43561457506) |
| 2026-11-14T04:12:31Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43555476231](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43555476231) |
| 2026-11-14T04:09:30Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43555216419](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43555216419) |
| 2026-11-14T01:26:41Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43540624437](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43540624437) |
| 2026-11-13T23:21:54Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43526553034](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43526553034) |
| 2026-11-13T23:19:38Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43526264183](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43526264183) |
| 2026-11-13T21:14:07Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43508843752](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43508843752) |
| 2026-11-13T19:40:49Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43494470775](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43494470775) |
| 2026-11-13T14:05:46Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43439494883](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43439494883) |
| 2026-11-13T14:03:38Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43439163653](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43439163653) |
| 2026-11-13T14:00:34Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43438679169](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43438679169) |
| 2026-11-13T10:57:38Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43413153214](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43413153214) |
| 2026-11-13T05:34:01Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43372854228](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43372854228) |
| 2026-11-13T04:43:30Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43367355650](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43367355650) |
| 2026-11-13T04:41:33Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43367151399](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43367151399) |
| 2026-11-13T01:48:51Z | Capture FIE PR2 Weekly Lineup Evidence | OUTSIDE_CHECKPOINT_WINDOW | [#43347648287](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43347648287) |
| 2026-11-12T23:38:55Z | Build FIE Window 1D Optimal Waiver | PIPELINE_UPSTREAM_NOT_DUE | [#43330615458](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43330615458) |
| 2026-11-12T23:36:51Z | Build FIE Window 1C Weekly Actions | CALENDAR_POLICY_SKIPPED_PRODUCER | [#43330330996](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43330330996) |
| 2026-11-12T23:17:01Z | Capture FIE M10 Prospective Research Evidence | NO_REPOSITORY_CHANGE | [#43327523099](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/43327523099) |

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
