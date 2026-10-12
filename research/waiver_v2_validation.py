"""Frozen, source-bound offline waiver experiment. Never an activation owner."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.stats import rankdata

from build_waiver_v2_label_batch import digest, label_frame
from waiver_v2_contract import _true
from waiver_v2_exact_replay_closure import build_exact_replay_closure

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'config/waiver-v2-statistical-methodology.json'
FROZEN_POLICY_SHA256 = '47d67da49e004114b26c9b55fab3c605baf6c698469014a19b5061baa4c9993b'
KEYS = ['canonical_player_id', 'season', 'week']
TARGET = 'fp_next3_weeks_exact'
FULL = 'fp_next3_weeks_full_horizon'
SCHEMA = 'fie-waiver-v2-nested-validation-v1'


def policy():
    if digest(POLICY) != FROZEN_POLICY_SHA256:
        raise ValueError('WAIVER_VALIDATION_METHOD_CHANGED_REQUIRES_NEW_VERSION')
    return json.loads(POLICY.read_text())


def verified(binding):
    path = Path(binding['path'])
    if not path.is_file() or digest(path) != binding['sha256']:
        raise ValueError('WAIVER_VALIDATION_SOURCE_HASH_MISMATCH')
    return path


def keyed(frame):
    result = frame.copy()
    if result[KEYS].isna().any().any():
        raise ValueError('WAIVER_VALIDATION_MISSING_IDENTITY')
    result['canonical_player_id'] = result.canonical_player_id.astype(str).str.strip()
    if result.canonical_player_id.isin(['', 'nan', 'None']).any():
        raise ValueError('WAIVER_VALIDATION_MISSING_IDENTITY')
    for column in ['season', 'week']:
        values = pd.to_numeric(result[column], errors='raise')
        if not np.isfinite(values).all() or (values % 1 != 0).any():
            raise ValueError('WAIVER_VALIDATION_INVALID_CALENDAR_IDENTITY')
        result[column] = values.astype(int)
    if result.duplicated(KEYS).any():
        raise ValueError('WAIVER_VALIDATION_DUPLICATE_IDENTITY')
    return result.set_index(KEYS, drop=False)


def numeric(series):
    values = pd.to_numeric(series, errors='coerce').to_numpy(dtype=float)
    return np.where(np.isfinite(values), values, np.nan)


def composite(frame, columns):
    if any(column not in frame for column in columns):
        return np.full(len(frame), np.nan)
    values = np.column_stack([numeric(frame[column]) for column in columns])
    return np.where(np.isfinite(values).all(axis=1), values.sum(axis=1), np.nan)


def observed_mean(values):
    counts = np.isfinite(values).sum(axis=1)
    return np.divide(np.nansum(values, axis=1), counts,
                     out=np.full(len(values), np.nan), where=counts > 0)


def features(outcomes, stats, position, contract=None):
    """Build all W roster opportunities before reading future label columns."""
    contract = contract or policy()
    ledger = keyed(outcomes)
    raw = keyed(stats)
    base = ledger[ledger.position_model == position].copy().reset_index(drop=True)
    valid = ledger.outcome_complete.map(_true) & ledger.exact_scoring.map(_true)
    points = pd.Series(np.where(valid, numeric(ledger.fantasy_points_exact), np.nan), index=ledger.index)
    role = pd.Series(composite(raw, contract['role_columns'][position]), index=raw.index)
    yards = pd.Series(composite(raw, contract['yardage_columns'][position]), index=raw.index)
    past = {'fp': [], 'role': [], 'yards': []}
    for offset in contract['feature_window_offsets']:
        lookup = pd.MultiIndex.from_arrays([base.canonical_player_id, base.season, base.week + offset], names=KEYS)
        for name, source in [('fp', points), ('role', role), ('yards', yards)]:
            past[name].append(source.reindex(lookup).to_numpy(dtype=float))
    for name, columns in past.items():
        matrix = np.column_stack(columns)
        count = np.isfinite(matrix).sum(axis=1)
        base[f'{name}_prior_4'] = observed_mean(matrix)
        base[f'{name}_history_count'] = count
        base[f'{name}_mask'] = (np.isfinite(matrix) * (2 ** np.arange(4))).sum(axis=1).astype(int)
        if name != 'yards':
            base[f'{name}_recent_delta'] = observed_mean(matrix[:, :2]) - observed_mean(matrix[:, 2:])
    base['history_count'] = base[['fp_history_count', 'role_history_count']].min(axis=1).astype(int)
    base['feature_admissible'] = (base.history_count >= contract['minimum_history']) & np.isfinite(base.fp_prior_4) & np.isfinite(base.role_prior_4)
    # The target is deliberately absent from this feature frame. Evaluation
    # attaches it only after fitting and issuing all candidate predictions.
    retained = KEYS + ['position_model', 'team', 'scoring_signature']
    retained += [column for column in base if column.endswith(('_prior_4', '_history_count', '_mask', '_recent_delta'))]
    return base[retained + ['history_count', 'feature_admissible']].sort_values(KEYS).reset_index(drop=True)


def pattern_keys(frame, columns):
    observed = np.isfinite(frame[columns].to_numpy(dtype=float))
    return [f'{int(fp):02x}:{int(role):02x}:' + ''.join('1' if bit else '0' for bit in bits)
            for fp, role, bits in zip(frame.fp_mask, frame.role_mask, observed)]


def fit(frame, choice, contract):
    train = frame[frame.feature_admissible & (frame.history_count >= choice['history']) & frame.label_complete]
    if len(train) < contract['minimum_training_rows']:
        return None
    columns = contract['feature_sets'][choice['features']]
    values = train[columns].to_numpy(dtype=float)
    medians = np.array([float(np.median(column[np.isfinite(column)])) if np.isfinite(column).any() else 0.0
                        for column in values.T])
    filled = np.where(np.isfinite(values), values, medians)
    # Fixed indicators also exist for fully observed columns; no test-dependent
    # change in feature dimensionality or whole-panel preprocessing.
    design = np.column_stack([filled, ~np.isfinite(values)]).astype(float)
    means = design.mean(axis=0)
    scales = design.std(axis=0)
    scales[scales == 0] = 1
    scaled = (design - means) / scales
    target = train[TARGET].to_numpy(dtype=float)
    intercept = float(target.mean())
    coefficients = np.linalg.solve(scaled.T @ scaled + choice['alpha'] * np.eye(scaled.shape[1]),
                                   scaled.T @ (target - intercept))
    support = pd.Series(pattern_keys(train, columns)).value_counts()
    patterns = sorted(support[support >= contract['minimum_pattern_training_rows']].index.tolist())
    return {'choice': choice, 'columns': columns, 'medians': medians.tolist(), 'means': means.tolist(),
            'scales': scales.tolist(), 'coefficients': coefficients.tolist(), 'intercept': intercept,
            'supported_patterns': patterns, 'training_rows': len(train),
            'training_seasons': sorted(int(year) for year in train.season.unique())}


def predict(spec, frame):
    values = frame[spec['columns']].to_numpy(dtype=float)
    valid = frame.feature_admissible.to_numpy() & (frame.history_count.to_numpy() >= spec['choice']['history'])
    support = set(spec['supported_patterns'])
    valid &= np.array([key in support for key in pattern_keys(frame, spec['columns'])], dtype=bool)
    filled = np.where(np.isfinite(values), values, np.array(spec['medians']))
    design = np.column_stack([filled, ~np.isfinite(values)]).astype(float)
    projections = ((design - np.array(spec['means'])) / np.array(spec['scales'])) @ np.array(spec['coefficients']) + spec['intercept']
    return np.where(valid & np.isfinite(projections), projections, np.nan)


def metrics(frame):
    if frame.empty:
        return None
    y = frame[TARGET].to_numpy(dtype=float)
    baseline = frame.fp_prior_4.to_numpy(dtype=float)
    prediction = frame.prediction.to_numpy(dtype=float)
    if not (np.isfinite(y).all() and np.isfinite(baseline).all() and np.isfinite(prediction).all()):
        raise ValueError('WAIVER_VALIDATION_NONFINITE_PAIRED_METRIC')
    bmae, mae = float(np.abs(y-baseline).mean()), float(np.abs(y-prediction).mean())
    brmse, rmse = float(np.sqrt(np.mean((y-baseline)**2))), float(np.sqrt(np.mean((y-prediction)**2)))
    return {'rows': len(frame), 'weeks': int(frame.week.nunique()), 'baseline_mae': bmae, 'model_mae': mae,
            'mae_gain': bmae-mae, 'relative_mae_lift': (bmae-mae)/bmae if bmae > 0 else None,
            'baseline_rmse': brmse, 'model_rmse': rmse, 'rmse_gain': brmse-rmse}


def select(training, contract):
    """Only earlier seasons participate; never accepts an outer test frame."""
    seasons = sorted(int(year) for year in training.season.unique())
    candidates = []
    for name, history, alpha in itertools.product(contract['feature_sets'], contract['coverage_thresholds'], contract['ridge_alphas']):
        choice = {'features': name, 'history': history, 'alpha': alpha}
        folds = []
        for year in seasons[1:]:
            earlier = training[training.season < year]
            held = training[(training.season == year) & training.feature_admissible & training.label_complete].copy()
            spec = fit(earlier, choice, contract)
            if spec is None or len(held) < contract['minimum_validation_rows'] or held.week.nunique() < contract['minimum_validation_weeks']:
                folds.append({'season': year, 'status': 'BLOCKED_INNER_SAMPLE'})
                continue
            values = predict(spec, held)
            covered = np.isfinite(values)
            held['prediction'] = np.where(covered, values, held.fp_prior_4)
            folds.append({'season': year, 'status': 'OK', 'coverage': float(covered.mean()),
                          'covered_rows': int(covered.sum()), 'paired_fallback_metrics': metrics(held)})
        admissible = bool(folds) and all(row['status'] == 'OK' and row['coverage'] >= contract['minimum_inner_coverage'] for row in folds)
        candidates.append({'choice': choice, 'inner_folds': folds, 'admissible': admissible,
                           'selection_gain': float(np.mean([row['paired_fallback_metrics']['mae_gain'] for row in folds])) if admissible else None,
                           'selection_coverage': float(np.mean([row['coverage'] for row in folds])) if admissible else None})
    allowed = [candidate for candidate in candidates if candidate['admissible']]
    if not allowed:
        return None, candidates
    selected = max(allowed, key=lambda row: (row['selection_gain'], row['selection_coverage'],
                   -list(contract['feature_sets']).index(row['choice']['features']), -row['choice']['history'], row['choice']['alpha']))
    return selected['choice'], candidates


def block_interval(gains, family_size=12):
    values = np.asarray(gains, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        return None
    if len(values) > 7:
        raise ValueError('WAIVER_VALIDATION_EXHAUSTIVE_BLOCK_LIMIT')
    samples = np.array([np.mean(values[list(index)]) for index in itertools.product(range(len(values)), repeat=len(values))])
    ordinary = np.quantile(samples, [0.025, 0.975]).tolist()
    adjusted = np.quantile(samples, [0.025/family_size, 1-0.025/family_size]).tolist()
    wins = int((values > 0).sum())
    return {'block_count': len(values), 'resamples': len(samples), 'equal_season_mae_gain': float(values.mean()),
            'ordinary_95_percentile': ordinary, 'family_adjusted_percentile': adjusted,
            'family_size': family_size, 'leave_one_season_out_means': [float(np.delete(values, i).mean()) for i in range(len(values))],
            'positive_seasons': wins, 'independent_sign_sensitivity_p_one_sided': sum(math.comb(len(values), k) for k in range(wins, len(values)+1))/2**len(values),
            'calibrated_population_confidence': False}


def ranking(frame):
    rows = []
    for (season, week), group in frame.groupby(['season', 'week']):
        if len(group) < 4:
            continue
        y, m, b = [group[column].to_numpy(dtype=float) for column in [TARGET, 'prediction', 'fp_prior_4']]
        def correlation(a):
            left, right = rankdata(a), rankdata(y)
            return float(np.corrcoef(left, right)[0, 1]) if np.ptp(left) and np.ptp(right) else None
        def top(column, n):
            return group.sort_values([column, 'canonical_player_id'], ascending=[False, True]).head(n)
        n = math.ceil(len(group)/4)
        truth = set(top(TARGET, n).canonical_player_id)
        mc, bc = correlation(m), correlation(b)
        rows.append({'season': int(season), 'week': int(week), 'candidates': len(group),
                     'model_spearman': mc, 'baseline_spearman': bc,
                     'spearman_gain': mc-bc if mc is not None and bc is not None else None,
                     'model_top_quartile_precision': len(set(top('prediction', n).canonical_player_id) & truth)/n,
                     'baseline_top_quartile_precision': len(set(top('fp_prior_4', n).canonical_player_id) & truth)/n,
                     'model_top_one_regret': float(y.max()-top('prediction', 1)[TARGET].iloc[0]),
                     'baseline_top_one_regret': float(y.max()-top('fp_prior_4', 1)[TARGET].iloc[0])})
    fields = ['spearman_gain', 'model_top_quartile_precision', 'baseline_top_quartile_precision', 'model_top_one_regret', 'baseline_top_one_regret']
    return {'domain': 'CONDITIONAL_ALL_PLAYER_DIAGNOSTIC', 'cutoffs': rows,
            'means': {field: float(np.mean([row[field] for row in rows if row[field] is not None]))
                      if any(row[field] is not None for row in rows) else None for field in fields}}


def evaluate(feature_frame, labels, contract=None):
    contract = contract or policy()
    target = keyed(labels)[KEYS + [TARGET, FULL]].reset_index(drop=True)
    target['label_complete'] = target[FULL].map(_true) & np.isfinite(numeric(target[TARGET]))
    frame = feature_frame.merge(target[KEYS+[TARGET, 'label_complete']], on=KEYS, how='left', validate='one_to_one')
    frame['label_complete'] = frame.label_complete.fillna(False).astype(bool)
    years = sorted(int(year) for year in frame.season.unique())
    folds, prediction_frames, all_models = [], [], []
    for year in years[contract['minimum_outer_training_seasons']:]:
        training = frame[frame.season < year].copy()
        held_features = feature_frame[feature_frame.season == year].copy()
        choice, candidates = select(training, contract)
        spec = fit(training, choice, contract) if choice is not None else None
        all_models.append({'season': year, 'selection': candidates, 'fitted_spec': spec})
        # Predictions are issued before target join, including missing labels.
        held_features['prediction'] = predict(spec, held_features) if spec is not None else np.nan
        held = held_features.merge(target[KEYS+[TARGET, 'label_complete']], on=KEYS, how='left', validate='one_to_one')
        held['label_complete'] = held.label_complete.fillna(False).astype(bool)
        held['prediction_status'] = np.where(np.isfinite(held.prediction), 'RESEARCH_FORECAST', 'ABSTAIN_UNSUPPORTED_FEATURES_OR_MODEL')
        prediction_frames.append(held)
        base = held[held.feature_admissible & held.label_complete]
        covered = base[np.isfinite(base.prediction)]
        covered_metrics = metrics(covered)
        fallback = base.copy()
        fallback['prediction'] = fallback.prediction.fillna(fallback.fp_prior_4)
        coverage = len(covered)/len(base) if len(base) else 0.0
        strata = {str(count): metrics(rows) for count, rows in covered.groupby('history_count')}
        valid = (spec is not None and len(spec['training_seasons']) >= contract['minimum_outer_training_seasons'] and covered_metrics is not None and
                 len(covered) >= contract['minimum_validation_rows'] and
                 covered.week.nunique() >= contract['minimum_validation_weeks'])
        folds.append({'season': year, 'training_seasons': sorted(int(s) for s in training.season.unique()),
                      'status': 'OK' if valid else 'BLOCKED_OUTER_SAMPLE_OR_SELECTION',
                      'selected_choice': choice, 'roster_decision_rows': len(held),
                      'feature_admissible_rows': int(held.feature_admissible.sum()),
                      'full_label_rows': int(held.label_complete.sum()), 'base_paired_rows': len(base),
                      'covered_paired_rows': len(covered), 'covered_fraction': coverage,
                      'missing_target_among_feature_admissible': int((held.feature_admissible & ~held.label_complete).sum()),
                      'predictions_without_target': int((np.isfinite(held.prediction) & ~held.label_complete).sum()),
                      'covered_metrics': covered_metrics, 'fallback_policy_metrics': metrics(fallback),
                      'coverage_strata': strata, 'ranking': ranking(covered)})
    good = [fold for fold in folds if fold['status'] == 'OK']
    uncertainty = block_interval([fold['covered_metrics']['mae_gain'] for fold in good], contract['uncertainty']['comparison_family_size'])
    gate = contract['research_signal']
    blockers = []
    if len(good) < contract['minimum_outer_folds'] or len(good) != len(folds):
        blockers.append('BLOCKED_INSUFFICIENT_VALID_OUTER_FOLDS')
    if not good or any(fold['covered_metrics']['mae_gain'] <= 0 for fold in good):
        blockers.append('BLOCKED_SEASON_MAE_STABILITY')
    lifts = [fold['covered_metrics']['relative_mae_lift'] for fold in good]
    mean_lift = float(np.mean(lifts)) if lifts and all(value is not None for value in lifts) else None
    if mean_lift is None or mean_lift < gate['minimum_equal_season_relative_mae_lift']:
        blockers.append('BLOCKED_PRACTICAL_MAE_LIFT')
    if not good or np.mean([fold['covered_metrics']['rmse_gain'] for fold in good]) <= 0:
        blockers.append('BLOCKED_RMSE_IMPROVEMENT')
    if uncertainty is None or uncertainty['family_adjusted_percentile'][0] <= 0:
        blockers.append('BLOCKED_DESCRIPTIVE_BLOCK_INTERVAL')
    if any(fold['covered_fraction'] < gate['minimum_covered_fraction_per_season'] or
           fold['covered_paired_rows'] < gate['minimum_covered_rows_per_season'] or
           (fold['covered_metrics'] or {}).get('weeks', 0) < gate['minimum_covered_weeks_per_season'] for fold in folds):
        blockers.append('BLOCKED_OUTER_COVERAGE')
    if any(values['relative_mae_lift'] is None or values['relative_mae_lift'] < -gate['maximum_stratum_relative_mae_regression']
           for fold in good for values in fold['coverage_strata'].values()
           if values is not None and values['rows'] >= gate['minimum_stratum_rows']):
        blockers.append('BLOCKED_MATERIAL_COVERAGE_STRATUM_REGRESSION')
    report = {'folds': folds, 'uncertainty': uncertainty, 'equal_season_relative_mae_lift': mean_lift,
              'research_signal_passed': not blockers, 'research_signal_blockers': blockers,
              'forecast_eligible': False, 'ranking_eligible': False, 'recommendation_eligible': False,
              'transaction_eligible': False, 'activation_eligible': False,
              'eligibility_blockers': contract['mandatory_eligibility_blockers'] + [contract['ranking_additional_blocker']]}
    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    return report, predictions, all_models


def replay_labels(label_report):
    report = json.loads(label_report.read_text())
    if report.get('schema') != 'fie-waiver-v2-label-batch-v1':
        raise ValueError('WAIVER_VALIDATION_LABEL_SCHEMA')
    batch_path = verified(report['batch_source'])
    closure = build_exact_replay_closure(batch_report_path=batch_path)
    batch = json.loads(batch_path.read_text())
    contract = policy()
    if sorted(report['requested_seasons']) != contract['seasons'] or sorted(batch['requested_seasons']) != contract['seasons']:
        raise ValueError('WAIVER_VALIDATION_UNREGISTERED_SEASONS')
    shared = batch['shared_source_run']
    for binding in shared['source_snapshot'].values():
        verified(binding)
    for binding in shared['adapter_receipt']['outputs'].values():
        verified(binding)
    for name, expected in report['builder_sha256'].items():
        if digest(Path(__file__).with_name(name)) != expected:
            raise ValueError('WAIVER_VALIDATION_LABEL_BUILDER_CHANGED')
    parent = verified(report['validation_policy'])
    if parent.resolve() != (ROOT/'config/offensive-waiver-eligibility-design.json').resolve():
        raise ValueError('WAIVER_VALIDATION_WRONG_PARENT_CONTRACT')
    entries = {entry['scoring_signature']: entry for entry in report['profiles']}
    if len(entries) != len(report['profiles']):
        raise ValueError('WAIVER_VALIDATION_DUPLICATE_SIGNATURE')
    source_profiles = {entry['scoring_signature']: entry for entry in closure['profiles']}
    prepared = []
    for signature in contract['signatures']:
        entry, source = entries[signature], source_profiles[signature]
        if not all(source['position_exact_replay'].values()):
            raise ValueError('WAIVER_VALIDATION_UNSUPPORTED_SIGNATURE')
        if entry['source_outcome_ledger'] != source['outcome_ledger'] or entry['source_outcome_report'] != source['outcome_report']:
            raise ValueError('WAIVER_VALIDATION_LABEL_SOURCE_BINDING_MISMATCH')
        ledger = pd.read_csv(verified(source['outcome_ledger']))
        labels = pd.read_csv(verified(entry['labels']))
        expected = label_frame(ledger, signature, contract['seasons'])
        # CSV round-trips preserve booleans; allow floating serialization noise.
        pd.testing.assert_frame_equal(labels.reset_index(drop=True), expected.reset_index(drop=True),
                                      check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
        receipt = json.loads(verified(source['outcome_report']).read_text())
        for binding in receipt['inputs'].values():
            if binding is not None:
                verified(binding)
        for name in ['player_stats', 'weekly_roster', 'team_schedule']:
            if receipt['inputs'][name] != shared['adapter_receipt']['outputs'][name]:
                raise ValueError('WAIVER_VALIDATION_ADAPTER_BINDING_MISMATCH')
        stats = pd.read_csv(verified(receipt['inputs']['player_stats']), low_memory=False)
        schedule = pd.read_csv(verified(receipt['inputs']['team_schedule']))
        last_weeks = schedule.groupby('season').week.max().to_dict()
        last = labels.season.map(last_weeks)
        if last.isna().any():
            raise ValueError('WAIVER_VALIDATION_MISSING_SCHEDULE_SEASON')
        decision_rows = labels[labels.week + contract['horizon_weeks'] <= last].copy()
        prepared.append((entry, decision_rows, stats, receipt['inputs']))
    return report, batch, prepared


def build(label_report, output_dir):
    if output_dir.exists():
        raise ValueError('WAIVER_VALIDATION_OUTPUT_MUST_BE_NEW')
    contract = policy()
    label_source, batch, prepared = replay_labels(label_report)
    # Validate every source before the first artifact is written.
    output_dir.mkdir(parents=True)
    units = []
    for entry, labels, stats, bindings in prepared:
        signature = entry['scoring_signature']
        for position in contract['positions']:
            full_outcomes = pd.read_csv(verified(entry['labels']))
            all_features = features(full_outcomes, stats, position, contract)
            allowed_keys = keyed(labels[labels.position_model == position]).index
            feature_frame = keyed(all_features).loc[allowed_keys].reset_index(drop=True)
            result, predictions, models = evaluate(feature_frame, labels, contract)
            prefix = output_dir / f'{signature}-{position}'
            paths = {}
            for name, frame in [('features', feature_frame), ('predictions', predictions)]:
                path = prefix.with_name(prefix.name + f'-{name}.csv.gz')
                frame.to_csv(path, index=False, compression={'method':'gzip', 'mtime':0})
                paths[name] = {'path': str(path), 'sha256': digest(path), 'rows': len(frame)}
            models_path = prefix.with_name(prefix.name + '-fold-models.json')
            models_path.write_text(json.dumps(models, indent=2, sort_keys=True, allow_nan=False)+'\n')
            paths['fold_models'] = {'path': str(models_path), 'sha256': digest(models_path)}
            units.append({'scoring_signature': signature, 'position': position, 'horizon_weeks': 3,
                          'source_labels': entry['labels'], 'source_inputs': bindings,
                          'artifacts': paths, **result})
    report = {'schema': SCHEMA, 'diagnostic_only': True, 'activation_eligible': False,
              'methodology': {'path': str(POLICY), 'sha256': digest(POLICY)},
              'label_batch': {'path': str(label_report), 'sha256': digest(label_report)},
              'source_batch': label_source['batch_source'],
              'raw_source_snapshot': batch['shared_source_run']['source_snapshot'],
              'builder_sha256': digest(Path(__file__)), 'requested_seasons': contract['seasons'],
              'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__},
              'units': units, 'unit_count': len(units), 'eligible_forecast_units': 0,
              'research_signal_units': sum(unit['research_signal_passed'] for unit in units),
              'limitations': ['Conditional observed-label evaluation; missing outcomes are never zero.',
                              'Historical source publication times and live feature parity remain unverified.',
                              'Four season-block intervals are descriptive, not calibrated confidence.',
                              'All-player ranking is not waiver free-agent or acquisition validation.']}
    (output_dir/'validation-report.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label-batch-report', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.label_batch_report, args.output_dir)
    print(json.dumps({'unit_count': report['unit_count'], 'research_signal_units': report['research_signal_units'],
                      'eligible_forecast_units': report['eligible_forecast_units']}, sort_keys=True))


if __name__ == '__main__':
    main()
