# FIE Feature Evidence Research

Generated: 2026-08-29T00:35:16.426398+00:00

## Governance

This layer is **research-only and fail-closed**. It does not alter FIE runtime projections. A candidate must still clear chronological out-of-sample testing, the temporal-block confidence interval, and downstream consumer integration before activation.

## QB

Status counts: descriptive_not_incremental=3, insufficient_coverage=1, mechanism_specific=5, no_incremental_evidence=5, redundant_or_explanatory=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| qb_pass_attempt_share_prior4 | opportunity | mechanism_specific | 93% | 0.65% | n/a | 0.316 | no |
| team_plays_prior4_team | opportunity | no_incremental_evidence | 98% | 0.62% | n/a | 0.072 | no |
| team_pass_attempts_prior4_team | opportunity | no_incremental_evidence | 98% | 0.59% | n/a | 0.014 | no |
| snap_share_prior4 | opportunity | mechanism_specific | 93% | 0.54% | n/a | 0.280 | no |
| opportunity_xfp_realized_prior4 | regression | descriptive_not_incremental | 45% | 0.09% | n/a | 0.327 | no |
| qb_rush_share_prior4 | opportunity | mechanism_specific | 93% | 0.07% | n/a | 0.276 | no |
| qb_rush_share_prior4 | rushing_leverage | mechanism_specific | 93% | 0.07% | n/a | 0.276 | no |
| opportunity_change_score_prior1 | opportunity | insufficient_coverage | 25% | 0.03% | n/a | -0.084 | no |

## RB

Status counts: descriptive_not_incremental=1, horizon_specific=7, insufficient_coverage=1, mechanism_specific=1, no_incremental_evidence=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| backfield_competitor_count | competition | horizon_specific | 100% | 1.60% | n/a | -0.361 | no |
| red_zone_carry_share_prior4 | opportunity | horizon_specific | 64% | 1.10% | n/a | 0.405 | no |
| inside_5_carry_share_prior4 | opportunity | mechanism_specific | 50% | 1.03% | n/a | 0.336 | no |
| target_share_prior4 | opportunity | horizon_specific | 94% | 0.91% | n/a | 0.561 | no |
| target_share_prior4 | receiving_role | horizon_specific | 94% | 0.91% | n/a | 0.561 | no |
| backfield_competition_index_prior4 | competition | horizon_specific | 94% | 0.81% | n/a | -0.529 | no |
| carry_share_prior4 | opportunity | horizon_specific | 94% | 0.70% | n/a | 0.668 | no |
| xfp_residual_prior4 | regression | no_incremental_evidence | 47% | -0.06% | n/a | 0.019 | no |

## WR

Status counts: descriptive_not_incremental=3, horizon_specific=2, insufficient_coverage=1, mechanism_specific=1, no_incremental_evidence=2

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| receiving_competitor_count | competition | descriptive_not_incremental | 100% | 0.14% | n/a | -0.216 | no |
| target_share_prior4 | opportunity | horizon_specific | 94% | -0.68% | n/a | 0.692 | no |
| receiving_competition_index_prior4 | competition | mechanism_specific | 94% | -0.69% | n/a | -0.438 | no |
| red_zone_target_share_prior4 | opportunity | descriptive_not_incremental | 45% | -1.02% | n/a | 0.208 | no |
| opportunity_xfp_realized_prior4 | regression | descriptive_not_incremental | 47% | -1.13% | n/a | 0.694 | no |
| pfr_receiving_drop_pct_prior4 | conversion | no_incremental_evidence | 73% | -1.22% | n/a | 0.099 | no |
| offense_snap_share_prior4 | opportunity | horizon_specific | 81% | -1.38% | n/a | 0.643 | no |
| xfp_residual_prior4 | regression | no_incremental_evidence | 47% | -1.40% | n/a | 0.083 | no |

## TE

Status counts: descriptive_not_incremental=4, horizon_specific=3, insufficient_coverage=1, mechanism_specific=1

| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |
|---|---|---|---:|---:|---|---:|---|
| receiving_competitor_count | competition | descriptive_not_incremental | 100% | -0.24% | n/a | -0.207 | no |
| receiving_competition_index_prior4 | competition | horizon_specific | 93% | -0.54% | n/a | -0.346 | no |
| target_share_prior4 | opportunity | horizon_specific | 93% | -0.55% | n/a | 0.641 | no |
| pfr_receiving_drop_pct_prior4 | conversion | descriptive_not_incremental | 74% | -0.97% | n/a | 0.143 | no |
| red_zone_target_share_prior4 | opportunity | mechanism_specific | 43% | -1.04% | n/a | 0.195 | no |
| offense_snap_share_prior4 | opportunity | horizon_specific | 79% | -1.30% | n/a | 0.583 | no |
| opportunity_xfp_realized_prior4 | regression | descriptive_not_incremental | 47% | -1.50% | n/a | 0.657 | no |
| xfp_residual_prior4 | regression | descriptive_not_incremental | 47% | -1.92% | n/a | 0.098 | no |

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
- RB target_share_prior4 → rest_of_season: mean improvement=1.11%
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

## Phase 4: model challengers

- QB ridge: mean ΔMAE=1.07%, CI low=None, diagnostic_only
- QB elastic: mean ΔMAE=1.02%, CI low=None, diagnostic_only
- QB partial_pool: mean ΔMAE=1.60%, CI low=None, diagnostic_only
- QB histgb: mean ΔMAE=3.14%, CI low=None, diagnostic_only
- RB ridge: mean ΔMAE=1.63%, CI low=None, diagnostic_only
- RB elastic: mean ΔMAE=1.63%, CI low=None, diagnostic_only
- RB partial_pool: mean ΔMAE=1.56%, CI low=None, diagnostic_only
- RB histgb: mean ΔMAE=2.67%, CI low=None, diagnostic_only
- WR ridge: mean ΔMAE=0.12%, CI low=None, diagnostic_only
- WR elastic: mean ΔMAE=0.13%, CI low=None, diagnostic_only
- WR partial_pool: mean ΔMAE=-0.03%, CI low=None, diagnostic_only
- WR histgb: mean ΔMAE=0.54%, CI low=None, diagnostic_only
- TE ridge: mean ΔMAE=-0.58%, CI low=None, diagnostic_only
- TE elastic: mean ΔMAE=-0.51%, CI low=None, diagnostic_only
- TE partial_pool: mean ΔMAE=-0.48%, CI low=None, diagnostic_only
- TE histgb: mean ΔMAE=0.95%, CI low=None, diagnostic_only

## Phase 5: conditional effects

- QB rush_x_goal: diagnostic_conditional_signal, incremental over main effects=-0.02%

## Phase 6: highest-priority data expansion

- RB opportunity_change_score_prior1: improve_source_coverage (priority 67.42)
- TE opportunity_change_score_prior1: improve_source_coverage (priority 64.97)
- QB xfp_residual_prior4: test_predefined_condition_or_accept_redundancy (priority 63.82)
- QB opportunity_xfp_realized_prior4: test_predefined_condition_or_accept_redundancy (priority 63.82)
- WR red_zone_target_share_prior4: test_predefined_condition_or_accept_redundancy (priority 63.78)
- TE opportunity_xfp_realized_prior4: test_predefined_condition_or_accept_redundancy (priority 63.31)
- RB opportunity_xfp_realized_prior4: test_predefined_condition_or_accept_redundancy (priority 63.19)
- WR opportunity_xfp_realized_prior4: test_predefined_condition_or_accept_redundancy (priority 63.14)
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
- RB target_share_prior4: route_to_best_horizon (priority 51.6)

## Phase 7: production gate

No feature or challenger is auto-activated by this audit. `eligible_for_manual_consumer_integration` means only that the challenger cleared the same robust chronological gate and may be wired into a downstream model in a separate, revalidated change.
