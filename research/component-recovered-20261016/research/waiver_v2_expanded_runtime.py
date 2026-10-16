"""Additional profile inference from bound sources; no production authority."""
from __future__ import annotations
import argparse,io,json,tempfile
from pathlib import Path
import numpy as np,pandas as pd
from archive_waiver_expansion_sources import BASE,csv
from build_waiver_v2_expansion import methodology
from prospective_research_io import sha,write,now,clock,binding,gates,verified,replay_response
from capture_week6_research_sources import validate_manifest
from run_waiver_v2_historical_ledger import run as source_run
from waiver_v2_scoped_sources import component_sources,profile_outcomes
from capture_prospective_waiver import identity_universe
from waiver_v2_prospective import forecast
from build_waiver_v2_outcome_ledger import scoring_signature

ROOT=Path(__file__).resolve().parents[1]
NAMESPACE='waiver-expanded'
FLAGS=[k for k in gates([]) if k.endswith('_eligible')]
def load_lock(root):
    config=json.loads((root/'config/waiver-v2-expanded-scope.json').read_text());path=root/BASE/'model-lock.json'
    if config['base']!=BASE or sha(path)!=config['model_lock_sha256']:raise ValueError('EXPANDED_LOCK_HASH_OR_NAMESPACE')
    lock=json.loads(path.read_text());contract=methodology(root)
    if lock['schema']!='fie-waiver-v2-expanded-lock-v1' or lock['parameters_selected_from_2026'] is not False or any(lock.get(k) is not False for k in FLAGS):raise ValueError('EXPANDED_LOCK_AUTHORITY')
    expected={(s,p) for s in config['signatures'] for p in contract['positions']}
    if config['signatures']!=contract['signatures'] or len(lock['units'])!=len(expected) or {(x['scoring_signature'],x['position']) for x in lock['units']}!=expected:raise ValueError('EXPANDED_LOCK_UNITS')
    for ref in [lock['methodology'],lock['feature_owner'],lock['source_owner'],*lock['inputs'].values()]:verified(root,ref,lock['frozen_at'])
    for unit in lock['units']:
        if any(unit.get(k) is not False for k in FLAGS):raise ValueError('EXPANDED_UNIT_AUTHORITY')
        model=unit['model']
        if model:
            if not set(model['training_seasons'])<=set(contract['seasons']) or max(model['training_seasons'])>=lock['season']:raise ValueError('EXPANDED_FUTURE_TRAINING')
            n=len(model['columns'])*2
            if any(len(model[k])!=n for k in ['means','scales','coefficients']) or len(model['medians'])!=n//2 or min(model['scales'])<=0:raise ValueError('EXPANDED_MODEL_SHAPE')
            if not np.isfinite([model['intercept'],*model['medians'],*model['means'],*model['scales'],*model['coefficients']]).all():raise ValueError('EXPANDED_MODEL_NONFINITE')
    return lock,path

def prepare(root,envelope,output,completed_week=None):
    source=validate_manifest(root,envelope);lock,_=load_lock(root)
    if output.exists():raise ValueError('EXPANDED_HISTORY_NEW_REVISION_REQUIRED')
    output.mkdir(parents=True);by_name={r['name']:r for r in source['responses']};season=source['season'];through=source['week']-1 if completed_week is None else completed_week
    if not 1<=through<=18 or through>source['week']:raise ValueError('EXPANDED_HISTORY_TARGET')
    required={'players','ff_playerids','player_week','weekly_rosters','schedule','pbp','sleeper_players'}
    if not required<=set(by_name):raise ValueError('EXPANDED_RAW_SOURCE_MISSING')
    if season!=lock['season']:raise ValueError('EXPANDED_SOURCE_SEASON_DRIFT')
    profiles=[]
    with tempfile.TemporaryDirectory(prefix='fie-expanded-live-') as folder:
        temp=Path(folder)
        from fie_research import SourceManager
        manager=SourceManager(temp/'cache')
        for name in required-{'sleeper_players'}:
            year=season if name in {'player_week','weekly_rosters','pbp'} else None
            manager.path_for(name if name!='schedule' else 'schedules',year).write_bytes(replay_response(root,by_name[name],source['captured_at']))
        scoring_ref=lock['profiles'][0]['artifacts']['scoring']
        report=source_run(seasons=[season],cache_dir=temp/'cache',scoring_path=verified(root,scoring_ref,lock['frozen_at']),output_dir=temp/'source',player_stats_complete=False)
        raw=report['source_snapshot'];adapted=report['adapter_receipt']['outputs'];event=report['event_ledger_receipt']
        stats=pd.read_csv(adapted['player_stats']['path'],low_memory=False);stats=stats[stats.week<=through]
        roster=pd.read_csv(adapted['weekly_roster']['path'],low_memory=False);roster=roster[roster.week<=through]
        pbp=pd.read_csv(raw['pbp']['path'],low_memory=False);pbp=pbp[pbp.week<=through]
        games=pd.read_csv(raw['games']['path'],low_memory=False);games=games[games.season.eq(season)&games.week.le(through)]
        identity=pd.read_csv(raw['identity']['path'],low_memory=False)
        events=pd.read_csv(event['event_ledger']['path'],low_memory=False);events=events[events.week<=through]
        blockers=[json.loads(s) for s in Path(event['blockers']['path']).read_text().splitlines() if s];blockers=[b for b in blockers if b['week']<=through]
        allstats=pd.read_csv(adapted['return_reconciliation_stats']['path'],low_memory=False);allstats=allstats[allstats.week<=through]
        weekly,support,excluded=component_sources(pbp,stats,events,event,blockers,allstats)
        write(output/'component-scope.json',{'exclusions':excluded,'effective_support':support,'original_support':event['rule_support']})
        for p in lock['profiles']:
            sig=p['scoring_signature'];settings=json.loads(verified(root,p['artifacts']['scoring'],lock['frozen_at']).read_text())['scoring_settings']
            outcomes,audit,proofs=profile_outcomes(pbp,stats,roster,games,identity,weekly,support,excluded,settings)
            dest=output/sig;dest.mkdir();at=now()
            for name,frame in [('outcomes',outcomes),('stats',stats),('identity',identity),('games',games),('game-proof-audit',audit)]:csv(frame,dest/(name+'.csv.gz'))
            ready=audit.groupby(['season','week']).proof_ready.all()
            profiles.append({'scoring_signature':sig,'outcomes':binding(root,dest/'outcomes.csv.gz',now()),'stats':binding(root,dest/'stats.csv.gz',now()),
                'identity':binding(root,dest/'identity.csv.gz',now()),'games':binding(root,dest/'games.csv.gz',now()),
                'whole_nfl_ready_weeks':[int(w) for (s,w),ok in ready.items() if ok and int(s)==season],
                'zero_proof_blockers':[],'scoped_excluded_rows':int(outcomes.outcome_status.eq('BLOCKED_SCOPED_EVENT_ATTRIBUTION').sum())})
    value={'schema':'fie-waiver-v2-live-history-v1','scope':'ADDITIONAL_COMPONENT_SCOPED','season':season,'completed_week':through,'prepared_at':now(),
        'source_envelope':binding(root,envelope,source['captured_at']),'profiles':profiles,'builder_sha256':sha(Path(__file__)),**gates(['BLOCKED_RESEARCH_ONLY'])}
    write(output/'live-history.json',value);return output/'live-history.json'

def issued_rows(root,lock,source,history,at,first):
    by_name={r['name']:r for r in source['responses']};catalog=json.loads(replay_response(root,by_name['sleeper_players'],source['captured_at']));rows=[];coverage=[]
    for p in history['profiles']:
        sig=p['scoring_signature'];bound=[]
        for ref in source['responses']:
            if ref.get('role')!='profile':continue
            live=json.loads(replay_response(root,ref,source['captured_at']))
            if str(live.get('season'))==str(source['season']) and scoring_signature(live['scoring_settings'])==sig and ref['league_id']!='1400388486179123200':bound.append(ref['league_id'])
        if not bound or source['week']-1 not in p['whole_nfl_ready_weeks']:
            coverage.append({'scoring_signature':sig,'bound_leagues':bound,'status':'BLOCKED_PROFILE_OR_GAME_PROOF'});continue
        identity=pd.read_csv(verified(root,p['identity'],at),low_memory=False);universe,blocked=identity_universe(identity,catalog)
        outcomes=pd.read_csv(verified(root,p['outcomes'],at),low_memory=False);stats=pd.read_csv(verified(root,p['stats'],at),low_memory=False)
        predicted=forecast(lock,sig,outcomes,stats,universe,season=source['season'],completed_week=history['completed_week'],captured_at=at,first_kickoff=first,additional_methodology=methodology(root))
        rows.extend(predicted);coverage.append({'scoring_signature':sig,'bound_leagues':bound,'status':'CAPTURED_RESEARCH','cutoff_rows':len(predicted),'identity_exclusions':blocked})
    return rows,coverage

def publish(root,envelope,history_path):
    source=validate_manifest(root,envelope);lock,lock_path=load_lock(root);history=json.loads(history_path.read_text());at=now()
    if (history['season'],history['completed_week'])!=(source['season'],source['week']-1) or history['builder_sha256']!=sha(Path(__file__)):raise ValueError('EXPANDED_HISTORY_OWNER_OR_CONTEXT')
    if verified(root,history['source_envelope'],history['prepared_at']).resolve()!=envelope.resolve():raise ValueError('EXPANDED_HISTORY_SOURCE_DRIFT')
    dest=root/f'data/research/prospective/{NAMESPACE}/forecasts/{source["season"]}/week_{source["week"]:02d}/capture.json'
    if dest.exists():validate_capture(root,json.loads(dest.read_text()));return {'status':'EXISTS','path':str(dest)}
    ref=next(r for r in source['responses'] if r['name']=='schedule');schedule=pd.read_csv(io.BytesIO(replay_response(root,ref,source['captured_at'])))
    from build_current_snapshot import first_kickoff_utc
    first=first_kickoff_utc(schedule,source['season'],source['week']).isoformat()
    if clock(at)>=clock(first):return {'status':'MISSED_FIRST_TARGET_KICKOFF','first_kickoff':first}
    rows,coverage=issued_rows(root,lock,source,history,at,first);at=now()
    if clock(at)>=clock(first):raise ValueError('EXPANDED_PROCESSING_CROSSED_KICKOFF')
    for r in rows:r['captured_at']=at
    value={'schema':'fie-waiver-v2-prospective-capture-v1','scope':'ADDITIONAL_COMPONENT_SCOPED','season':source['season'],'week':source['week'],
        'target_weeks':list(range(source['week'],source['week']+3)),'captured_at':at,'first_kickoff':first,'status':'CAPTURED_RESEARCH' if rows else 'BLOCKED_NO_FORECASTS',
        'forecasts':rows,'coverage':coverage,'baseline':'SAME_CUTOFF_FP_PRIOR_4',
        'bindings':{'source':binding(root,envelope,source['captured_at']),'history':binding(root,history_path,history['prepared_at']),'model_lock':binding(root,lock_path,lock['frozen_at'])},
        **gates(['BLOCKED_RESEARCH_ONLY','BLOCKED_PROSPECTIVE_CONFIRMATION','BLOCKED_DECISION_DOMAIN','BLOCKED_PROMOTION_REVIEW'])}
    write(dest,value);validate_capture(root,value)
    return {'status':value['status'],'path':str(dest),'forecast_rows':sum(r['forecast_mean'] is not None for r in rows),'abstained_rows':sum(r['forecast_mean'] is None for r in rows)}

def validate_capture(root,value):
    lock,lock_path=load_lock(root);at=value['captured_at']
    if value.get('scope')!='ADDITIONAL_COMPONENT_SCOPED' or value.get('schema')!='fie-waiver-v2-prospective-capture-v1' or any(value.get(k) is not False for k in FLAGS):raise ValueError('EXPANDED_CAPTURE_BOUNDARY')
    if value['target_weeks']!=list(range(value['week'],value['week']+3)) or value['week']>16 or clock(at)>=clock(value['first_kickoff']):raise ValueError('EXPANDED_CAPTURE_HORIZON_OR_TIME')
    if verified(root,value['bindings']['model_lock'],at).resolve()!=lock_path.resolve():raise ValueError('EXPANDED_CAPTURE_LOCK_BINDING')
    source=validate_manifest(root,verified(root,value['bindings']['source'],at));history=json.loads(verified(root,value['bindings']['history'],at).read_text())
    if (source['season'],source['week'])!=(value['season'],value['week']) or (history['season'],history['completed_week'])!=(value['season'],value['week']-1) or history['builder_sha256']!=sha(Path(__file__)):raise ValueError('EXPANDED_CAPTURE_HISTORY_OR_SOURCE_CONTEXT')
    if verified(root,history['source_envelope'],history['prepared_at']).resolve()!=verified(root,value['bindings']['source'],at).resolve():raise ValueError('EXPANDED_CAPTURE_HISTORY_SOURCE')
    ref=next(r for r in source['responses'] if r['name']=='schedule');schedule=pd.read_csv(io.BytesIO(replay_response(root,ref,at)))
    from build_current_snapshot import first_kickoff_utc
    if clock(value['first_kickoff'])!=first_kickoff_utc(schedule,value['season'],value['week']):raise ValueError('EXPANDED_CAPTURE_KICKOFF_DRIFT')
    expected,coverage=issued_rows(root,lock,source,history,at,value['first_kickoff'])
    from validate_waiver_v2_validation import equivalent
    equivalent(value['forecasts'],expected);equivalent(value['coverage'],coverage)
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--source-envelope',type=Path,required=True);a=p.parse_args()
    source=validate_manifest(a.root,a.source_envelope)
    dest=a.root/f'data/research/prospective/{NAMESPACE}/history/{source["season"]}/week_{source["week"]:02d}/{clock(now()).strftime("%Y%m%dT%H%M%S%fZ")}'
    history=prepare(a.root,a.source_envelope,dest);print(json.dumps(publish(a.root,a.source_envelope,history)))
