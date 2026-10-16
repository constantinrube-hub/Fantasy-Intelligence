"""Generate all raw components jointly, then apply each frozen league's scoring.

Replay is explicitly retrospective. New pregame issues require all observations
before the first kickoff, up-to-date training through start_week-1, and a fresh
output directory. The immutable previously merged forecasts are never changed.
"""
import argparse,collections,gzip,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from recovery_common import *
from component_baselines import MODELS,parameters
from component_scoring import rules_for,score_scenarios
from issue_component_forecasts import snapshot,pool_eligibility
JsonLines=AtomicJsonLines
from recovery_population import universe
from component_joint_matchup import profiles_from_pbp,shrink
from component_source_contract import team
from nfl_schedule_time import kickoff_iso
import recovery_engine as engine

def contexts_for(schedule,start,season=2026):
    games=[];contexts={};first={};wanted=list(range(start,start+3))
    for x in schedule[schedule.season.eq(season)&schedule.game_type.eq('REG')&schedule.week.isin(wanted)].itertuples(index=False):
        week=int(x.week);kick=kickoff_iso(x.gameday,x.gametime);a,h=team(x.away_team),team(x.home_team)
        games.append({'game_id':x.game_id,'week':week,'kickoff_at':kick,'away_team':a,'home_team':h})
        for club,opp in [(a,h),(h,a)]:contexts[(week,club)]={'game_id':x.game_id,'opponent':opp,'kickoff_at':kick}
        first[week]=min(first.get(week,kick),kick)
    if set(first)!=set(wanted):raise ValueError('THREE_WEEK_SCHEDULE_INCOMPLETE')
    return contexts,first,games

def prepare(root,bundle_path,through,training_dir=None,replay=False):
    bundle=read(root/bundle_path);refs={r['name']:r for r in bundle['responses']}
    required={'players','weekly_rosters','sleeper_players','schedule','snaps','pbp'}
    if not required<=set(refs):raise ValueError('MISSING_GLOBAL_OBSERVATIONS')
    data={name:snapshot(root,refs[name],bundle['observation_cutoff']) for name in required}
    profile=[];owned={};all_owned=set()
    for lid in bundle['league_ids']:
        lid=str(lid);p=snapshot(root,refs[lid+'-profile'],bundle['observation_cutoff']);profile.append(p)
        rosters=snapshot(root,refs[lid+'-rosters'],bundle['observation_cutoff']);owned[lid]=set()
        for r in rosters:
            owned[lid].update(str(v) for v in (r.get('players') or [])+(r.get('reserve') or [])+(r.get('taxi') or []))
        all_owned|=owned[lid]
    if len(profile)!=23 or len(set(str(p['league_id']) for p in profile))!=23:raise ValueError('EXPECTED_23_DISTINCT_LEAGUES')
    if replay:
        entities=read(root/JOINT/'entities.json')['entities']
    else:
        bridge=pd.read_csv(root/'data/research/components/2026-10-14/c0-c1-v1/identity-bridge.csv.gz',dtype={'sleeper_id':'string'})
        entities,_=universe(data['sleeper_players'],data['weekly_rosters'],data['players'],bridge,all_owned,target_week=through+1)
        snaps=data['snaps'];snaps=snaps[snaps.week.between(max(1,through-3),through)&snaps.game_type.eq('REG')]
        catalog=data['players'].dropna(subset=['pfr_id']);catalog=catalog[~catalog.pfr_id.duplicated(keep=False)]
        mapping=dict(zip(catalog.pfr_id,catalog.gsis_id));snaps=snaps.copy();snaps['cid']=snaps.pfr_player_id.map(mapping)
        means=snaps.groupby('cid')[['offense_pct','defense_pct','st_pct']].mean().to_dict('index')
        for e in entities:
            meta=data['sleeper_players'].get(e['sleeper_id'],{});e['depth_order']=engine.num(meta.get('depth_chart_order'));e['snaps']=means.get(e['canonical_player_id'],{});e['official_status']=None;e['provider_injury']=str(meta.get('injury_status') or '').upper()
    original=read(root/OLD/'capture-manifest.json');model_path=root/original['model_lock']['path'];lock=read(model_path)
    if sha(model_path)!=original['model_lock']['sha256']:raise ValueError('BASE_MODEL_LOCK_DRIFT')
    # The baseline priors stay frozen; recency features use the declared training revision.
    lock=dict(lock);lock['training_through_week']=through
    train=root/(training_dir or TRAINING)/'training-2026.csv.gz';training=pd.read_csv(train,low_memory=False)
    if training.week.max()<through:raise ValueError('TRAINING_NOT_UPDATED_THROUGH_PRIOR_WEEK')
    training=training[training.week.le(through)];histories={cid:g for cid,g in training.groupby('canonical_player_id')}
    previous={r['canonical_player_id']:r for r in rows(root/OLD/'model-parameters.jsonl.gz') if r['model_id']==MODELS[1]}
    ps={e['canonical_player_id']:(previous.get(e['canonical_player_id']) if replay else None) or parameters(lock,histories.get(e['canonical_player_id'],training.iloc[:0]),e['model_position'],MODELS[1]) for e in entities}
    hist=[];hist_refs=[]
    needed={'season_type','game_id','posteam','defteam','week','play_type','game_seconds_remaining','two_point_attempt','pass_attempt','rush_attempt','sack','complete_pass','interception','pass_touchdown','rush_touchdown','first_down_pass','first_down_rush','fumble','fumble_lost','field_goal_attempt','solo_tackle','assist_tackle','qb_hit','safety','passing_yards','rushing_yards','receiver_player_id','desc'}
    for year in range(2021,2026):
        p=root/TRAINING/f'sources/pbp-{year}.csv.gz';receipt=read(p.with_name(f'pbp-{year}.receipt.json'))
        if sha(p)!=receipt['sha256']:raise ValueError('HISTORICAL_PBP_HASH')
        hist.append(pd.read_csv(p,usecols=lambda k:k in needed,low_memory=False));hist_refs.append({'path':p.relative_to(root).as_posix(),'sha256':sha(p)})
    league,_,pools=profiles_from_pbp(pd.concat(hist,ignore_index=True))
    current=data['pbp'];current=current[current.week.le(through)&current.season_type.eq('REG')]
    _,teamgames,_=profiles_from_pbp(current)
    clubs=sorted({e['team'] for e in entities if e['team']});off={};defense={}
    for club in clubs:
        off[club]=shrink([x for x in teamgames if x['team']==club],league);defense[club]=shrink([x for x in teamgames if x['opponent']==club],league)
    return bundle,data,entities,ps,lock,profile,owned,off,defense,pools,hist_refs,train

def generate(output,bundle_path=None,fitted_path=None,start=6,stage=4,training_dir=None,replay=False,root=ROOT,game_limit=None):
    if not 1<=start<=16 or stage not in range(5):raise ValueError('INVALID_TARGET_WINDOW_OR_STAGE')
    output=root/output
    if output.exists() and any(output.iterdir()):raise ValueError('NEW_ISSUANCE_DIRECTORY_REQUIRED')
    bundle_path=Path(bundle_path or JOINT/'observations/observation-bundle.json');fitted_path=Path(fitted_path or BASE/'fit/fitted.json')
    fitted=read(root/fitted_path)
    if fitted['bundle_sha256']!=sha(root/bundle_path) or fitted['through_week']!=start-1:raise ValueError('FIT_SOURCE_OR_CUTOFF_MISMATCH')
    for ref in fitted['training_sources']:verified(root,ref)
    for ref in fitted.get('coefficient_sources',[]):verified(root,ref)
    bundle,data,es,ps,lock,profiles,owned,off,defense,pools,hrefs,training=prepare(root,bundle_path,start-1,training_dir,replay)
    contexts,first,games=contexts_for(data['schedule'],start)
    if game_limit:games=games[:game_limit];contexts={k:v for k,v in contexts.items() if v['game_id'] in {g['game_id'] for g in games}}
    if not replay and (clock(now())>=clock(first[start]) or clock(bundle['observation_cutoff'])>=clock(first[start])):raise ValueError('PREGAME_ISSUANCE_REQUIRED_USE_REPLAY_FOR_AUDIT')
    if replay and (start!=6 or bundle_path!=JOINT/'observations/observation-bundle.json'):raise ValueError('ARCHIVED_REPLAY_ONLY_FOR_FROZEN_WINDOW')
    output.mkdir(parents=True,exist_ok=True);out=output/'issuance';out.mkdir();(out/'draws').mkdir()
    contracts=read(root/'config/contracts/runtime-contracts.json');old_profiles={p.stem:read(p) for p in (root/OLD/'profiles').glob('*.json')}
    model=f'RECOVERED_V2_STAGE_{stage}';groups={club:[e for e in es if e['team']==club] for club in off}
    writers={n:JsonLines(out/(n+'.jsonl.gz')) for n in ['weekly-components','weekly-league-scores','team-ledgers','allocation']};horizon=collections.defaultdict(lambda:np.zeros(engine.N));count=0;checks=0
    write(output/'entities.json',{'entities':es});write(output/'team-parameters.json',{'offense':off,'defense':defense})
    write(output/'pipeline-lock.json',{'fitted_path':fitted_path.as_posix(),'fitted_sha256':sha(root/fitted_path),'bundle_path':bundle_path.as_posix(),'bundle_sha256':sha(root/bundle_path),'training_path':training.relative_to(root).as_posix(),'training_sha256':sha(training),'historical':hrefs,'stage':stage,'replay':replay,'target_weeks':list(range(start,start+3)),'source_version':fitted['version'],'original_WR_training_recovered':False})
    def emit(e,week,samples,context=None):
        nonlocal count
        relevant={k:v for k,v in samples.items() if k.startswith('dst_')==(e['position_model']=='DEF')}
        means={k:float(v.mean()) for k,v in relevant.items() if not k.startswith(('prob_','dst_prob_'))};probs={k:float(v.mean()) for k,v in relevant.items() if k.startswith(('prob_','dst_prob_'))}
        row={**{k:e[k] for k in ['canonical_player_id','sleeper_id','name','position_model','model_position','team','fantasy_positions']},'week':week,'season':2026,'model_id':model,'means':means,'event_probabilities':probs,'opponent':context['opponent'] if context else None,'game_id':context['game_id'] if context else None,'available':engine.available(e,week),'official_status':e['official_status'],'injury_status':e['provider_injury'],'bye':context is None,'weather_used':False,'intervals_calibrated':False}
        writers['weekly-components'].append(row);count+=1
        for p in profiles:
            lid=str(p['league_id']);old=old_profiles[lid];elig=pool_eligibility(e,old['research_constraints'],e['sleeper_id'] in owned[lid])
            if not set(e['fantasy_positions']).intersection(old['positions']) or (elig['status']!='ELIGIBLE' and e['sleeper_id'] not in owned[lid]):continue
            rules=rules_for(p['scoring_settings'],e['position_model'],e['fantasy_positions'],contracts);draws,score=score_scenarios(samples,rules);horizon[(lid,e['canonical_player_id'])]+=draws
            writers['weekly-league-scores'].append({'league_id':lid,'canonical_player_id':e['canonical_player_id'],'name':e['name'],'position_model':e['position_model'],'week':week,'season':2026,'model_id':model,**score})
    for game in games:
        clubs=[game['away_team'],game['home_team']];week=game['week'];engine.configure(fitted,stage,{clubs[0]:clubs[1],clubs[1]:clubs[0]},start)
        rng=np.random.default_rng(int.from_bytes(hashlib.sha256((game['game_id']+'|20261015').encode()).digest()[:8],'big'));pace=rng.lognormal(-.5*.08**2,.08,engine.N)
        arrays={};ledgers={};dw={}
        for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
            arrays[club],ledgers[club],dw[club]=engine.team_events(rng,groups[club],ps,lock,week,off[club],defense[opp],pools,pace);ledgers[club]['week']=week
        engine.finalize_game(rng,clubs,groups,arrays,ledgers,dw,ps,week);checks+=engine.audit_game(clubs,groups,arrays,ledgers)
        atomic_npz(out/'draws'/(game['game_id']+'.npz'),**{club+'__'+k:v.astype(np.float32) for club,a in arrays.items() for k,v in a.items()},**{club+'__ledger_'+k:v for club,l in ledgers.items() for k,v in l.items() if isinstance(v,np.ndarray)})
        writers['allocation'].append({'game_id':game['game_id'],'week':week,'team_entities':{club:[e['canonical_player_id'] for e in groups[club]] for club in clubs}})
        for club in clubs:
            l=ledgers[club];writers['team-ledgers'].append({'game_id':game['game_id'],'week':week,'team':club,'opponent':contexts[(week,club)]['opponent'],'matchup':l['matchup'],'starter':l['starter'],**{k:float(v.mean()) for k,v in l.items() if isinstance(v,np.ndarray) and not k.startswith('event_')}})
            for i,e in enumerate(groups[club]):emit(e,week,{k:v[i] for k,v in arrays[club].items()},contexts[(week,club)])
        print('GENERATED',game['game_id'],stage,flush=True)
    for e in es:
        for week in range(start,start+3):
            if (week,e['team']) not in contexts:emit(e,week,{k:np.zeros(engine.N) for k in lock['components']})
    for w in writers.values():w.close()
    h=JsonLines(out/'three-week-summaries.jsonl.gz')
    for (lid,cid),v in sorted(horizon.items()):h.append({'league_id':lid,'canonical_player_id':cid,'model_id':model,'sum':float(v.mean()),'mean':float(v.mean())/3,'p10_sum':float(np.quantile(v,.1)),'p90_sum':float(np.quantile(v,.9))})
    h.close()
    owners=['recovery_common.py','recovery_parameters.py','recovery_engine.py','recovery_pipeline.py','recovery_population.py','component_baselines.py','component_training_view.py','component_source_contract.py','component_registry.py','component_scoring.py','component_joint_matchup.py','issue_component_forecasts.py']
    manifest={'schema':'fie-component-recovery-issuance-v2','model_id':model,'generated_at':now(),'issued_at':None if replay else now(),'reference_observation_cutoff':bundle['observation_cutoff'],'first_kickoff':first[start],'target_weeks':list(range(start,start+3)),'enabled_leagues':23,'entities':len(es),'weekly_component_rows':count,'league_rows':writers['weekly-league-scores'].rows,'horizon_rows':h.rows,'games':len(games),'draws':engine.N,'draw_checks':checks,'pipeline_lock_sha256':sha(output/'pipeline-lock.json'),'owners':{('research/'+n):sha(root/'research'/n) for n in owners},'artifacts':closure(out,root),'weather_used':False,'research_only':True,'replay_only':replay,'partial_game_fixture':bool(game_limit),'provider_exact_certified':False,'calibrated':False,'limitations':fitted['limitations']}
    write(out/'capture-manifest.json',manifest);print('COMPLETE',count,manifest['league_rows'],flush=True);return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--bundle',type=Path);p.add_argument('--fitted',type=Path);p.add_argument('--start-week',type=int,default=6);p.add_argument('--stage',type=int,default=4);p.add_argument('--training-dir',type=Path);p.add_argument('--replay',action='store_true');p.add_argument('--game-limit',type=int);a=p.parse_args();generate(a.output,a.bundle,a.fitted,a.start_week,a.stage,a.training_dir,a.replay,game_limit=a.game_limit)
