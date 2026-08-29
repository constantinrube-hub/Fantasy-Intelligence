# FIE Feature Evidence Research

Generated: 2026-08-29T11:28:48.117788+00:00

## Governance

This layer is **research-only and fail-closed**. It does not alter FIE runtime projections. A candidate must still clear chronological out-of-sample testing, the temporal-block confidence interval, and downstream consumer integration before activation.

## QB

Status counts: descriptive_not_incremental=3, insufficient_coverage=1, mechanism_specific=4, no_incremental_evidence=2, promising_underpowered=2, redundant_or_explanatory=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| opportunity_xfp_realized_prior4 | regression | descriptive_not_incremental | 45% | 0.21% | 0.001..0.003 | 0.327 | no |
| team_pass_attempts_prior4_team | opportunity | promising_underpowered | 98% | 0.09% | -0.001..0.002 | 0.014 | no |
| team_plays_prior4_team | opportunity | promising_underpowered | 98% | 0.01% | -0.002..0.002 | 0.072 | no |
| xfp_residual_prior4 | regression | descriptive_not_incremental | 45% | -0.16% | -0.003..0.000 | 0.254 | no |
| qb_pass_attempt_share_prior4 | opportunity | mechanism_specific | 93% | -0.19% | -0.006..0.001 | 0.316 | no |
| snap_share_prior4 | opportunity | mechanism_specific | 93% | -0.25% | -0.006..0.001 | 0.280 | no |
| inside_5_carry_share_prior4 | opportunity | redundant_or_explanatory | 35% | -0.26% | -0.004..-0.002 | 0.020 | no |
| pfr_times_sacked_prior4 | pressure_response | no_incremental_evidence | 74% | -0.35% | -0.009..0.003 | -0.008 | no |

## RB

Status counts: horizon_specific=5, insufficient_coverage=1, mechanism_specific=1, no_incremental_evidence=1, promising_underpowered=1, validated=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| backfield_competitor_count | competition | validated | 100% | 1.41% | 0.011..0.017 | -0.361 | no |
| opportunity_xfp_realized_prior4 | regression | promising_underpowered | 47% | 0.12% | -0.001..0.002 | 0.727 | no |
| inside_5_carry_share_prior4 | opportunity | mechanism_specific | 50% | -0.11% | -0.006..0.003 | 0.336 | no |
| xfp_residual_prior4 | regression | no_incremental_evidence | 47% | -0.19% | -0.007..0.002 | 0.019 | no |
| red_zone_carry_share_prior4 | opportunity | horizon_specific | 64% | -0.20% | -0.007..0.002 | 0.405 | no |
| backfield_competition_index_prior4 | competition | horizon_specific | 94% | -0.34% | -0.008..-0.000 | -0.529 | no |
| carry_share_prior4 | opportunity | horizon_specific | 94% | -0.43% | -0.009..-0.001 | 0.668 | no |
| opportunity_change_score_prior1 | opportunity | insufficient_coverage | 29% | -0.63% | -0.015..-0.001 | 0.197 | no |

## WR

Status counts: descriptive_not_incremental=2, horizon_specific=2, insufficient_coverage=1, mechanism_specific=1, no_incremental_evidence=2, redundant_or_explanatory=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| xfp_residual_prior4 | regression | no_incremental_evidence | 47% | -0.48% | -0.014..0.003 | 0.083 | no |
| opportunity_xfp_realized_prior4 | regression | redundant_or_explanatory | 47% | -0.52% | -0.011..-0.001 | 0.694 | no |
| receiving_competitor_count | competition | descriptive_not_incremental | 100% | -0.70% | -0.011..-0.004 | -0.216 | no |
| opportunity_change_score_prior1 | opportunity | insufficient_coverage | 29% | -1.23% | -0.018..-0.006 | 0.118 | no |
| red_zone_target_share_prior4 | opportunity | descriptive_not_incremental | 45% | -1.48% | -0.019..-0.010 | 0.208 | no |
| target_share_prior4 | opportunity | horizon_specific | 94% | -1.89% | -0.025..-0.015 | 0.692 | no |
| receiving_competition_index_prior4 | competition | mechanism_specific | 94% | -1.90% | -0.025..-0.014 | -0.438 | no |
| pfr_receiving_drop_pct_prior4 | conversion | no_incremental_evidence | 73% | -1.92% | -0.026..-0.013 | 0.099 | no |

## TE

Status counts: descriptive_not_incremental=3, horizon_specific=3, insufficient_coverage=1, mechanism_specific=1, redundant_or_explanatory=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| receiving_competitor_count | competition | descriptive_not_incremental | 100% | -0.03% | -0.003..0.002 | -0.207 | no |
| xfp_residual_prior4 | regression | descriptive_not_incremental | 47% | -1.14% | -0.019..-0.005 | 0.098 | no |
| opportunity_xfp_realized_prior4 | regression | redundant_or_explanatory | 47% | -1.45% | -0.015..-0.014 | 0.657 | no |
| target_share_prior4 | opportunity | horizon_specific | 93% | -1.63% | -0.021..-0.013 | 0.641 | no |
| receiving_competition_index_prior4 | competition | horizon_specific | 93% | -1.65% | -0.022..-0.013 | -0.346 | no |
| red_zone_target_share_prior4 | opportunity | mechanism_specific | 43% | -1.66% | -0.018..-0.015 | 0.195 | no |
| pfr_receiving_drop_pct_prior4 | conversion | descriptive_not_incremental | 74% | -1.75% | -0.024..-0.013 | 0.143 | no |
| opportunity_change_score_prior1 | opportunity | insufficient_coverage | 27% | -1.76% | -0.020..-0.016 | 0.168 | no |

## Phase 2: component targets

- QB qb_pass_attempt_share_prior4 → pass_volume: mean improvement=2.23%, FDR q=0.7647058823529411
- QB snap_share_prior4 → pass_volume: mean improvement=2.11%, FDR q=0.7647058823529411
- QB qb_rush_share_prior4 → rush_volume: mean improvement=7.13%, FDR q=0.45882352941176474
- QB m7_qb_rush_goal_role → rush_volume: mean improvement=2.31%, FDR q=0.45882352941176474
- QB qb_pass_attempt_share_prior4 → yards_per_attempt: mean improvement=1.01%, FDR q=0.7222222222222222
- RB offense_snap_share_prior4 → carry_volume: mean improvement=7.79%, FDR q=0.16806722689075632
- RB carry_share_prior4 → carry_volume: mean improvement=10.76%, FDR q=0.16806722689075632
- RB target_share_prior4 → carry_volume: mean improvement=2.69%, FDR q=0.16806722689075632
- RB red_zone_carry_share_prior4 → carry_volume: mean improvement=3.33%, FDR q=0.16806722689075632
- RB inside_5_carry_share_prior4 → carry_volume: mean improvement=1.98%, FDR q=0.16806722689075632
- RB backfield_competition_index_prior4 → carry_volume: mean improvement=5.86%, FDR q=0.16806722689075632
- RB backfield_competitor_count → carry_volume: mean improvement=1.26%, FDR q=0.16806722689075632
- RB offense_snap_share_prior4 → target_volume: mean improvement=7.80%, FDR q=0.16806722689075632
- RB carry_share_prior4 → target_volume: mean improvement=4.41%, FDR q=0.16806722689075632
- RB target_share_prior4 → target_volume: mean improvement=9.46%, FDR q=0.16806722689075632
- RB red_zone_carry_share_prior4 → target_volume: mean improvement=1.08%, FDR q=0.16806722689075632
- RB backfield_competition_index_prior4 → target_volume: mean improvement=3.19%, FDR q=0.16806722689075632
- RB backfield_competitor_count → target_volume: mean improvement=1.19%, FDR q=0.16806722689075632
- WR offense_snap_share_prior4 → target_volume: mean improvement=9.75%, FDR q=0.21176470588235294
- WR target_share_prior4 → target_volume: mean improvement=10.99%, FDR q=0.21176470588235294
- WR receiving_competition_index_prior4 → target_volume: mean improvement=2.62%, FDR q=0.21176470588235294
- TE offense_snap_share_prior4 → target_volume: mean improvement=7.79%, FDR q=0.21176470588235294
- TE target_share_prior4 → target_volume: mean improvement=10.67%, FDR q=0.21176470588235294
- TE red_zone_target_share_prior4 → target_volume: mean improvement=1.45%, FDR q=0.21176470588235294
- TE receiving_competition_index_prior4 → target_volume: mean improvement=2.08%, FDR q=0.21176470588235294
- QB pass_volume all-feature challenger: validated_component_signal, mean improvement=2.80%
- QB rush_volume all-feature challenger: validated_component_signal, mean improvement=7.09%
- QB completion_rate all-feature challenger: diagnostic_component_signal, mean improvement=-0.53%
- QB yards_per_attempt all-feature challenger: diagnostic_component_signal, mean improvement=0.21%
- RB carry_volume all-feature challenger: validated_component_signal, mean improvement=10.90%
- RB target_volume all-feature challenger: validated_component_signal, mean improvement=9.50%
- RB rushing_efficiency all-feature challenger: diagnostic_component_signal, mean improvement=-0.17%
- RB catch_conversion all-feature challenger: diagnostic_component_signal, mean improvement=-0.53%
- WR target_volume all-feature challenger: validated_component_signal, mean improvement=11.02%
- WR catch_conversion all-feature challenger: diagnostic_component_signal, mean improvement=0.26%
- WR yards_per_target all-feature challenger: diagnostic_component_signal, mean improvement=0.38%
- TE target_volume all-feature challenger: validated_component_signal, mean improvement=10.59%
- TE catch_conversion all-feature challenger: diagnostic_component_signal, mean improvement=0.05%
- TE yards_per_target all-feature challenger: diagnostic_component_signal, mean improvement=0.20%

## Phase 3: validated future/tail horizons

- RB offense_snap_share_prior4 → next_week: mean improvement=2.50%
- RB offense_snap_share_prior4 → next_3_games: mean improvement=3.40%
- RB offense_snap_share_prior4 → rest_of_season: mean improvement=4.09%
- RB offense_snap_share_prior4 → floor: mean improvement=4.25%
- RB offense_snap_share_prior4 → ceiling: mean improvement=1.48%
- RB offense_snap_share_prior4 → breakout: mean improvement=5.34%
- RB carry_share_prior4 → next_week: mean improvement=2.01%
- RB carry_share_prior4 → next_3_games: mean improvement=3.33%
- RB carry_share_prior4 → rest_of_season: mean improvement=4.21%
- RB carry_share_prior4 → floor: mean improvement=2.93%
- RB carry_share_prior4 → breakout: mean improvement=4.68%
- RB target_share_prior4 → rest_of_season: mean improvement=1.11%
- RB red_zone_carry_share_prior4 → breakout: mean improvement=1.27%
- RB backfield_competition_index_prior4 → next_week: mean improvement=1.39%
- RB backfield_competition_index_prior4 → next_3_games: mean improvement=1.86%
- RB backfield_competition_index_prior4 → rest_of_season: mean improvement=2.31%
- RB backfield_competition_index_prior4 → floor: mean improvement=1.57%
- RB backfield_competition_index_prior4 → breakout: mean improvement=2.44%
- RB backfield_competitor_count → next_3_games: mean improvement=1.11%
- RB backfield_competitor_count → rest_of_season: mean improvement=1.26%
- RB backfield_competitor_count → floor: mean improvement=1.52%
- RB backfield_competitor_count → breakout: mean improvement=1.17%
- WR offense_snap_share_prior4 → next_week: mean improvement=2.22%
- WR offense_snap_share_prior4 → next_3_games: mean improvement=3.29%
- WR offense_snap_share_prior4 → rest_of_season: mean improvement=3.09%
- WR offense_snap_share_prior4 → floor: mean improvement=5.95%
- WR offense_snap_share_prior4 → breakout: mean improvement=6.05%
- WR target_share_prior4 → next_week: mean improvement=2.38%
- WR target_share_prior4 → next_3_games: mean improvement=3.92%
- WR target_share_prior4 → rest_of_season: mean improvement=4.70%

## Phase 4: model challengers

- QB ridge: mean ΔMAE=-0.28%, CI low=-0.008460730326961317, diagnostic_only
- QB elastic: mean ΔMAE=-0.31%, CI low=-0.008493960283739993, diagnostic_only
- QB partial_pool: mean ΔMAE=-0.04%, CI low=-0.007367467566310151, diagnostic_only
- QB histgb: mean ΔMAE=1.40%, CI low=0.0005518647476741547, eligible_for_manual_consumer_integration
- RB ridge: mean ΔMAE=0.70%, CI low=-0.002774617400240876, diagnostic_only
- RB elastic: mean ΔMAE=0.79%, CI low=-0.0006120782823373153, diagnostic_only
- RB partial_pool: mean ΔMAE=0.51%, CI low=-0.0039307030257653384, diagnostic_only
- RB histgb: mean ΔMAE=2.37%, CI low=0.01776898260963914, eligible_for_manual_consumer_integration
- WR ridge: mean ΔMAE=-0.98%, CI low=-0.01435413792235125, diagnostic_only
- WR elastic: mean ΔMAE=-0.95%, CI low=-0.01387530205963825, diagnostic_only
- WR partial_pool: mean ΔMAE=-1.56%, CI low=-0.028203020865165393, diagnostic_only
- WR histgb: mean ΔMAE=-0.60%, CI low=-0.012603326370069777, diagnostic_only
- TE ridge: mean ΔMAE=-0.53%, CI low=-0.007472937358551369, diagnostic_only
- TE elastic: mean ΔMAE=-0.47%, CI low=-0.0070937436006159055, diagnostic_only
- TE partial_pool: mean ΔMAE=-0.60%, CI low=-0.020501741783624457, diagnostic_only
- TE histgb: mean ΔMAE=-0.42%, CI low=-0.012259172685812014, diagnostic_only

## Phase 5: conditional effects

- QB rush_x_goal: diagnostic_conditional_signal, incremental over main effects=-0.05%

## Phase 6: highest-priority data expansion

- RB opportunity_xfp_realized_prior4: collect_more_history (priority 73.19)
- RB opportunity_change_score_prior1: improve_source_coverage (priority 67.42)
- TE opportunity_change_score_prior1: improve_source_coverage (priority 64.97)
- QB xfp_residual_prior4: test_predefined_condition_or_accept_redundancy (priority 63.82)
- QB opportunity_xfp_realized_prior4: test_predefined_condition_or_accept_redundancy (priority 63.82)
- WR red_zone_target_share_prior4: test_predefined_condition_or_accept_redundancy (priority 63.78)
- WR opportunity_change_score_prior1: improve_source_coverage (priority 59.55)
- RB red_zone_carry_share_prior4: route_to_best_horizon (priority 58.98)
- QB opportunity_change_score_prior1: improve_source_coverage (priority 57.1)
- TE offense_snap_share_prior4: route_to_best_horizon (priority 55.18)
- RB offense_snap_share_prior4: route_to_best_horizon (priority 54.84)
- WR offense_snap_share_prior4: route_to_best_horizon (priority 54.76)
- TE xfp_residual_prior4: test_predefined_condition_or_accept_redundancy (priority 53.1)
- TE target_share_prior4: route_to_best_horizon (priority 51.64)
- TE receiving_competition_index_prior4: route_to_best_horizon (priority 51.64)
- RB carry_share_prior4: route_to_best_horizon (priority 51.6)
- RB target_share_prior4: route_to_best_horizon (priority 51.6)
- RB backfield_competition_index_prior4: route_to_best_horizon (priority 51.6)
- WR target_share_prior4: route_to_best_horizon (priority 51.57)
- TE pfr_receiving_drop_pct_prior4: test_predefined_condition_or_accept_redundancy (priority 50.89)

## Phase 7: production gate

No feature or challenger is auto-activated by this audit. `eligible_for_manual_consumer_integration` means only that the challenger cleared the same robust chronological gate and may be wired into a downstream model in a separate, revalidated change.

## Evidence Hardening

- Extended M4 OOS backfill is research-only and never overwrites the canonical M4 artifact.
- Next-season comparisons now use calibrated Ridge baseline vs calibrated Ridge+feature on identical rows.
- Feature hypotheses are de-duplicated across semantic families before validation/FDR.
- Consumer routes emitted: 72; all require manual integration and revalidation.
- QB: OOS seasons=[2019, 2020, 2021, 2022, 2023, 2024, 2025]; second-stage residual folds=4.
- RB: OOS seasons=[2019, 2020, 2021, 2022, 2023, 2024, 2025]; second-stage residual folds=4.
- WR: OOS seasons=[2019, 2020, 2021, 2022, 2023, 2024, 2025]; second-stage residual folds=4.
- TE: OOS seasons=[2019, 2020, 2021, 2022, 2023, 2024, 2025]; second-stage residual folds=4.
