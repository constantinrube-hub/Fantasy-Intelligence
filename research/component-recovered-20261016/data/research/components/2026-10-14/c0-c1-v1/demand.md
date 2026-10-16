# C0 component demand and source audit

23 enabled leagues; 98 configured nonzero keys; 97 relevant keys; 95 required component/probability outputs.

Registration and source-bound outcomes do not certify every provider convention or a complete forecast.

| League | Relevant keys | Explicitly irrelevant configured keys |
|---|---:|---:|
| Stoned Lack Dynasty 29 (1312066407394975744) | 26 | 16 |
| Chopped - Drive 🏉 Football League (1313696967989157888) | 18 | 31 |
| ReDraft – Pro 🎯 XVI Football  (1313697754907697152) | 35 | 9 |
| Dynasty - Prime 💎 XVI Football  (1314002567004459008) | 19 | 25 |
| BestBall - Pro 🎖️XVI League (1314007486205804544) | 17 | 25 |
| BestBall - Prime 🏆 XVI League (1314008320385748992) | 19 | 25 |
| Crazy tryhards (1315816926198382592) | 26 | 25 |
| Genesis Dynasty - sixteen now & for the future (1316165875291668480) | 56 | 0 |
| Stoned Lack IDP Dynasty 39 (1331042152091766784) | 33 | 24 |
| Stoned Lack Bestball Dynasty 4 (1332838151168724992) | 14 | 0 |
| Stoned Lack Dynasty 30 (1335691030116184065) | 26 | 16 |
| Stoned Lack Bestball Dynasty 3 (1341105213464924160) | 15 | 0 |
| Stoned Lack Bestball 2 (1341131690998788096) | 14 | 0 |
| Genesis NFL GM League Dynasty 2025 4 (1342896584593018880) | 35 | 26 |
| 🪓 MinusPPR Knockout (1343914986388353024) | 23 | 24 |
| German Football League (1387106650413887488) | 39 | 0 |
| Guillotine - last team standing (1387526015705690112) | 16 | 25 |
| SLR2026 - Liga 38 (1391803939736801280) | 41 | 0 |
| The Hunger Games (1397547920563171328) | 17 | 25 |
| AEF - FFLeague (1399128582088835072) | 45 | 0 |
| Ultimate ITN Chopped League (1400388486179123200) | 16 | 25 |
| 🪓 The Final Cut (1400561646463672320) | 18 | 25 |
| 🪓 Among Us Guillotine 3 (1402643913583398912) | 18 | 25 |

| Component | Mode | Unit | Source method |
|---|---|---|---|
| dst_blocked_kick_return_yards | mean | yards | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_blocked_kicks | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_defensive_touchdowns | mean | count | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_field_goal_return_yards | mean | yards | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_forced_fumbles | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_fourth_down_stops | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_fumble_recoveries | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_fumble_return_yards | mean | yards | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_interception_return_yards | mean | yards | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_interceptions | mean | count | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_kick_return_yards | mean | yards | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_passes_defended | mean | count | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_prob_pts_allow_0 | probability | probability | EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND |
| dst_prob_pts_allow_14_20 | probability | probability | EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND |
| dst_prob_pts_allow_1_6 | probability | probability | EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND |
| dst_prob_pts_allow_28_34 | probability | probability | EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND |
| dst_prob_pts_allow_35p | probability | probability | EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND |
| dst_prob_pts_allow_7_13 | probability | probability | EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND |
| dst_punt_return_yards | mean | yards | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_sacks | mean | count | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| dst_safeties | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_special_teams_forced_fumbles | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_special_teams_fumble_recoveries | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| dst_special_teams_touchdowns | mean | count | ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS |
| fumbles | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| fumbles_lost | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_blocked_kicks | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_defensive_touchdowns | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_forced_fumbles | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_fumble_recoveries | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_fumble_return_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_interception_return_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_interceptions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_passes_defended | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_quarterback_hits | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| idp_sack_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_sacks | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_safeties | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_tackles_assisted | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_tackles_for_loss | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_tackles_solo | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| idp_tackles_total | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| individual_special_teams_forced_fumbles | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| individual_special_teams_fumble_recoveries | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| individual_special_teams_touchdowns | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| kick_return_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_0_19 | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_20_29 | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_30_39 | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_40_49 | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_50_59 | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_50p | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_60p | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgm_yds | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgmiss | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_fgmiss_0_19 | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| kicker_fgmiss_20_29 | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| kicker_fgmiss_30_39 | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| kicker_fgmiss_40_49 | mean | count | EXPLICIT_PROVIDER_STAT_ONLY |
| kicker_xpm | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| kicker_xpmiss | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| offensive_fumble_recovery_touchdowns | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| passing_attempts | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| passing_completions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| passing_completions_40_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| passing_first_downs | mean | count | PUBLISHED_FIRST_DOWNS_MINUS_TOUCHDOWNS |
| passing_interceptions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| passing_pick_sixes | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| passing_sacks_charged | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| passing_touchdowns | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| passing_touchdowns_40_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| passing_touchdowns_50_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| passing_two_point_conversions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| passing_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| prob_pass_yd_300 | probability | probability | EXCLUSIVE_GAME_YARDAGE_BAND |
| prob_pass_yd_400 | probability | probability | EXCLUSIVE_GAME_YARDAGE_BAND |
| prob_rec_yd_100 | probability | probability | EXCLUSIVE_GAME_YARDAGE_BAND |
| prob_rush_yd_100 | probability | probability | EXCLUSIVE_GAME_YARDAGE_BAND |
| punt_return_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| receiving_first_downs | mean | count | PUBLISHED_FIRST_DOWNS_MINUS_TOUCHDOWNS |
| receiving_touchdowns | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| receiving_touchdowns_40_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| receiving_touchdowns_50_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| receiving_two_point_conversions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| receiving_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| receptions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| receptions_40_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| rushes_40_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| rushing_attempts | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| rushing_first_downs | mean | count | PUBLISHED_FIRST_DOWNS_MINUS_TOUCHDOWNS |
| rushing_touchdowns | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| rushing_touchdowns_40_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| rushing_touchdowns_50_plus | mean | count | SCOPED_CANONICAL_EVENT_LEDGER |
| rushing_two_point_conversions | mean | count | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
| rushing_yards | mean | yards | ADDITIVE_PUBLISHED_PLAYER_FIELDS |
