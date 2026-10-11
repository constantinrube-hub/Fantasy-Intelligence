"""Descriptive paired forecast errors; no inference or promotion authority."""
from __future__ import annotations

from collections import Counter, defaultdict
import math
from statistics import mean, median
from strict_sleeper_baseline import finite


def ranks(values):
    ordered = sorted(range(len(values)), key=values.__getitem__)
    output = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and values[ordered[stop]] == values[ordered[start]]:
            stop += 1
        for index in ordered[start:stop]:
            output[index] = (start + 1 + stop) / 2
        start = stop
    return output


def spearman(predicted, actual):
    if len(actual) < 2:
        return None
    x, y = ranks(predicted), ranks(actual)
    mx, my = mean(x), mean(y)
    covariance = sum((a-mx)*(b-my) for a, b in zip(x, y))
    divisor = math.sqrt(sum((a-mx)**2 for a in x) * sum((b-my)**2 for b in y))
    return covariance/divisor if divisor else None


def metrics(rows):
    if not rows:
        return {'rows': 0, 'fie': None, 'sleeper': None, 'paired_mae_delta_fie_minus_sleeper': None}
    actual = [row['realized_points'] for row in rows]
    output = {'rows': len(rows)}
    for owner in ('fie', 'sleeper'):
        predictions = [row[owner+'_mean'] for row in rows]
        errors = [p-a for p, a in zip(predictions, actual)]
        output[owner] = {'mae': mean(abs(e) for e in errors),
                         'rmse': math.sqrt(mean(e*e for e in errors)),
                         'bias_prediction_minus_actual': mean(errors),
                         'median_absolute_error': median(abs(e) for e in errors),
                         'spearman': spearman(predictions, actual)}
    output['paired_mae_delta_fie_minus_sleeper'] = output['fie']['mae'] - output['sleeper']['mae']
    return output


def compare(capture: dict, evaluation: dict, baseline: dict) -> dict:
    sources = {str(row['league_id']): row.get('evaluation_input') or {} for row in capture.get('leagues', [])}
    strict = {(str(row['league_id']), str(row['captured_player_id'])): row for row in baseline.get('strict_scoring_rows', [])}
    bindings = {str(row['league_id']): row['status'] for row in baseline.get('refresh_source_bindings', [])}
    cohorts = {'descriptive': [], 'exact': []}
    rejected, seen = Counter(), set()
    for league in evaluation.get('leagues', []):
        if league.get('status') != 'READY':
            continue
        lid = str(league['league_id'])
        source = sources.get(lid, {})
        candidates = {str(row['captured_player_id']): row for row in source.get('active_candidates', [])}
        artifacts = source.get('fie_forecast_artifacts') or {}
        bound = all(isinstance(artifacts.get(k), dict) and artifacts[k].get('status') == 'BOUND' and
                    isinstance(artifacts[k].get('sha256'), str) and len(artifacts[k]['sha256']) == 64 and
                    all(c in '0123456789abcdef' for c in artifacts[k]['sha256']) for k in ('M4', 'M5', 'M6'))
        for pair in league.get('paired_projection_rows', []):
            key = (lid, str(pair['captured_player_id']))
            if key in seen:
                raise ValueError('PAIRED_DUPLICATE_LEAGUE_PLAYER')
            seen.add(key)
            numbers = {k: finite(pair.get(k)) for k in ('fie_mean', 'sleeper_mean', 'realized_points')}
            if any(v is None for v in numbers.values()):
                rejected['NONFINITE_PAIR'] += 1
                continue
            evidence = (candidates.get(key[1]) or {}).get('projection_evidence') or {}
            row = {**pair, **numbers, 'league_id': lid,
                   'scoring_signature': (league.get('capture_evidence') or {}).get('scoring_signature'),
                   'model': ':'.join(str(evidence.get(k) or 'UNKNOWN') for k in ('model_id', 'model_version'))}
            cohorts['descriptive'].append(row)
            reasons = []
            if bindings.get(lid) != 'REFRESH_PROJECTION_STATS_BOUND_TO_ARCHIVE':
                reasons.append('BASELINE_SOURCE_UNBOUND')
            replay = strict.get(key) or {}
            if replay.get('exact') is not True or replay.get('captured_value_reproduced') is not True:
                reasons.append('BASELINE_SCORING_OR_VALUE_UNVERIFIED')
            if not bound:
                reasons.append('FIE_ARTIFACTS_UNBOUND')
            if not evidence.get('model_id') or not evidence.get('model_version'):
                reasons.append('FIE_MODEL_IDENTITY_MISSING')
            if pair.get('fie_weekly_activation_eligible') is not True:
                reasons.append('FIE_ACTIVATION_INELIGIBLE')
            if not row['scoring_signature']:
                reasons.append('SCORING_SIGNATURE_MISSING')
            if reasons:
                rejected.update(reasons)
            else:
                cohorts['exact'].append(row)
    output = {}
    for name, rows in cohorts.items():
        groups = defaultdict(list)
        for row in rows:
            # Raw points never aggregate across scoring contracts or models.
            key = (row['scoring_signature'], row['model'], row.get('position_model') or 'UNKNOWN')
            groups[key].append(row)
        output[name] = {'rows': len(rows), 'slices': [
            {'scoring_signature': key[0], 'model': key[1], 'position': key[2],
             'league_ids': sorted({r['league_id'] for r in group}), **metrics(group)}
            for key, group in sorted(groups.items(), key=lambda x: str(x[0]))]}
    return {'schema': 'fie-paired-forecast-metrics-v1', 'season': evaluation.get('season'), 'week': evaluation.get('week'),
            'capture_id': capture.get('capture_id'),
            'status': 'EXACT_COHORT_AVAILABLE' if cohorts['exact'] else 'BLOCKED_NO_EXACT_PAIRS',
            'cohorts': output, 'exact_rejection_counts': dict(sorted(rejected.items())),
            'inference': 'DESCRIPTIVE_ONLY_DEPENDENT_LEAGUE_PLAYER_OBSERVATIONS',
            'interval_calibration': 'NOT_AVAILABLE_FROM_MEAN_ONLY_ROWS', 'production_promotion_authorized': False}
