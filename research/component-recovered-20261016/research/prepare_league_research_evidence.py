"""Captured Chopped/auction and specialist research, no calibrated advice."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import pandas as pd
from prospective_research_io import binding, clock, gates, now, replay_response, write, encoded
from capture_week6_research_sources import validate_manifest
from capture_m10_prospective_weekly_raw import normalize_sleeper_id
from league_profile import infer_format
from weekly_lineup_operational_evidence import chopped_field_context, verify_chopped_active_field
from weekly_portfolio_surface import identity_only_projection
from strict_sleeper_baseline import audit_score


def managed_roster(users,rosters,username):
    if not isinstance(users,list) or not isinstance(rosters,list) or len({r.get('roster_id') for r in rosters})!=len(rosters):
        raise ValueError('LEAGUE_USERS_OR_ROSTERS_INVALID')
    ids={str(u['user_id']) for u in users if str(u.get('display_name') or '').casefold()==username.casefold() or str(u.get('username') or '').casefold()==username.casefold()}
    owned=[r for r in rosters if str(r.get('owner_id')) in ids]
    if len(ids)!=1 or len(owned)!=1:
        raise ValueError('LEAGUE_MANAGED_IDENTITY_NOT_UNIQUE')
    return owned[0]


def specialists(profile,rosters,managed,catalog,projections,identity,season=None,week=None):
    positions=profile.get('roster_positions') or []
    requested=[]
    for pos,slots in [('DST',{'DEF','DST','D/ST'}),('K',{'K'})]:
        if set(positions)&slots:requested.append(pos)
    owned={str(pid) for roster in rosters or [] for pid in roster.get('players') or []}
    held={str(pid) for pid in managed.get('players') or []}
    crosswalk={}
    for _,row in identity.dropna(subset=['canonical_player_id','sleeper_id']).iterrows():
        crosswalk.setdefault(normalize_sleeper_id(row.sleeper_id),set()).add(str(row.canonical_player_id))
    index={}
    for row in projections:
        sid=str(row.get('player_id') or '')
        if sid in index:raise ValueError('SPECIALIST_PROJECTION_DUPLICATE')
        index[sid]=row
    result=[]
    for position in requested:
        candidates=[]
        for sid,player in sorted(catalog.items()):
            source_position=player.get('position')
            if source_position not in ({'DEF','DST','D/ST'} if position=='DST' else {'K'}):continue
            if not player.get('team'):continue
            exact=identity_only_projection(str(sid),catalog)
            canonical=exact.get('canonical_player_id') if exact else None
            ids=crosswalk.get(str(sid),set())
            if canonical and ids and ids!={canonical}:canonical=None
            elif not canonical and len(ids)==1:canonical=next(iter(ids))
            projection=index.get(str(sid))
            if projection and (season is None or week is None or str(projection.get('season'))!=str(season) or str(projection.get('week'))!=str(week) or projection.get('season_type')!='regular'):
                projection=None
            if position=='K':
                from strict_kicker_source_components import audit
                score=audit((projection or {}).get('stats') or {},profile['scoring_settings'])
            else:
                score=audit_score((projection or {}).get('stats') or {},profile['scoring_settings'],position)
            candidates.append({'sleeper_id':str(sid),'canonical_player_id':canonical,'team':player['team'],
                'position':position,'available':str(sid) not in owned if rosters is not None else None,'held':str(sid) in held,
                'mean':score['points'] if score['exact'] else None,'scoring_audit':score,
                'forecast_owner':'SLEEPER_RAW_STRICT_REPLAY','realized_points':None,'bye':None})
        held_rows=[r for r in candidates if r['held']]
        result.append({'position':position,'candidates':candidates,'initial_hold_sleeper_id':held_rows[0]['sleeper_id'] if len(held_rows)==1 else None,
            'hold_basis':'CURRENT_MIDSEASON_MANAGED_ROSTER_NOT_PRESEASON_TOP5',
            'strategies':['FULL_HOLD_WITH_BYE_REPLACEMENT','FULL_STREAM_ALLOW_KEEP']+(['SELECTED_HOLD_BOTTOM10'] if position=='DST' else []),
            'status':'FROZEN_SOURCE_BOARD' if len(held_rows)==1 else 'BLOCKED_HOLD_IDENTITY_REQUIRES_DECLARATION',
            'selected_hold_status':'BLOCKED_COMPLETE_32_TEAM_RANK_UNIVERSE_REQUIRED' if position=='DST' else 'NOT_APPLICABLE_DST_SPECIFIC_BOTTOM10_RULE',
            **gates(['BLOCKED_EXACT_OUTCOME_REQUIRED','BLOCKED_STRATEGY_VALIDATION_REQUIRED'])})
    return result


def build(root,envelope):
    source=validate_manifest(root,envelope);at=source['captured_at'];lookup={r['name']:r for r in source['responses']}
    def load(name):return json.loads(replay_response(root,lookup[name],at))
    catalog=load('sleeper_players');projections=load('sleeper_projections')
    from fie_research import build_identity
    identity,_=build_identity(pd.read_csv(io.BytesIO(replay_response(root,lookup['players'],at)),low_memory=False),
                               pd.read_csv(io.BytesIO(replay_response(root,lookup['ff_playerids'],at)),low_memory=False))
    username=json.loads((root/'config/league-portfolio.json').read_text())['sleeper_username']
    from window2d_context_foundation import normalize_team,parse_schedule_csv
    games=parse_schedule_csv(replay_response(root,lookup['schedule'],at),source['season'])
    known_teams={g[k] for g in games for k in ['home_team','away_team']}
    active_teams={g[k] for g in games if g['week']==source['week'] for k in ['home_team','away_team']}
    leagues=[]
    for lid in source['league_ids']:
        try:
            profile=load(lid+'-profile');rosters=load(lid+'-rosters');users=load(lid+'-users')
            managed=managed_roster(users,rosters,username);fmt=infer_format(profile,'AUTO')
            if str(profile.get('season'))!=str(source['season']):raise ValueError('LEAGUE_PROFILE_SEASON')
            matchups=load(lid+'-matchups');transactions=load(lid+'-transactions')
            field=None
            availability_rosters=rosters
            if fmt in {'CHOPPED','CHOPPED_BESTBALL'}:
                captured=lookup[lid+'-matchups']['observed_at']
                field=chopped_field_context(managed['roster_id'],{'season':source['season'],'week':source['week'],
                        'captured_at':captured,'rows':matchups},season=source['season'],week=source['week'],as_of=clock(at))
                core={'generated_at':max(lookup[lid+'-profile']['observed_at'],lookup[lid+'-rosters']['observed_at'],key=clock),
                      'format':fmt,'sleeper':{'league':profile,'rosters':rosters}}
                import hashlib
                field=verify_chopped_active_field(field,core,core_sha256=hashlib.sha256(encoded(core)).hexdigest(),
                        season=source['season'],week=source['week'],managed_roster_id=managed['roster_id'])
                availability_rosters=([r for r in rosters if 'eliminated' not in (r.get('settings') or {})]
                                      if field.get('active_field_certified') else None)
            boards=specialists(profile,availability_rosters,managed,catalog,projections,identity,source['season'],source['week'])
            for board in boards:
                for row in board['candidates']:
                    team=normalize_team(row['team'])
                    row['bye']=(team not in active_teams) if team in known_teams and active_teams else None
            league={'league_id':lid,'format':fmt,'managed_roster_id':managed['roster_id'],'field':field,
                    'auction_observations':transactions,'auction_completeness':'CENSORED_EXPOSED_TRANSACTIONS_ONLY',
                    'bid_clearing_curve_status':'BLOCKED_COMPLETE_COMPETING_BIDS_REQUIRED',
                    'specialists':boards,
                    'survival_status':'BLOCKED_REAL_JOINT_BANK_AND_CALIBRATION_REQUIRED',
                    'source_bindings':{role:lookup[lid+'-'+role] for role in ['profile','rosters','users','matchups','transactions']},
                    **gates(['BLOCKED_CALIBRATION_REQUIRED','BLOCKED_DECISION_DOMAIN_VALIDATION_REQUIRED'])}
            leagues.append(league)
        except (ValueError,KeyError,TypeError) as error:
            leagues.append({'league_id':lid,'status':'BLOCKED_LEAGUE_SOURCE_OR_IDENTITY','reason':str(error),**gates(['BLOCKED_LEAGUE_SOURCE_OR_IDENTITY'])})
    return {'schema':'fie-weekly-league-research-evidence-v1','season':source['season'],'week':source['week'],
            'captured_at':at,'prepared_at':now(),'source_envelope':binding(root,envelope,at),'leagues':leagues,
            **gates(['BLOCKED_RESEARCH_VALIDATION_REQUIRED'])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--source-envelope',type=Path,required=True);a=p.parse_args();value=build(a.root,a.source_envelope)
    at=now();path=a.root/f"data/research/prospective/league-evidence/{value['season']}/week_{value['week']:02d}/{clock(at).strftime('%Y%m%dT%H%M%S%fZ')}/evidence.json"
    write(path,value);print(json.dumps({'status':'LEAGUE_RESEARCH_PREPARED','leagues':len(value['leagues']),'path':str(path)}))


if __name__=='__main__':main()
