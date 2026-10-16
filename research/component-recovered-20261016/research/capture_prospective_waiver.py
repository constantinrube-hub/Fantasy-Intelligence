"""Run a source-replayed pregame waiver research capture, never a recommendation."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import pandas as pd
from prospective_research_io import binding, clock, gates, now, replay_response, sha, verified, write
from capture_week6_research_sources import SOURCES, fetch, resolve_target, capture, validate_manifest
from prepare_live_waiver_history import prepare
from waiver_v2_prospective import ROOT, validate_lock, forecast
from build_waiver_v2_outcome_ledger import scoring_signature
from capture_m10_prospective_weekly_raw import normalize_sleeper_id


def identity_universe(identity, catalog):
    groups={}
    for _,row in identity.dropna(subset=['canonical_player_id','sleeper_id']).iterrows():
        sid=normalize_sleeper_id(row.sleeper_id)
        groups.setdefault(sid,set()).add(str(row.canonical_player_id))
    rows,blocked=[],[]
    for sid,player in sorted(catalog.items()):
        if player.get('position') not in {'QB','RB','WR','TE'} or player.get('sport') not in {None,'nfl'}:
            continue
        # Team absence does not establish zero or current availability. Keep a
        # separate unresolved record; do not silently invent active membership.
        if not player.get('team'):
            blocked.append({'sleeper_id':sid,'reason':'CURRENT_NFL_TEAM_UNVERIFIED'});continue
        ids=groups.get(str(sid),set())
        provider=player.get('gsis_id')
        if provider and str(provider) in set(identity.canonical_player_id.astype(str)):
            ids=ids|{str(provider)}
        if len(ids)!=1:
            blocked.append({'sleeper_id':sid,'reason':'CANONICAL_ID_MISSING_OR_AMBIGUOUS'});continue
        if player.get('player_id') not in {None,str(sid)}:
            raise ValueError('WAIVER_CURRENT_PROVIDER_ID_CONFLICT')
        rows.append({'canonical_player_id':next(iter(ids)),'sleeper_id':str(sid),
                     'position_model':player['position'],'team':player['team']})
    if len({r['canonical_player_id'] for r in rows})!=len(rows):
        raise ValueError('WAIVER_CURRENT_CANONICAL_COLLISION')
    return rows,blocked


def publish(root, envelope, history_path, lock_path):
    source=validate_manifest(root,envelope)
    history=json.loads(history_path.read_text());lock=validate_lock(root,lock_path)
    if history.get('schema')!='fie-waiver-v2-live-history-v1' or history['season']!=source['season'] or history['completed_week']!=source['week']-1:
        raise ValueError('WAIVER_CURRENT_HISTORY_TARGET')
    if history.get('builder_sha256')!=sha(Path(__file__).with_name('prepare_live_waiver_history.py')):
        raise ValueError('WAIVER_CURRENT_HISTORY_OWNER_CHANGED')
    if verified(root,history['source_envelope'],history['prepared_at']).resolve()!=envelope.resolve():
        raise ValueError('WAIVER_CURRENT_HISTORY_SOURCE')
    cutoff=now()
    responses={r['name']:r for r in source['responses']}
    catalog=json.loads(replay_response(root,responses['sleeper_players'],cutoff))
    schedule=pd.read_csv(io.BytesIO(replay_response(root,responses['schedule'],cutoff)))
    from build_current_snapshot import first_kickoff_utc
    first=first_kickoff_utc(schedule,source['season'],source['week']).isoformat()
    destination=root/f"data/research/prospective/waiver-v2/forecasts/{source['season']}/week_{source['week']:02d}"
    canonical=destination/'capture.json'
    if canonical.exists():
        old=json.loads(canonical.read_text())
        for ref in old['bindings'].values():verified(root,ref,old['captured_at'])
        return {'status':'EXISTS','path':str(canonical)}
    if clock(cutoff)>=clock(first):
        path=destination/'attempts'/clock(cutoff).strftime('%Y%m%dT%H%M%S%fZ')/'missed.json'
        write(path,{'status':'MISSED_FIRST_TARGET_KICKOFF','captured_at':cutoff,'first_kickoff':first,
                    'season':source['season'],'week':source['week'],**gates(['BLOCKED_MISSED_CAPTURE'])})
        return {'status':'MISSED','path':str(path)}
    forecasts,coverage,profile_scope=[],[],[]
    for profile in history['profiles']:
        signature=profile['scoring_signature']
        identities=pd.read_csv(verified(root,profile['identity'],cutoff),low_memory=False)
        universe,unresolved=identity_universe(identities,catalog)
        history_rows=pd.read_csv(verified(root,profile['outcomes'],cutoff),low_memory=False)
        stats=pd.read_csv(verified(root,profile['stats'],cutoff),low_memory=False)
        # Current weights must match the lock signature. Retain all other
        # profiles as unsupported; never borrow a Best Ball model for them.
        bound=[]
        for item in source['responses']:
            if item.get('role')=='profile':
                live=json.loads(replay_response(root,item,cutoff))
                if str(live.get('season'))!=str(source['season']):
                    profile_scope.append({'league_id':item['league_id'],'status':'BLOCKED_PROFILE_SEASON'});continue
                if scoring_signature(live['scoring_settings'])==signature:
                    bound.append(item['league_id'])
        coverage.append({'scoring_signature':signature,'cutoff_identity_rows':len(universe),
                         'unresolved_identities':unresolved,'bound_leagues':bound,
                         'whole_nfl_ready_weeks':profile['whole_nfl_ready_weeks']})
        if not bound or history['completed_week'] not in profile['whole_nfl_ready_weeks']:
            profile_scope.append({'scoring_signature':signature,'status':'BLOCKED_PROFILE_OR_COMPLETED_WEEK_PROOF'});continue
        rows=forecast(lock,signature,history_rows,stats,universe,season=source['season'],
                      completed_week=history['completed_week'],captured_at=cutoff,first_kickoff=first)
        forecasts.extend(rows)
    valid=sum(r['forecast_mean'] is not None for r in forecasts)
    at=now()
    if clock(at)>=clock(first):
        raise ValueError('WAIVER_CAPTURE_PROCESSING_CROSSED_KICKOFF')
    for row in forecasts:row['captured_at']=at
    report={'schema':'fie-waiver-v2-prospective-capture-v1','season':source['season'],'week':source['week'],
            'completed_week':history['completed_week'],'target_weeks':list(range(source['week'],source['week']+3)),
            'captured_at':at,'first_kickoff':first,'forecasts':forecasts,'valid_forecast_rows':valid,
            'coverage':coverage,'profile_scope':profile_scope,
            'bindings':{'source_envelope':binding(root,envelope,source['captured_at']),
                        'history':binding(root,history_path,history['prepared_at']),
                        'model_lock':binding(root,lock_path,lock['frozen_at'])},
            'status':'CAPTURED_RESEARCH' if valid else 'BLOCKED_NO_SUPPORTED_FORECASTS',
            'same_cutoff_three_week_sleeper_baseline':'UNAVAILABLE_NOT_INFERRED_FROM_WEEKLY',
            **gates(['BLOCKED_PROSPECTIVE_VALIDATION_REQUIRED','BLOCKED_PROMOTION_REVIEW_REQUIRED'])}
    # Failed source preparations remain retryable inside the genuine window.
    path=canonical if valid else destination/'attempts'/clock(at).strftime('%Y%m%dT%H%M%S%fZ')/'blocked.json'
    write(path,report)
    return {'status':report['status'],'path':str(path),'valid_forecast_rows':valid}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--season',type=int,default=2026);p.add_argument('--week',type=int)
    p.add_argument('--source-envelope',type=Path);p.add_argument('--lock',type=Path)
    a=p.parse_args();week=a.week or resolve_target(a.season)
    if week>16:
        print(json.dumps({'status':'NOT_APPLICABLE_FULL_THREE_WEEK_HORIZON','week':week}));return
    lock=a.lock or a.root/f'data/research/prospective/waiver-v2/locks/{a.season}/revision-1/model-lock.json'
    validate_lock(a.root,lock)
    envelope=a.source_envelope or capture(a.root,a.season,week)
    source=json.loads(envelope.read_text())
    history=prepare(a.root,envelope,a.root/f"data/research/prospective/waiver-v2/history/{a.season}/week_{week:02d}/{clock(now()).strftime('%Y%m%dT%H%M%S%fZ')}")
    print(json.dumps(publish(a.root,envelope,history,lock)))


if __name__=='__main__':main()
