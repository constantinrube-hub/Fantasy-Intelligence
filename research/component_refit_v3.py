"""Opt-in source-column repair; writes a distinct fit, never replaces V2."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from component_weekly_ops import PROJECT, read, write_new, digest
from component_diagnostics import safe

def normalize_opponent(frame):
    result = frame.copy()
    if 'opponent_team' not in result:
        if 'opponent' not in result or result.opponent.isna().any():
            raise ValueError('NO_BOUND_OPPONENT_COLUMN')
        return result
    if 'opponent' in result:
        both = result.opponent.notna() & result.opponent_team.notna()
        if result.loc[both, 'opponent'].astype(str).ne(result.loc[both, 'opponent_team'].astype(str)).any():
            raise ValueError('CONFLICTING_OPPONENT_COLUMNS')
        result['opponent'] = result.opponent.fillna(result.opponent_team)
    else:
        result['opponent'] = result.opponent_team
    if result.opponent.isna().any():
        raise ValueError('UNKNOWN_OPPONENT_AFTER_NORMALIZATION')
    return result

def repair_fit(project, bundle, training, output, through):
    if safe(project, output).exists():
        raise ValueError('NEW_V3_FIT_PATH_REQUIRED')
    sys.path.insert(0, str(project / 'research'))
    import recovery_refit
    from component_source_contract import team
    from issue_component_forecasts import snapshot
    original = recovery_refit.source_frames
    def adapted(root, bound_bundle, cutoff):
        hist, current = original(root, bound_bundle, cutoff)
        current = normalize_opponent(current)
        reference = next(r for r in bound_bundle['responses'] if r['name'] == 'schedule')
        schedule = snapshot(root, reference, bound_bundle['observation_cutoff'])
        schedule = schedule[schedule.season.eq(2026) & schedule.game_type.eq('REG') & schedule.week.le(cutoff)]
        opponents = {}
        for row in schedule.itertuples():
            opponents[(int(row.week), team(row.home_team))] = team(row.away_team)
            opponents[(int(row.week), team(row.away_team))] = team(row.home_team)
        if any(opponents.get((int(row.week), team(row.team))) != team(row.opponent) for row in current.itertuples()):
            raise ValueError('OPPONENT_COLUMN_DISAGREES_WITH_BOUND_SCHEDULE')
        return hist, current
    intermediate = output.with_name(output.stem + '-v2-normalized-intermediate.json')
    recovery_refit.source_frames = adapted
    try:
        value = recovery_refit.refit(intermediate, bundle, training, through, project)
    finally:
        recovery_refit.source_frames = original
    value = dict(value)
    value.update({'version': 'SOURCE_PREWEEK_ROLE_REFIT_V3_OPPONENT_COLUMN', 'source_adapter_sha256': digest(Path(__file__)),
                  'normalized_opponent_source': 'opponent_team', 'baseline_replacement': False,
                  'intermediate_fit_sha256': digest(safe(project, intermediate))})
    cells = [spec for section in ['receiving_defense', 'wr_defense', 'rushing_defense'] for roles in value[section].values() for spec in roles.values()]
    supported = sum(any(isinstance(v, (int, float)) and v > 0 for k, v in row['observed'].items() if k in {'carries', 'targets'}) for row in cells)
    if not supported:
        raise ValueError('V3_REPAIR_DID_NOT_RESTORE_OPPONENT_SUPPORT')
    value['supported_opponent_cells'] = supported
    write_new(safe(project, output), value)
    return value

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--project', type=Path, default=PROJECT)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--training', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--through-week', type=int, required=True)
    a = p.parse_args()
    value = repair_fit(a.project.resolve(), a.bundle, a.training, a.output, a.through_week)
    print(value['version'], value['supported_opponent_cells'], 'supported cells; baseline unchanged')
