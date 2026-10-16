"""Read-only fit tracking and postgame component attribution; never inference input."""
from __future__ import annotations
import argparse
import collections
import csv
import gzip
import html
import itertools
import json
import math
import heapq
from pathlib import Path
import sys
from datetime import datetime, timezone
from component_weekly_ops import REPO, PROJECT, HISTORY, REFERENCE, digest, read, write_new

CONFIG = REPO / 'config/component-diagnostics-v1.json'
OFFENSE = {'QB', 'RB', 'WR', 'TE'}

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def records(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)

def lines(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as compressed:
        for value in values:
            compressed.write((json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf-8'))

class StreamRows:
    def __init__(self, path):
        self.raw = Path(path).open('xb')
        self.stream = gzip.GzipFile(fileobj=self.raw, mode='wb', mtime=0)
        self.count = 0
    def append(self, row):
        self.stream.write((json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode('utf-8'))
        self.count += 1
    def close(self):
        self.stream.close(); self.raw.close()
    def __del__(self):
        if hasattr(self, 'stream'):
            self.close()

class Moments:
    def __init__(self):
        self.n = 0; self.absolute = 0.; self.square = 0.; self.signed = 0.; self.nonzero = 0
    def append(self, pair):
        error, actual = pair
        self.n += 1; self.absolute += abs(error); self.square += error * error; self.signed += error; self.nonzero += actual != 0
    def result(self):
        return {'n': self.n, 'mae': self.absolute / self.n, 'rmse': math.sqrt(self.square / self.n),
                'bias': self.signed / self.n, 'nonzero_actuals': self.nonzero}

def safe(project, relative):
    relative = Path(relative)
    path = (project / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(project.resolve()):
        raise ValueError('UNSAFE_DIAGNOSTIC_PATH')
    return path

def verify_artifacts(project, receipt):
    for rel, expected in receipt.get('artifacts', {}).items():
        if digest(safe(project, rel)) != expected:
            raise ValueError('DIAGNOSTIC_SOURCE_DRIFT:' + rel)

def finish(out, result):
    result = {**result, 'built_at': datetime.now(timezone.utc).isoformat(), 'diagnostic_only': True,
              'forecast_input_eligible': False, 'artifacts': {p.relative_to(out).as_posix(): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    write_new(out / 'diagnostic-receipt.json', result)
    return result

def verify_diagnostic(out):
    receipt = read(out / 'diagnostic-receipt.json')
    for rel, expected in receipt['artifacts'].items():
        path = safe(out, rel)
        if digest(path) != expected:
            raise ValueError('PARAMETER_SNAPSHOT_DRIFT')
    return receipt

def parameter_rows(fit):
    result = []
    for cid, metrics in fit.get('players', {}).items():
        for metric, spec in metrics.items():
            value = spec.get('rate')
            if not finite(value):
                continue
            current = spec.get('current_exposure')
            historical = spec.get('historical_exposure')
            result.append({'key': ['player', cid, metric], 'value': value, 'entity_id': cid,
                           'support': {'current_exposure': current, 'historical_exposure': historical},
                           'current_weight': spec.get('current_weight'),
                           'support_status': 'CURRENT_SUPPORTED' if finite(current) and current > 0 else 'HISTORICAL_OR_PRIOR_ONLY',
                           'position_prior': spec.get('position_prior')})
    for section in ['rushing_defense', 'receiving_defense', 'wr_defense']:
        for team, roles in fit.get(section, {}).items():
            for role, spec in roles.items():
                observed = spec.get('observed', {})
                opportunity = observed.get('carries' if section == 'rushing_defense' else 'targets')
                status = 'OBSERVED_SUPPORTED' if finite(opportunity) and opportunity > 0 else 'PRIOR_ONLY' if opportunity == 0 else 'SUPPORT_UNKNOWN'
                for metric, value in spec.items():
                    if finite(value):
                        result.append({'key': [section, team, role, metric], 'value': value,
                                       'team': team, 'role': role, 'support': observed, 'support_status': status})
    def flatten(section, value, path=()):
        if isinstance(value, dict):
            if finite(value.get('rate')):
                result.append({'key': [section, *path, 'rate'], 'value': value['rate'], 'support': {k: v for k, v in value.items() if k != 'rate'}, 'support_status': 'POOLED_PRIOR'})
            else:
                for key, child in value.items():
                    flatten(section, child, (*path, key))
        elif finite(value):
            result.append({'key': [section, *path], 'value': value, 'support_status': 'SOURCE_ESTIMATE'})
    for section in ['position_priors', 'td_priors', 'offensive_role_td', 'wr_offensive_role_td', 'source_role_priors']:
        flatten(section, fit.get(section, {}))
    for metric, value in read(CONFIG)['fixed_method_weights'].items():
        result.append({'key': ['fixed_method_weight', metric], 'value': value, 'support_status': 'DECLARED_FIXED_NOT_LEARNED'})
    return sorted(result, key=lambda r: r['key'])

def compare_snapshots(current, previous):
    if current['method_version'] != previous['method_version'] or current['config_sha256'] != previous['config_sha256']:
        return {'status': 'METHOD_CHANGED_NOT_COMPARABLE', 'changes': [], 'context_changes': []}
    if previous['through_week'] > current['through_week']:
        raise ValueError('FUTURE_PARAMETER_PREDECESSOR')
    old = {tuple(r['key']): r for r in previous['parameters']}
    new = {tuple(r['key']): r for r in current['parameters']}
    changes = []
    for key in sorted(old.keys() | new.keys()):
        a, b = old.get(key), new.get(key)
        delta = b['value'] - a['value'] if a and b else None
        changes.append({'key': list(key), 'previous': a['value'] if a else None, 'current': b['value'] if b else None,
                        'delta': delta, 'relative_change': delta / abs(a['value']) if a and b and a['value'] != 0 else None,
                        'state': 'COMPARED' if a and b else 'ADDED' if b else 'REMOVED',
                        'previous_support': a.get('support') if a else None, 'current_support': b.get('support') if b else None})
    context = []
    fields = ['team', 'position_model', 'provider_injury', 'source_roster_status', 'depth_order']
    for cid in sorted(current.get('contexts', {}).keys() & previous.get('contexts', {}).keys()):
        a, b = previous['contexts'][cid], current['contexts'][cid]
        for field in fields:
            if a.get(field) != b.get(field):
                context.append({'entity_id': cid, 'field': field, 'previous': a.get(field), 'current': b.get(field)})
    return {'status': 'COMPARABLE', 'changes': changes, 'context_changes': context}

def snapshot(project, fitted, entities, output, history=None):
    fit = read(safe(project, fitted))
    out = safe(project, output)
    out.mkdir(parents=True, exist_ok=False)
    contexts = {}
    if entities:
        contexts = {r['canonical_player_id']: {k: r.get(k) for k in ['name', 'team', 'position_model', 'provider_injury', 'source_roster_status', 'depth_order']}
                    for r in read(safe(project, entities))['entities']}
    current = {'schema': 'fie-parameter-snapshot-v1', 'method_version': fit['version'], 'through_week': fit['through_week'],
               'fit_path': str(fitted), 'fit_sha256': digest(safe(project, fitted)), 'config_sha256': digest(CONFIG),
               'bundle_sha256': fit.get('bundle_sha256'), 'parameters': parameter_rows(fit), 'contexts': contexts}
    write_new(out / 'snapshot.json', current)
    previous = None
    if history:
        candidates = []
        for path in safe(project, history).glob('runs/*/diagnostics/**/snapshot.json'):
            if path.parent == out or not (path.parent / 'diagnostic-receipt.json').is_file():
                continue
            parent_run = next((p for p in path.parents if p.parent.name == 'runs'), None)
            if parent_run is None or not (parent_run / 'run-receipt.json').is_file() or read(parent_run / 'run-receipt.json')['status'] != 'PASS':
                continue
            verify_diagnostic(path.parent)
            value = read(path)
            if value['method_version'] == current['method_version'] and value['through_week'] <= current['through_week']:
                candidates.append((value['through_week'], read(path.parent / 'diagnostic-receipt.json')['built_at'], path, value))
        if candidates:
            _, _, path, previous = max(candidates, key=lambda x: (x[0], x[1], str(x[2])))
            current_previous = str(path.relative_to(project))
        else:
            current_previous = None
    else:
        current_previous = None
    seed = project / REFERENCE / 'fit/source-refit-final.json'
    if previous is None and seed.is_file() and seed.resolve() != safe(project, fitted):
        value = read(seed)
        previous = {'method_version': value['version'], 'through_week': value['through_week'],
                    'config_sha256': digest(CONFIG), 'parameters': parameter_rows(value),
                    'contexts': {r['canonical_player_id']: r for r in read(project / REFERENCE / 'verified/source-refit/entities.json')['entities']}}
        current_previous = str(seed.relative_to(project))
    comparison = compare_snapshots(current, previous) if previous else {'status': 'INITIAL_SNAPSHOT', 'changes': [], 'context_changes': []}
    lines(out / 'parameter-changes.jsonl.gz', comparison['changes'])
    lines(out / 'context-changes.jsonl.gz', comparison['context_changes'])
    prior_cells = {tuple(r['key'][:3]) for r in current['parameters'] if r.get('support_status') == 'PRIOR_ONLY'}
    summary = {'status': comparison['status'], 'parameter_count': len(current['parameters']), 'prior_only_defense_cells': len(prior_cells),
               'prior_only_by_section': dict(collections.Counter(k[0] for k in prior_cells)),
               'changed_parameters': sum(r['delta'] not in {None, 0} for r in comparison['changes']),
               'context_change_count': len(comparison['context_changes']), 'previous_snapshot': current_previous,
               'warning': 'ZERO_SUPPORT_IS_NOT_A_LEARNED_OPPONENT_EFFECT' if prior_cells else None}
    write_new(out / 'summary.json', summary)
    changed = sorted([r for r in comparison['changes'] if r['delta'] is not None], key=lambda r: -abs(r['delta']))[:100]
    html_report(out, 'Parameter stability', summary, changed)
    return finish(out, {'type': 'parameter-stability', **summary, 'fit_sha256': current['fit_sha256'], 'method_version': fit['version']})

def product_attribution(forecast, actual, names):
    if len(forecast) != len(actual) or len(names) != len(actual) or not 1 <= len(names) <= 4:
        raise ValueError('INVALID_ATTRIBUTION_FACTORS')
    effects = [0.] * len(names)
    orders = list(itertools.permutations(range(len(names))))
    for order in orders:
        values = list(actual)
        for i in order:
            before = math.prod(values)
            values[i] = forecast[i]
            effects[i] += (math.prod(values) - before) / len(orders)
    if not math.isclose(sum(effects), math.prod(forecast) - math.prod(actual), rel_tol=1e-9, abs_tol=1e-8):
        raise ValueError('ATTRIBUTION_DOES_NOT_RECONCILE')
    return dict(zip(names, effects))

def decompose_component(pred, actual, component, chain, budgets=None):
    wanted = list(dict.fromkeys(chain))
    if any(not finite(pred.get(k)) or not finite(actual.get(k)) for k in wanted):
        return {'status': 'MISSING_FACTOR_VALUES', 'contributions': {}}
    error = pred[component] - actual[component]
    result = {'forecast': pred[component], 'actual': actual[component], 'error': error, 'contributions': {}}
    parents = chain[:-1]
    if any(pred[k] <= 0 or actual[k] <= 0 for k in parents):
        return {**result, 'status': 'ZERO_PARENT_UNIDENTIFIABLE', 'opportunity_error': pred[chain[0]] - actual[chain[0]]}
    fp = [pred[chain[0]]] + [pred[b] / pred[a] for a, b in zip(chain, chain[1:])]
    ap = [actual[chain[0]]] + [actual[b] / actual[a] for a, b in zip(chain, chain[1:])]
    names = ['player_opportunities'] + ['implied_' + b + '_per_' + a for a, b in zip(chain, chain[1:])]
    if budgets and all(finite(x) and x > 0 for x in budgets):
        fp = [budgets[0], fp[0] / budgets[0], *fp[1:]]
        ap = [budgets[1], ap[0] / budgets[1], *ap[1:]]
        names = ['team_opportunities', 'player_share', *names[1:]]
    contributions = product_attribution(fp, ap, names)
    return {**result, 'status': 'DECOMPOSED', 'factors': names, 'forecast_factors': fp, 'actual_factors': ap,
            'contributions': contributions, 'reconciliation_error': sum(contributions.values()) - error,
            'efficiencies_are_implied_from_means': True}

def html_report(out, title, summary, rows):
    text = '<!doctype html><meta charset="utf-8"><title>' + html.escape(title) + '</title>'
    text += '<style>body{font:15px/1.5 system-ui;margin:30px;max-width:1200px}pre{white-space:pre-wrap}td,th{padding:8px;border-bottom:1px solid #ddd;vertical-align:top}table{border-collapse:collapse}</style>'
    text += '<h1>' + html.escape(title) + '</h1><p>Postgame diagnostic only. These values never modify an issued forecast.</p><pre>' + html.escape(json.dumps(summary, indent=2)) + '</pre>'
    text += '<p>Preview: up to 100 rows. Complete rows are in the companion compressed tables.</p><table><tr><th>Record</th></tr>'
    text += ''.join('<tr><td><pre>' + html.escape(json.dumps(r, ensure_ascii=False, indent=2)) + '</pre></td></tr>' for r in rows[:100]) + '</table>'
    (out / 'report.html').write_text(text, encoding='utf-8')

def forecast_metadata(project, receipt):
    metadata = {}
    fallback = project / REFERENCE / 'verified/source-refit/entities.json'
    if fallback.is_file():
        metadata.update({r['canonical_player_id']: r for r in read(fallback)['entities']})
    for source in receipt.get('sources', []):
        path = safe(project, source['path'])
        if digest(path) != source['sha256']:
            raise ValueError('FREEZE_SOURCE_MANIFEST_DRIFT')
        entities = path.parent.parent / 'entities.json'
        if entities.is_file():
            metadata.update({r['canonical_player_id']: r for r in read(entities)['entities']})
    return metadata

def review(project, frozen, actual_dirs, output):
    config = read(CONFIG)
    out = safe(project, output)
    out.mkdir(parents=True, exist_ok=False)
    folder = safe(project, frozen)
    fr = read(folder / 'freeze-receipt.json')
    verify_artifacts(project, fr)
    meta = forecast_metadata(project, fr)
    actual = {}; actual_meta = {}; refs = []
    for relative in actual_dirs:
        base = safe(project, relative); receipt = read(base / 'actual-receipt.json')
        verify_artifacts(project, receipt)
        refs.append({'path': str(relative), 'sha256': digest(base / 'actual-receipt.json')})
        csv_path = base / 'training-2026.csv.gz'
        if csv_path.is_file():
            with gzip.open(csv_path, 'rt', encoding='utf-8') as stream:
                for row in csv.DictReader(stream):
                    actual_meta[(row['canonical_player_id'], int(row['season']), int(row['week']))] = {'team': row.get('team')}
        for row in records(base / 'actual-components.jsonl.gz'):
            key = row['canonical_player_id'], row['season'], row['week']
            if key in actual:
                raise ValueError('DUPLICATE_ACTUAL_REVISION')
            actual[key] = row
    forecasts = list(records(folder / 'forecasts.jsonl.gz'))
    matching_weeks = {key[2] for key in actual}
    # Complete actor sums, not sums with unknown components silently set to zero.
    actual_budgets = collections.defaultdict(list)
    for key, row in actual.items():
        team = row.get('team') or actual_meta.get(key, {}).get('team')
        if team and row['position_model'] in OFFENSE:
            for component in ['targets', 'rushing_attempts', 'passing_attempts']:
                actual_budgets[(team, key[1], key[2], component)].append(row['components'].get(component))
    forecast_budgets = collections.defaultdict(list); ranks = {}; rank_groups = collections.defaultdict(list)
    for row in forecasts:
        if row['week'] not in matching_weeks:
            continue
        cid = row['canonical_player_id']; team = meta.get(cid, {}).get('team'); pos = row['position_model']
        if team and pos in OFFENSE:
            for component in ['targets', 'rushing_attempts', 'passing_attempts']:
                forecast_budgets[(row['model_id'], team, row['season'], row['week'], component)].append(row['components'].get(component))
        for component, value in row['components'].items():
            if finite(value):
                rank_groups[(row['model_id'], pos, row['week'], component)].append((cid, value))
    for group, values in rank_groups.items():
        previous_value = None; tied_rank = 0
        for rank, (cid, value) in enumerate(sorted(values, key=lambda v: (-v[1], v[0])), 1):
            if previous_value is None or value != previous_value:
                tied_rank = rank
            ranks[(*group, cid)] = tied_rank
            previous_value = value
    raw_errors = StreamRows(out / 'raw-errors.jsonl.gz')
    decompositions = StreamRows(out / 'component-decomposition.jsonl.gz')
    league_rows = StreamRows(out / 'league-component-impact.jsonl.gz')
    probabilities = collections.defaultdict(lambda: collections.defaultdict(Moments))
    group_values = collections.defaultdict(Moments)
    decomposition_states = collections.Counter(); factor_groups = collections.defaultdict(Moments); preview = []
    matched = 0; missing = 0
    for row in forecasts:
        cid, season, week = row['canonical_player_id'], row['season'], row['week']
        key = cid, season, week; outcome = actual.get(key); pos = row['position_model']; model = row['model_id']
        if outcome is None or outcome['position_model'] != pos:
            missing += len(row['components']); continue
        team = meta.get(cid, {}).get('team', 'UNKNOWN')
        observed_team = outcome.get('team') or actual_meta.get(key, {}).get('team')
        lead = fr['target_weeks'].index(week) + 1
        for component, pred in row['components'].items():
            value = outcome['components'].get(component)
            if not finite(pred) or not finite(value):
                missing += 1; continue
            matched += 1
            rank = ranks[(model, pos, week, component, cid)]
            cuts = config['rank_cuts'].get(pos, [24, 48])
            band = '1-%d' % cuts[0] if rank <= cuts[0] else '%d-%d' % (cuts[0] + 1, cuts[1]) if rank <= cuts[1] else '%d+' % (cuts[1] + 1)
            if pred == 0:
                band = 'ZERO_FORECAST'
            identity = {'model_id': model, 'canonical_player_id': cid, 'name': meta.get(cid, {}).get('name'),
                        'position': pos, 'team': team, 'actual_team': observed_team, 'week': week, 'lead_week': lead,
                        'component': component, 'pregame_component_rank': rank, 'rank_band': band, 'replay_only': row.get('replay_only')}
            opportunity_key = {'QB': 'passing_attempts', 'RB': 'rushing_attempts', 'WR': 'targets', 'TE': 'targets',
                               'K': 'kicker_field_goal_attempts', 'DL': 'idp_tackles_total', 'LB': 'idp_tackles_total', 'DB': 'idp_tackles_total'}.get(pos)
            opportunity = row['components'].get(opportunity_key) if opportunity_key else 1.
            cohort = 'PROJECTED_ACTIVE' if finite(opportunity) and opportunity > .1 else 'PROJECTED_LOW_OR_UNKNOWN'
            identity['cutoff_activity_cohort'] = cohort
            error = pred - value
            raw_errors.append({**identity, 'forecast': pred, 'actual': value, 'error': error,
                               'actual_basis': outcome.get('basis', {}).get(component)})
            for scope, group in [('position', pos), ('team', team), ('rank_band', pos + ':' + band), ('cutoff_activity', pos + ':' + cohort)]:
                group_values[(model, component, week, lead, scope, group)].append((error, value))
            if component.startswith(('prob_', 'dst_prob_')) and 0 <= pred <= 1 and value in {0, 1}:
                probabilities[(model, pos, component, week, lead)][min(int(pred * 10), 9)].append((pred - value, value))
                probabilities[(model, pos, component, week, lead)][('prob', min(int(pred * 10), 9))].append((pred, value))
            if component not in config['decompositions']:
                continue
            chain = config['decompositions'][component]; opportunity = chain[0]
            fb = forecast_budgets.get((model, team, season, week, opportunity), [])
            ab = actual_budgets.get((observed_team, season, week, opportunity), [])
            budgets = (sum(fb), sum(ab)) if team == observed_team and fb and ab and all(finite(x) for x in fb + ab) else None
            result = decompose_component(row['components'], outcome['components'], component, chain, budgets)
            detail = {**identity, **result, 'team_budget_scope': 'COMPLETE_OBSERVED_ACTOR_SUM' if budgets else 'UNAVAILABLE_OR_TEAM_CHANGED'}
            decompositions.append(detail); decomposition_states[result['status']] += 1
            for factor, effect in detail['contributions'].items():
                factor_groups[(model, pos, component, week, lead, factor)].append((effect, 0))
            item = (abs(detail.get('error', 0)), decompositions.count, detail)
            if len(preview) < 100:
                heapq.heappush(preview, item)
            elif item[:2] > preview[0][:2]:
                heapq.heapreplace(preview, item)
    aggregate = []
    for (model, component, week, lead, scope, group), values in sorted(group_values.items()):
        aggregate.append({'model_id': model, 'component': component, 'week': week, 'lead_week': lead, 'scope': scope, 'group': group,
                          **values.result()})
    probability_rows = []
    for key, values in sorted(probabilities.items()):
        bins = []
        total_n = 0; total_square = 0.
        for i in range(10):
            rows = values.get(i)
            if rows and rows.n:
                probs = values[('prob', i)]
                bins.append({'lower': i / 10, 'upper': (i + 1) / 10, 'n': rows.n,
                             'mean_probability': probs.signed / probs.n, 'event_frequency': rows.nonzero / rows.n})
                total_n += rows.n; total_square += rows.square
        probability_rows.append({'model_id': key[0], 'position': key[1], 'component': key[2], 'week': key[3], 'lead_week': key[4],
                                 'n': total_n, 'brier': total_square / total_n, 'reliability_bins': bins})
    factor_rows = [{'model_id': k[0], 'position': k[1], 'component': k[2], 'week': k[3], 'lead_week': k[4], 'factor': k[5],
                    'n': v.n, 'mean_signed_effect': v.signed / v.n, 'mean_absolute_effect': v.absolute / v.n} for k, v in sorted(factor_groups.items())]
    # League impact uses the same frozen rules; its rows are scoring translations,
    # never additional independent football observations.
    if matched and (folder / 'profiles.json').is_file():
        sys.path.insert(0, str(project / 'research'))
        from component_scoring import rules_for
        profiles = {str(p['league_id']): p for p in read(folder / 'profiles.json')}
        contracts = read(project / 'config/contracts/runtime-contracts.json')
        for row in forecasts:
            outcome = actual.get((row['canonical_player_id'], row['season'], row['week']))
            if not outcome or outcome['position_model'] != row['position_model']:
                continue
            for lid in row.get('scores', {}):
                rules = rules_for(profiles[lid]['scoring_settings'], row['position_model'], row.get('fantasy_positions', [row['position_model']]), contracts)
                complete = all(finite(row['components'].get(r['component'])) and finite(outcome['components'].get(r['component'])) for r in rules)
                for rule in rules:
                    component = rule['component']; p = row['components'].get(component); a = outcome['components'].get(component)
                    if finite(p) and finite(a):
                        league_rows.append({'model_id': row['model_id'], 'canonical_player_id': row['canonical_player_id'], 'week': row['week'],
                                            'league_id': lid, 'scoring_key': rule['scoring_key'], 'component': component, 'weight': rule['weight'],
                                            'fantasy_error_contribution': rule['weight'] * (p-a), 'full_score_components_known': complete,
                                            'independent_football_observation': False})
    raw_errors.close(); decompositions.close(); league_rows.close()
    for name, rows in [('group-metrics', aggregate), ('factor-metrics', factor_rows), ('probability-metrics', probability_rows)]:
        lines(out / (name + '.jsonl.gz'), rows)
    summary = {'status': 'OBSERVED_DIAGNOSTICS' if matched else 'WAITING_FOR_OUTCOMES', 'matched_values': matched, 'missing_values': missing,
               'decomposition_statuses': dict(decomposition_states), 'group_rows': len(aggregate),
               'probability_groups': len(probability_rows), 'league_impact_rows': league_rows.count, 'freeze_path': str(frozen),
               'freeze_sha256': digest(folder / 'freeze-receipt.json'), 'actual_sources': refs, 'error_sign': 'FORECAST_MINUS_ACTUAL'}
    write_new(out / 'summary.json', summary)
    html_report(out, 'Component error diagnostics', summary, [x[2] for x in sorted(preview, reverse=True)])
    return finish(out, {'type': 'error-decomposition', **summary, 'config_sha256': digest(CONFIG)})

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project', type=Path, default=PROJECT)
    sub = p.add_subparsers(dest='action', required=True)
    s = sub.add_parser('snapshot'); s.add_argument('--fit', type=Path, required=True); s.add_argument('--entities', type=Path)
    s.add_argument('--history', type=Path); s.add_argument('--output', type=Path, required=True)
    r = sub.add_parser('review'); r.add_argument('--freeze', type=Path, required=True); r.add_argument('--actual', nargs='*', type=Path, default=[])
    r.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); project = a.project.resolve()
    result = snapshot(project, a.fit, a.entities, a.output, a.history) if a.action == 'snapshot' else review(project, a.freeze, a.actual, a.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'artifacts'}))

if __name__ == '__main__':
    main()
