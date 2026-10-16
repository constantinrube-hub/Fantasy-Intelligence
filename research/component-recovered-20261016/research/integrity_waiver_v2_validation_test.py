"""Calendar leakage, nested selection, missingness and blocked activation."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from unittest.mock import patch

from build_waiver_v2_label_batch import label_frame
from waiver_v2_validation import (
    FULL, TARGET, POLICY, SCHEMA, block_interval, build, evaluate, features, fit, keyed,
    metrics, pattern_keys, policy, predict, ranking, select, verified,
)
from build_waiver_v2_label_batch import digest
from validate_waiver_v2_validation import equivalent, validate


def reject(action):
    try:
        action()
    except (ValueError, AssertionError):
        return
    raise AssertionError('Invalid validation source accepted')


def fixture():
    rows, stats = [], []
    for year in policy()['seasons']:
        for player in range(36):
            for week in range(1, 19):
                key = {'canonical_player_id': f'p{player:02d}', 'season': year, 'week': week}
                points = float(5 + player/3 + np.sin(week+player)*2 + week/4)
                rows.append({**key, 'position_model': 'WR', 'team': 'T', 'scoring_signature': 'sig',
                             'fantasy_points_exact': points, 'outcome_complete': True, 'exact_scoring': True,
                             'outcome_status': 'COMPLETE_EXACT'})
                stats.append({**key, 'targets': float(2+player%7), 'receiving_yards': float(week+player)})
    return label_frame(pd.DataFrame(rows), 'sig', policy()['seasons']), pd.DataFrame(stats)


def main():
    contract = policy()
    outcomes, stats = fixture()
    past = features(outcomes, stats, 'WR')
    assert TARGET not in past and FULL not in past and 'outcome_complete' not in past
    assert past[past.week == 1].fp_history_count.eq(1).all()
    assert past[(past.season == 2021) & (past.week == 1)].fp_history_count.eq(1).all()
    # Future source/label changes cannot change a W feature or universe.
    changed = outcomes.copy()
    changed.loc[changed.week > 5, 'fantasy_points_exact'] = 100000
    changed[TARGET] = -99999
    future_stats = stats.copy()
    future_stats.loc[future_stats.week > 5, 'targets'] = 50000
    future = features(changed, future_stats, 'WR')
    pd.testing.assert_frame_equal(past[past.week <= 5].reset_index(drop=True), future[future.week <= 5].reset_index(drop=True))
    # Sparse calendar history does not reach back to the fifth week or appearances.
    sparse = outcomes[~((outcomes.canonical_player_id == 'p00') & outcomes.week.isin([3, 4]))]
    row = features(sparse, stats, 'WR').query("canonical_player_id == 'p00' and season == 2025 and week == 5").iloc[0]
    assert row.fp_history_count == 2 and row.fp_mask == 9
    assert row.fp_prior_4 == outcomes.query("canonical_player_id == 'p00' and season == 2025 and week in [2, 5]").fantasy_points_exact.mean()
    # Missing role fields stay missing; a confirmed score zero invents no raw stat.
    absent = stats[~((stats.canonical_player_id == 'p00') & stats.week.isin([2, 3, 4, 5]))]
    row = features(outcomes, absent, 'WR').query("canonical_player_id == 'p00' and season == 2025 and week == 5").iloc[0]
    assert row.fp_history_count == 4 and row.role_history_count == 0 and not row.feature_admissible
    reject(lambda: features(pd.concat([outcomes, outcomes.iloc[:1]]), stats, 'WR'))
    collision = stats.copy(); collision.loc[1, 'canonical_player_id'] = ' p00 '
    reject(lambda: keyed(pd.concat([stats, collision.iloc[:1]])))
    # An unsupported missingness mask abstains; required inputs are not imputed.
    frame = past.merge(outcomes[['canonical_player_id','season','week',TARGET,FULL]], on=['canonical_player_id','season','week'])
    frame['label_complete'] = frame[FULL]
    choice = {'features': 'trend', 'history': 2, 'alpha': 10.0}
    train = frame[frame.season == 2018]
    spec = fit(train, choice, contract)
    assert spec is not None
    unsupported = frame.query('season == 2021 and week == 5').copy()
    unsupported['fp_mask'] = 3
    assert not np.isfinite(predict(spec, unsupported)).any()
    no_role = frame.query('season == 2021 and week == 5').copy()
    no_role['role_prior_4'] = np.nan; no_role['feature_admissible'] = False
    assert not np.isfinite(predict(spec, no_role)).any()
    # Optional imputation/scaling parameters come exclusively from train.
    missing = train.copy(); missing.loc[missing.index[::3], 'yards_prior_4'] = np.nan
    imputed = fit(missing, choice, contract)
    expected_median = missing[missing.feature_admissible & missing.label_complete].yards_prior_4.median()
    assert imputed['medians'][2] == expected_median
    # Changing an outer target cannot select another candidate for that fold.
    chosen, candidates = select(frame[frame.season < 2022], contract)
    altered = outcomes.copy()
    altered.loc[altered.season >= 2022, TARGET] = 1234567.0
    base_result, base_predictions, base_models = evaluate(past, outcomes)
    other_result, other_predictions, other_models = evaluate(past, altered)
    assert base_models[0] == other_models[0]
    pd.testing.assert_series_equal(base_predictions[base_predictions.season == 2022].prediction.reset_index(drop=True),
                                   other_predictions[other_predictions.season == 2022].prediction.reset_index(drop=True))
    assert chosen == base_result['folds'][0]['selected_choice']
    assert all(fold['season'] > max(fold['training_seasons']) for fold in base_result['folds'])
    assert [fold['season'] for fold in base_result['folds']] == [2022, 2023, 2024, 2025]
    assert all(not base_result[field] for field in ['forecast_eligible','ranking_eligible','recommendation_eligible','transaction_eligible','activation_eligible'])
    assert 'BLOCKED_OUTCOME_SELECTION_BIAS' in base_result['eligibility_blockers']
    # Future-label omissions change evaluable denominators, never predictions.
    dropped = outcomes.copy(); dropped.loc[dropped.season == 2022, FULL] = False
    missed_result, missed_predictions, _ = evaluate(past, dropped)
    pd.testing.assert_series_equal(base_predictions.query('season == 2022').prediction.reset_index(drop=True),
                                   missed_predictions.query('season == 2022').prediction.reset_index(drop=True))
    assert missed_result['folds'][0]['covered_paired_rows'] == 0
    assert missed_result['folds'][0]['predictions_without_target'] > 0
    assert 'BLOCKED_INSUFFICIENT_VALID_OUTER_FOLDS' in missed_result['research_signal_blockers']
    ci = block_interval([1, 2, 3, 4])
    assert ci['resamples'] == 256 and ci['block_count'] == 4
    assert ci['independent_sign_sensitivity_p_one_sided'] == 1/16
    assert ci['family_adjusted_percentile'][0] <= ci['ordinary_95_percentile'][0]
    assert not ci['calibrated_population_confidence']
    assert block_interval([1]) is None
    # Constant ranks stay unknown and ties use stable canonical IDs.
    paired = base_predictions.query('season == 2022 and week == 5').copy()
    paired['prediction'] = 10.0
    ranked = ranking(paired)
    assert ranked['cutoffs'][0]['model_spearman'] is None
    assert ranked == ranking(paired.sample(frac=1, random_state=9))
    reject(lambda: metrics(paired.assign(prediction=np.nan)))
    with TemporaryDirectory() as td:
        root = Path(td)
        reject(lambda: build(root/'absent', root))
        reject(lambda: verified({'path': str(root/'absent'), 'sha256': 'wrong'}))
        invalid = root/'source.json'; invalid.write_text(json.dumps({'schema': 'wrong'}))
        reject(lambda: build(invalid, root/'output'))
        assert not (root/'output').exists()
        with patch('waiver_v2_validation.POLICY', invalid):
            reject(policy)
        # Replay a complete, small artifact graph. A reviewed report hash alone
        # is insufficient when a model or metric disagrees with the source rows.
        artifact = root/'artifact'; artifact.mkdir(); sources = artifact/'sources'; sources.mkdir()
        def binding(path):
            return {'path': str(path), 'sha256': digest(path)}
        source_labels = sources/'labels.csv.gz'; outcomes.to_csv(source_labels,index=False)
        source_stats = sources/'stats.csv.gz'; stats.to_csv(source_stats,index=False)
        schedule = sources/'schedule.csv.gz'
        pd.DataFrame([{'season': s, 'week': 18} for s in contract['seasons']]).to_csv(schedule,index=False)
        roster = sources/'roster.csv.gz'; outcomes[['canonical_player_id','season','week']].to_csv(roster,index=False)
        small_labels = outcomes[outcomes.week <= 15]
        small_features = keyed(past).loc[keyed(small_labels).index].reset_index(drop=True)
        small_result, small_predictions, small_models = evaluate(small_features, small_labels)
        stored_features = artifact/'features.csv.gz'; small_features.to_csv(stored_features,index=False)
        stored_predictions = artifact/'predictions.csv.gz'; small_predictions.to_csv(stored_predictions,index=False)
        stored_models = artifact/'models.json'; stored_models.write_text(json.dumps(small_models))
        unit = {'scoring_signature':'sig','position':'WR','source_labels':binding(source_labels),
                'source_inputs':{'player_stats':binding(source_stats),'team_schedule':binding(schedule),'weekly_roster':binding(roster)},
                'artifacts':{'features':binding(stored_features),'predictions':binding(stored_predictions),'fold_models':binding(stored_models)},**small_result}
        snapshot = {'schema':SCHEMA,'activation_eligible':False,'methodology':{'sha256':digest(POLICY)},
                    'builder_sha256':digest(Path(__file__).with_name('waiver_v2_validation.py')),'units':[unit],
                    'eligible_forecast_units':0,'research_signal_units':int(small_result['research_signal_passed'])}
        report_path = artifact/'report.json'; report_path.write_text(json.dumps(snapshot))
        with patch('validate_waiver_v2_validation.policy',return_value={**contract,'signatures':['sig'],'positions':['WR']}):
            assert validate(report_path,digest(report_path))['status']=='PASS_RESEARCH_ARTIFACT_REPLAY'
            reject(lambda: validate(report_path,'bad-report-hash'))
            snapshot['units'][0]['folds'][0]['covered_metrics']['model_mae'] += 1
            report_path.write_text(json.dumps(snapshot))
            reject(lambda: validate(report_path,digest(report_path)))
        reject(lambda: equivalent(False,0.0))
    print('PASS waiver-v2 frozen validation: calendar/PIT guards, nested selection, masks, temporal blocks, target attrition and no activation')


if __name__ == '__main__':
    main()
