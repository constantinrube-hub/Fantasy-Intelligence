"""Meaningful scoring and comparison boundary tests using known outcomes."""
from copy import deepcopy
from math import isclose, sqrt
from paired_forecast_metrics import compare, metrics, spearman
from strict_sleeper_baseline import audit_score


def main():
    assert audit_score({'rec': 0}, {'rec': 1}, 'RB')['points'] == 0
    assert not audit_score({}, {'rec': 1}, 'RB')['exact']
    assert audit_score({'rec': 3}, {'rec': 1, 'bonus_rec_te': 0.5}, 'TE')['points'] == 4.5
    assert audit_score({'rec': 3}, {'rec': 1, 'bonus_rec_te': 0.5}, 'RB')['points'] == 3
    assert audit_score({'passing_interceptions': 2}, {'pass_int': -2}, 'QB')['points'] == -4
    for stats, scoring in [({'rec': 2, 'receptions': 3}, {'rec': 1}),
                           ({'rec': float('nan')}, {'rec': 1}),
                           ({'rec': True}, {'rec': 1}), ({'rec': 2}, {'rec': float('inf')}),
                           ({'mystery': 1}, {'mystery': 1}),
                           ({'bonus_rush_yd_100': 1}, {'bonus_rush_yd_100': 3}),
                           ({'pts_ppr': 10}, {'rec': 1})]:
        assert not audit_score(stats, scoring, 'RB')['exact']
    rows = [{'fie_mean': 2, 'sleeper_mean': 1, 'realized_points': 0},
            {'fie_mean': 4, 'sleeper_mean': 5, 'realized_points': 4}]
    result = metrics(rows)
    assert result['fie']['mae'] == 1 and isclose(result['fie']['rmse'], sqrt(2))
    assert result['paired_mae_delta_fie_minus_sleeper'] == 0
    assert spearman([1, 1, 3], [2, 2, 5]) == 1
    assert spearman([1, 1], [2, 3]) is None and metrics([])['fie'] is None
    candidate = {'captured_player_id': 'a', 'projection_evidence': {'model_id': 'M9', 'model_version': 'v1'}}
    capture = {'leagues': [{'league_id': '1', 'evaluation_input': {'active_candidates': [candidate],
        'fie_forecast_artifacts': {k: {'status': 'BOUND', 'sha256': 'a'*64} for k in ('M4','M5','M6')}}}]}
    evaluation = {'leagues': [{'league_id': '1', 'status': 'READY', 'capture_evidence': {'scoring_signature': 'one'},
        'paired_projection_rows': [{**rows[0], 'captured_player_id': 'a', 'fie_weekly_activation_eligible': True}]}]}
    baseline = {'refresh_source_bindings': [{'league_id': '1', 'status': 'REFRESH_PROJECTION_STATS_BOUND_TO_ARCHIVE'}],
                'strict_scoring_rows': [{'league_id': '1', 'captured_player_id': 'a', 'exact': True,
                                        'captured_value_reproduced': True}]}
    assert compare(capture,evaluation,baseline)['cohorts']['exact']['rows'] == 1
    for altered in ({}, {'strict_scoring_rows': baseline['strict_scoring_rows']},
                    {'refresh_source_bindings': baseline['refresh_source_bindings']}):
        report = compare(capture,evaluation,altered)
        assert report['cohorts']['exact']['rows'] == 0 and report['cohorts']['descriptive']['rows'] == 1
    changed = deepcopy(capture)
    changed['leagues'][0]['evaluation_input']['active_candidates'][0]['projection_evidence'] = {}
    assert compare(changed,evaluation,baseline)['exact_rejection_counts']['FIE_MODEL_IDENTITY_MISSING'] == 1
    evaluation['leagues'][0]['paired_projection_rows'] *= 2
    try:
        compare(capture,evaluation,baseline)
        raise AssertionError('duplicate accepted')
    except ValueError:
        pass
    print('PASS strict baseline scoring, paired errors, tied ranks and independent evidence gates')


if __name__ == '__main__':
    main()
