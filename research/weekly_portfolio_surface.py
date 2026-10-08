#!/usr/bin/env python3
"""Stored current roster exposure and independent FIE/baseline projection views.

Display only. Existing input/profile/identity owners retain authority. Missing
quantiles and gated projections remain explicit; no advice or simulation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from current_snapshot_storage import load_current_snapshot
from capture_m10_prospective_weekly_raw import normalize_sleeper_id
from in_season_pr2_weekly_lineups import verified_core, managed_roster, current_index, valid_ids, sleeper_parts
from weekly_lineup_decision_support import canonical_player_id, numeric
from weekly_pipeline_readiness import verify_inputs, stamp, digest
from workflow_decision_context import operational_lifecycle


def projection(row: dict, season: int, week: int, signature: str, artifacts: dict | None = None) -> dict:
    if row.get('season') not in (None,season) or row.get('week') not in (None,week):
        raise ValueError('PROJECTION_ROW_TARGET_MISMATCH')
    fie, baseline = numeric(row.get('fie_weekly_projection')), numeric(row.get('sleeper_weekly_projection'))
    p10, p50, p90 = (numeric(row.get(key)) for key in ('p10','p50','p90'))
    interval_state = 'AVAILABLE' if all(value is not None for value in (p10,p50,p90)) else 'PARTIAL' if any(value is not None for value in (p10,p50,p90)) else 'UNAVAILABLE'
    if p10 is not None and p90 is not None and p10 > p90 or p50 is not None and (p10 is not None and p50 < p10 or p90 is not None and p50 > p90):
        raise ValueError('PROJECTION_QUANTILE_ORDER_INVALID')
    source = forecast_source(fie,artifacts or {})
    bound = source is not None and source.get('status') == 'BOUND_SOURCE_BUNDLES'
    return {'player_id':canonical_player_id(row), 'sleeper_id':normalize_sleeper_id(row.get('sleeper_id')) or None,
        'player_name':row.get('full_name'), 'team':row.get('team'), 'position':row.get('position_model'),
        'season':season, 'week':week, 'scoring_signature':signature,
        'fie_mean':fie, 'fie_median':p50, 'p10':p10, 'p50':p50, 'p90':p90,
        'sleeper_mean':baseline, 'fie_minus_sleeper':round(fie-baseline,6) if fie is not None and baseline is not None else None,
        'fie_coverage':'AVAILABLE' if fie is not None else 'UNSUPPORTED', 'interval_coverage':interval_state,
        'weekly_activation_eligible':row.get('weekly_activation_eligible') is True,
        'waiver_activation_eligible':row.get('waiver_activation_eligible') is True,
        'decision_mean':numeric(row.get('decision_weekly_projection')),
        'projection_source':row.get('projection_source'), 'component_stats':row.get('predicted_stats') or {},
        'model_id':row.get('model_id'), 'model_version':row.get('model_version'),
        'model_identity_status':'BOUND' if row.get('model_id') and row.get('model_version') else 'ARTIFACT_BOUND_MODEL_UNDECLARED' if bound else 'NOT_DECLARED_BY_CURRENT_OWNER',
        'fie_forecast_source':source,
        'confidence':numeric(row.get('confidence')), 'feature_coverage':numeric(row.get('feature_coverage')),
        'status':'GOVERNED_FORECAST' if fie is not None and row.get('weekly_activation_eligible') is True else 'RESEARCH_OR_DIAGNOSTIC' if fie is not None else 'UNSUPPORTED',
        'injury_status':row.get('injury_status')}


def projection_index(current: dict) -> dict:
    """Reuse M10's numeric CSV-ID normalization, preserving exact Sleeper rows."""
    index = {}
    for row in current['players']:
        raw = str(row.get('sleeper_id') or '')
        pid = normalize_sleeper_id(raw)
        if not pid:
            continue
        previous = index.get(pid)
        if previous is not None:
            # Exact live Sleeper-ID row owns the current view. Do not merge a
            # historical numeric-CSV alias's forecast into that row.
            previous_exact = str(previous.get('sleeper_id')) == pid
            current_exact = raw == pid
            if previous_exact and current_exact:
                raise ValueError('PORTFOLIO_DUPLICATE_EXACT_SLEEPER_ID')
            if previous_exact:
                continue
            if not current_exact and previous != row:
                raise ValueError('PORTFOLIO_CONFLICTING_CSV_ALIASES')
        index[pid] = row
    return index


def forecast_source(fie: float | None, artifacts: dict) -> dict | None:
    """Read immutable snapshot-level lineage without duplicating it in player bases."""
    if fie is None:
        return None
    if not artifacts:
        return {'status':'NOT_DECLARED_BY_CURRENT_OWNER'}
    if not isinstance(artifacts,dict):
        raise ValueError('PORTFOLIO_FORECAST_ARTIFACTS_INVALID')
    labels=('M4','M5','M6')
    if any(not isinstance(artifacts.get(label),dict) for label in labels):
        raise ValueError('PORTFOLIO_FORECAST_ARTIFACTS_INVALID')
    if any(artifacts[label].get('status')!='BOUND' for label in labels):
        return {'status':'SOURCE_BUNDLES_NOT_BOUND'}
    if any(artifacts[label].get('artifact')!=label or
           not isinstance(artifacts[label].get('research_build'),str) or
           not artifacts[label]['research_build'].strip() or
           not isinstance(artifacts[label].get('sha256'),str) or
           len(artifacts[label]['sha256'])!=64 or
           any(c not in '0123456789abcdef' for c in artifacts[label]['sha256']) for label in labels):
        raise ValueError('PORTFOLIO_FORECAST_ARTIFACTS_INVALID')
    return {'status':'BOUND_SOURCE_BUNDLES','primary_artifact':'M4',
            'm4_sha256':artifacts['M4']['sha256'],
            'm5_gate_sha256':artifacts['M5']['sha256'],
            'm6_snapshot_input_sha256':artifacts['M6']['sha256']}


def league_surface(root: Path, lid: str, season: int, week: int, as_of: datetime, username: str) -> dict:
    base = root / f'data/research/leagues/{lid}'
    current_path = base/'current/milestone5_current.json'
    current = load_current_snapshot(current_path,root=root)
    core_path, core = verified_core(root,base/'app/manifest.json')
    generated = stamp(core['generated_at'])
    age = (as_of-generated).total_seconds()
    if age < 0 or age > min(float(core.get('stale_after_seconds',21600)),36*3600):
        raise ValueError(f'PORTFOLIO_CORE_STALE_OR_FUTURE observed_at={core["generated_at"]} age_seconds={age:.0f} limit_seconds={min(float(core.get("stale_after_seconds",21600)),36*3600):.0f}; refresh currentseason before rebuilding the surface')
    roster, _ = managed_roster(core,username)
    if roster is None:
        raise ValueError('PORTFOLIO_MANAGED_ROSTER_UNRESOLVED')
    league, rosters, _ = sleeper_parts(core)
    owned = valid_ids(roster.get('players'))
    starters = valid_ids(roster.get('starters'))
    if not set(starters).issubset(owned):
        raise ValueError('PORTFOLIO_STARTER_NOT_OWNED')
    index = projection_index(current)
    universe = set(pid for row in rosters for pid in valid_ids(row.get('players')))
    # Also expose independently forecastable available players. Never substitute
    # their diagnostic rows into a recommendation or declare waiver eligibility.
    universe.update(normalize_sleeper_id(row['sleeper_id']) for row in index.values() if row.get('sleeper_id')
                    and numeric(row.get('fie_weekly_projection')) is not None
                    and (row.get('weekly_activation_eligible') is True or row.get('waiver_activation_eligible') is True
                         or row.get('position_model') in {'DEF','DST','D/ST','K'}))
    records, unresolved = [], []
    seen = set()
    for pid in sorted(universe):
        row = index.get(pid) or index.get(pid.upper())
        if row is None or canonical_player_id(row) is None:
            unresolved.append(pid)
            continue
        canonical = canonical_player_id(row)
        if canonical in seen:
            raise ValueError('PORTFOLIO_DUPLICATE_CANONICAL_PLAYER')
        seen.add(canonical)
        item = projection(row,season,week,current['scoring_signature'],current.get('forecast_artifacts'))
        item.update(owned_by_user=pid in owned, submitted_starter=pid in starters,
                    rostered_in_league=any(pid in valid_ids(r.get('players')) for r in rosters))
        records.append(item)
    lifecycle = operational_lifecycle(root,lid,season,week)
    active = lifecycle.get('operational') is True
    return {'league_id':lid, 'league_name':core.get('league_name'), 'format':core.get('format'),
            'season':season, 'week':week, 'status':'PARTIAL_UNRESOLVED_PLAYERS' if unresolved else 'BOUND_CURRENT_ROSTER',
            'as_of_utc':as_of.isoformat(), 'roster_observed_at':core['generated_at'],
            'forecast_observed_at':current['generated_at'], 'profile_fingerprint':current['profile_fingerprint'],
            'forecast_snapshot_storage_sha256':digest(current_path),
            'forecast_artifacts':current.get('forecast_artifacts') or {},
            'scoring_signature':current['scoring_signature'], 'lifecycle':lifecycle, 'active_operational_scope':active,
            'managed_roster_id':roster['roster_id'], 'roster_positions':league.get('roster_positions') or [], 'unresolved_sleeper_ids':unresolved,
            'projection_coverage':dict(Counter(item['fie_coverage'] for item in records)),
            'players':records, 'core_path':core_path.relative_to(root).as_posix(),
            'starter_semantics':'STORED_AUTOMATIC_ROSTER' if 'BEST' in str(core.get('format','')).upper() else 'STORED_SUBMITTED_ROSTER',
            'opponent_exposure':{'kind':'CHOPPED_FIELD' if 'CHOPPED' in str(core.get('format','')).upper() else 'DIRECT_H2H',
                                 'status':'BLOCKED_CAPTURED_ACTIVE_FIELD_REQUIRED' if 'CHOPPED' in str(core.get('format','')).upper() else 'BLOCKED_MATCHUP_CAPTURE_REQUIRED',
                                 'reason':'Observed roster rows do not certify active chopped-field membership.' if 'CHOPPED' in str(core.get('format','')).upper() else 'Core roster data alone does not identify this week’s direct H2H opponent.'}}


def exposure(leagues: list[dict]) -> list[dict]:
    rows = {}
    for league in leagues:
        if not league.get('active_operational_scope'):
            continue
        for player in league.get('players',[]):
            if not player['owned_by_user']:
                continue
            item = rows.setdefault(player['player_id'], {'player_id':player['player_id'], 'player_name':player['player_name'],
                 'team':player['team'], 'position':player['position'], 'owned_contexts':[], 'starting_contexts':[]})
            context = {key:league.get(key) for key in ('league_id','league_name','format','scoring_signature','profile_fingerprint','roster_observed_at','starter_semantics')}
            item['owned_contexts'].append(context)
            if player['submitted_starter']:
                item['starting_contexts'].append(context)
    for item in rows.values():
        item['owned_league_count'] = len(item['owned_contexts'])
        item['starting_league_count'] = len(item['starting_contexts'])
    return sorted(rows.values(),key=lambda row:(-row['starting_league_count'],-row['owned_league_count'],str(row['player_id'])))


def specialist_boards(leagues: list[dict]) -> dict:
    """Expose owned/available specialist evidence without inventing strategy."""
    boards={'DST':[],'K':[]}
    for league in leagues:
        for label,positions in [('DST',{'DEF','DST','D/ST'}),('K',{'K'})]:
            base={key:league.get(key) for key in ('league_id','league_name','season','week','scoring_signature','roster_observed_at')}
            if league['status'] not in {'BOUND_CURRENT_ROSTER','PARTIAL_UNRESOLVED_PLAYERS'}:
                boards[label].append({**base,'status':'BLOCKED_LEAGUE_INPUTS','owned':[],'available':[]})
                continue
            if not set(league['roster_positions']) & positions:
                boards[label].append({**base,'status':'NOT_APPLICABLE_NO_ROSTER_SLOT','owned':[],'available':[]})
                continue
            if not league['active_operational_scope']:
                boards[label].append({**base,'status':'NOT_APPLICABLE_RESEARCH_ONLY','owned':[],'available':[]})
                continue
            rows=[row for row in league['players'] if row['position'] in positions]
            boards[label].append({**base,'status':'PARTIAL_FORECAST_BOARD_NO_HOLD_STREAM_STRATEGY',
                'owned':[row for row in rows if row['owned_by_user']],
                'available':[row for row in rows if not row['rostered_in_league']],
                'strategy_recommendation':None,
                'note':'Current independent forecasts and observed availability only. Replacement, multi-week hold/stream strategy and transaction advice retain their original owners.'})
    return boards


def build(root: Path, season: int, week: int, as_of: datetime) -> dict:
    if as_of.tzinfo is None or not 1 <= week <= 18:
        raise ValueError('PORTFOLIO_TARGET_OR_TIME_INVALID')
    username = json.loads((root/'config/league-portfolio.json').read_text())['sleeper_username']
    receipt = verify_inputs(root,target={'season':season,'week':week},as_of=as_of,league_id=None,max_age_hours=36)
    leagues = []
    for check in receipt['leagues']:
        lid = check['league_id']
        if check['status'] != 'READY':
            leagues.append({'league_id':lid,'status':'BLOCKED_INPUTS','reason_codes':check['reason_codes']})
            continue
        try:
            leagues.append(league_surface(root,lid,season,week,as_of,username))
        except Exception as exc:
            leagues.append({'league_id':lid,'status':'BLOCKED_LEAGUE_SURFACE','reason':f'{type(exc).__name__}:{exc}'})
    return {'producer':{'module':'research/weekly_portfolio_surface.py','version':'1.0.0','sha256':digest(Path(__file__))},'schema':'fie-weekly-portfolio-surface-v1','season':season,'week':week,'as_of_utc':as_of.isoformat(),
            'status':'BLOCKED' if not any(row['status'] in {'BOUND_CURRENT_ROSTER','PARTIAL_UNRESOLVED_PLAYERS'} for row in leagues) else 'PARTIAL' if any(row['status'] != 'BOUND_CURRENT_ROSTER' for row in leagues) else 'BOUND',
            'input_hashes':receipt['input_hashes'],'leagues':leagues,'roster_exposure':exposure(leagues),'specialist_evidence':specialist_boards(leagues),
            'league_status_counts':dict(Counter(row['status'] for row in leagues)),
            'player_scope':'Observed league-rostered players, eligible unrostered forecast candidates and current specialist boards; not a complete unsupported offensive free-agent universe.',
            'governance':{'display_only':True,'new_forecasts':False,'new_recommendations':False,'cross_league_decision_transfer':False,
                          'production_model_changed':False,'target_week_realized_stats_used':False},
            'note':'FIE and Sleeper are independent columns. Mean is never relabeled as median; unknown intervals stay null. Stored starters are observations, not proposed or executed lineups. Research-only leagues are excluded from active exposure and remain inspectable.'}


def markdown(report: dict) -> str:
    lines = [f"## Roster and projection surface — {report['season']} Week {report['week']}",f"Status: **{report['status']}**",'',
        '| Player | Position | Owned leagues | Starting leagues |','|---|---|---|---|']
    for row in report['roster_exposure']:
        lines.append(f"| {row['player_name']} | {row['position']} | {row['owned_league_count']} | {row['starting_league_count']} |")
    lines += ['',report['note'],'','### League coverage and owned-player forecasts','']
    for league in report['leagues']:
        if league.get('reason'):
            lines.append(f"- {league['league_id']}: **{league['status']}** — {league['reason']}")
    for league in report['leagues']:
        lines += [f"#### {league.get('league_name') or league['league_id']}", '',
            f"**{league['status']}** — scoring `{league.get('scoring_signature','—')}`; lifecycle `{(league.get('lifecycle') or {}).get('state','UNKNOWN')}`.", '',
            '| Player | FIE mean | Sleeper mean | Delta | P10 / P50 / P90 | Eligibility |', '|---|---|---|---|---|---|']
        def show(value):return '—' if value is None else f'{value:.2f}'
        for player in league.get('players',[]):
            if player['owned_by_user']:
                interval=' / '.join(show(player[key]) for key in ('p10','p50','p90'))
                lines.append(f"| {player['player_name']} | {show(player['fie_mean'])} | {show(player['sleeper_mean'])} | {show(player['fie_minus_sleeper'])} | {interval} | {player['status']} |")
        lines.append('')
    return '\n'.join(line.rstrip() for line in lines).rstrip()+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--season',type=int,required=True);parser.add_argument('--week',type=int,required=True)
    parser.add_argument('--as-of-utc',default='');parser.add_argument('--output',required=True)
    args=parser.parse_args();root=Path(args.root).resolve();output=Path(args.output).resolve()
    if output.is_relative_to(root/'data/research'):
        raise ValueError('PORTFOLIO_SURFACE_MUST_NOT_OVERWRITE_RESEARCH')
    report=build(root,args.season,args.week,stamp(args.as_of_utc) if args.as_of_utc else datetime.now(timezone.utc))
    report['input_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(report,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    with output.with_suffix('.md').open('x',encoding='utf-8') as stream:
        stream.write(markdown(report))
    print(markdown(report))

if __name__=='__main__':
    main()
