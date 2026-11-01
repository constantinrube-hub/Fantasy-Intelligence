# FIE automatic workflow usability — rolling 14 days

Generated: `2026-11-01T16:01:14.559347+00:00`

Runs: **451**; usable: **168**; investigate: **44**; known gaps: **23**.

| State | Runs | Meaning |
|---|---:|---|
| USABLE | 168 | The invocation produced or verified a current, contract-valid result for its purpose. |
| NO_OP | 216 | Nothing was due, the immutable result already existed, or policy correctly skipped the invocation. |
| PARTIAL | 23 | Some intended evidence is usable, but declared source or portfolio coverage is incomplete. |
| BLOCKED | 37 | The workflow completed technically but did not prove a usable result for its intended purpose. |
| MISSED | 1 | A time-bound evidence opportunity passed without a valid prospective capture. |
| INFRASTRUCTURE | 6 | The workflow did not complete successfully because of a technical, runner, validation, or delivery failure. |

## Workflows

| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Refresh FIE Current Season | 50 | 45 | 0 | 0 | 0 | 0 | 5 | 5 |
| Build FIE Window 1C Weekly Actions | 53 | 0 | 42 | 11 | 0 | 0 | 0 | 0 |
| Build FIE Window 1D Optimal Waiver | 53 | 0 | 42 | 11 | 0 | 0 | 0 | 0 |
| Build FIE Window 2A Trench Evidence | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Availability Evidence | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE M10 Prospective Research Evidence | 55 | 1 | 54 | 0 | 0 | 0 | 0 | 0 |
| Capture Immutable FIE Sleeper Weekly Benchmark | 49 | 32 | 16 | 0 | 0 | 0 | 1 | 1 |
| Capture FIE PR2 Weekly Lineup Evidence | 57 | 2 | 55 | 0 | 0 | 0 | 0 | 0 |
| Capture Daily FIE Sleeper Season Projections / ADP | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Sunday M10 / Sleeper Paired Checkpoint | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| Capture FIE Waiver Evidence | 32 | 31 | 1 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Pregame Weather Evidence | 41 | 41 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capture FIE Weekly Research Preparation | 28 | 0 | 0 | 1 | 27 | 0 | 0 | 27 |
| FIE Component Forecast and Weekly Evaluation | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 4 |
| Evaluate FIE PR2 Weekly Lineup Capture | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 6 |

## Runs worth investigating

Expected no-ops are excluded from this table.

| Time | Workflow | State | Reason | Run |
|---|---|---|---|---|
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
| 2026-10-26T12:51:27Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40325764507](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40325764507) |
| 2026-10-26T05:16:31Z | Capture Immutable FIE Sleeper Weekly Benchmark | INFRASTRUCTURE | JOB_FAILURE | [#40273335866](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40273335866) |
| 2026-10-25T20:46:33Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40232349386](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40232349386) |
| 2026-10-25T14:37:35Z | Capture FIE Sunday M10 / Sleeper Paired Checkpoint | MISSED | CHECKPOINT_MISSED | [#40203113217](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40203113217) |
| 2026-10-25T11:18:01Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40188278484](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40188278484) |
| 2026-10-24T19:28:03Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40125421189](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40125421189) |
| 2026-10-24T09:28:43Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40082103267](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40082103267) |
| 2026-10-23T20:24:47Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#40019009821](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/40019009821) |
| 2026-10-23T09:59:52Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39935898976](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39935898976) |
| 2026-10-22T17:56:55Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39827094094](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39827094094) |
| 2026-10-22T12:36:48Z | Evaluate FIE Prospective Three-Week Waiver Evidence | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39779778360](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39779778360) |
| 2026-10-22T10:05:16Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39760429763](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39760429763) |
| 2026-10-21T17:59:33Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39648690212](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39648690212) |
| 2026-10-21T12:32:40Z | Evaluate FIE Prospective Three-Week Waiver Evidence | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39600446155](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39600446155) |
| 2026-10-21T10:27:36Z | FIE Component Forecast and Weekly Evaluation | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#39584736206](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39584736206) |
| 2026-10-21T10:03:31Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39581735896](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39581735896) |
| 2026-10-20T20:10:08Z | Evaluate FIE Prospective Three-Week Waiver Evidence | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39489663406](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39489663406) |
| 2026-10-20T17:56:51Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39470466347](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39470466347) |
| 2026-10-20T10:18:16Z | FIE Component Forecast and Weekly Evaluation | BLOCKED | USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN | [#39406978779](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39406978779) |
| 2026-10-20T09:58:26Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39404568555](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39404568555) |
| 2026-10-19T21:29:47Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39327933537](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39327933537) |
| 2026-10-19T10:42:16Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39239341071](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39239341071) |
| 2026-10-18T19:24:51Z | Capture FIE Weekly Research Preparation | BLOCKED | INVALID_USABILITY_ARTIFACT, ValueError | [#39158655037](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/39158655037) |

## Known gaps

PARTIAL by design: every reason is declared in `known_gap_reasons` in the monitor config. Counted here, not under investigate. A new reason code moves a run back to the table above.

| Workflow | Known-gap runs | Declared reasons |
|---|---:|---|
| Build FIE Window 1C Weekly Actions | 11 | OPERATIONAL_READINESS_PARTIAL |
| Build FIE Window 1D Optimal Waiver | 11 | OPERATIONAL_READINESS_PARTIAL |
| Capture FIE Weekly Research Preparation | 1 | OPERATIONAL_READINESS_PARTIAL |
| Evaluate FIE Prospective Three-Week Waiver Evidence | 0 | OPERATIONAL_READINESS_PARTIAL |

## Expected no-ops

| Time | Workflow | Reason | Run |
|---|---|---|---|
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

A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.
