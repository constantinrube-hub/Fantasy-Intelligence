"""C4 first-write Weeks 6–8 component forecasts and all-league scoring."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import numpy as np
import pandas as pd

from component_registry import ROOT,position_universe
from component_source_contract import position,team
from component_baselines import BASE as MODEL,MODELS,parameters,scenarios
from component_training_view import BASE as TRAINING
from component_scoring import rules_for,score_scenarios,sleeper_comparison,validate_scenarios
from nfl_schedule_time import kickoff_iso
from prospective_research_io import now,clock,sha,write,verified,replay_response
from portfolio_rules import load_portfolio_config,entry_for

METHOD=Path('config/component-baseline-methodology-v1.json')
ALLOWED={'QB','RB','WR','TE','K','DL','LB','DB'}
GSIS=re.compile(r'^00-\d{7}$')

class JsonLines:
    def __init__(self,path):
        self.file=Path(path).open('xb');self.gz=gzip.GzipFile(filename='',mode='wb',fileobj=self.file,mtime=0)
        self.rows=0
    def append(self,value):
        self.gz.write((json.dumps(value,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n').encode());self.rows+=1
    def close(self):self.gz.close();self.file.close()

def snapshot(root,ref,cutoff):
    raw=replay_response(root,ref,cutoff)
    return pd.read_csv(io.BytesIO(raw),low_memory=False,dtype={'sleeper_id':'string'}) if ref['kind']=='csv' else json.loads(raw)

def as_id(value):
    text=str(value).strip().removesuffix('.0')
    return text if text.isdigit() else None

def entry_season(*values):
    for v in values:
        try:
            year=int(float(v))
            if 1990<=year<=2026:return year
        except (TypeError,ValueError):pass
    return None

def universe(catalog,roster,players,bridge,owned):
    """Exact NFL IDs or explicitly separated provider-only identities; no names."""
    roster=roster[roster.season.eq(2026)&roster.week.le(6)].copy()
    latest=int(roster.week.max())
    # NFLverse need not publish a target-week roster for a club on bye.
    # Retain the latest observed club roster, including the prior week for byes.
    latest_club_week=roster.groupby('team',dropna=False).week.transform('max')
    roster=roster[roster.week.eq(latest_club_week)]
    membership=roster.status.isin({'ACT','DEV','E14','EXE','INA','PUP','RES','RSN','SUS'})
    if 'status_description_abbr' in roster:membership|=roster.status_description_abbr.eq('A01')
    roster=roster[membership & roster.gsis_id.astype(str).str.strip().str.fullmatch(GSIS.pattern)].copy()
    rows={};audit=[]
    exact=bridge[bridge.identity_status.eq('EXACT_ONE_TO_ONE')].copy()
    gsis_to_sid=dict(zip(exact.canonical_player_id.astype(str),exact.sleeper_id.astype(str)))
    sid_to_gsis={sid:gsis for gsis,sid in gsis_to_sid.items()}
    players_map={str(r.gsis_id).strip():r._asdict() for r in players.itertuples(index=False) if pd.notna(r.gsis_id)}
    def add(sid,cid,raw_roster=None):
        meta=catalog.get(sid,{})
        p=position(meta.get('position') or (raw_roster or {}).get('position',''))
        eligible=sorted({position(x) for x in meta.get('fantasy_positions',[]) if position(x) in ALLOWED}|({p} if p in ALLOWED else set()))
        if p not in ALLOWED:
            if eligible:p=eligible[0]
            else:return
        gsis=cid if GSIS.fullmatch(cid) else None
        nfl=players_map.get(gsis,{})
        observed=(raw_roster or {})
        meta_team=meta.get('team');observed_team=observed.get('team')
        club=team(meta_team) if meta_team else team(observed_team) if observed_team else None
        nfl_clubs={team(v) for v in roster.team.dropna()}
        if club not in nfl_clubs:club=None
        nfl_pos=position(observed.get('position',p))
        model_pos=nfl_pos if nfl_pos in ALLOWED else p
        rookie=entry_season(nfl.get('rookie_season'),observed.get('rookie_year'),observed.get('entry_year'))
        identity_status='EXACT_GSIS_PROVIDER_BINDING' if gsis else 'EXACT_PROVIDER_ID_GSIS_UNRESOLVED'
        rows[cid]={'canonical_player_id':cid,'gsis_id':gsis,'sleeper_id':sid,
          'name':meta.get('full_name') or observed.get('full_name') or nfl.get('display_name') or sid,
          'position_model':p,'model_position':model_pos,'fantasy_positions':eligible,'team':club,
          'entry_season':rookie,'identity_status':identity_status,'current_roster_week':int(observed['week']) if raw_roster else None,
          'injury_status':meta.get('injury_status'),'provider_status':meta.get('status'),
          'source_roster_status':observed.get('status'),'position_source_disagreement':p!=model_pos}
    for gsis,group in roster.groupby(roster.gsis_id.astype(str).str.strip(),sort=True):
        candidates={as_id(v) for v in group.sleeper_id.dropna()} if 'sleeper_id' in group else set()
        candidates.discard(None)
        mapped=gsis_to_sid.get(gsis)
        if mapped:candidates.add(mapped)
        if len(candidates)!=1:
            audit.append({'canonical_player_id':gsis,'status':'UNRESOLVED_CURRENT_PROVIDER_BINDING','candidates':sorted(candidates)});continue
        sid=next(iter(candidates));meta=catalog.get(sid,{})
        pg=str(meta.get('gsis_id') or '').strip()
        if pg and pg!=gsis:
            audit.append({'canonical_player_id':gsis,'sleeper_id':sid,'status':'CONFLICTING_FRESH_PROVIDER_GSIS'});continue
        teams=set(group.team.dropna().map(team));meta_team=team(meta['team']) if meta.get('team') else None
        selected=group
        if len(teams)>1:
            if meta_team in teams:selected=group[group.team.map(team).eq(meta_team)]
            else:
                audit.append({'canonical_player_id':gsis,'sleeper_id':sid,'status':'AMBIGUOUS_CUTOFF_TEAM'});continue
        add(sid,gsis,selected.iloc[0].to_dict())
    existing={r['sleeper_id']:cid for cid,r in rows.items()}
    for sid in sorted(owned):
        if sid in existing or re.fullmatch(r'[A-Z]{2,3}',sid):continue
        meta=catalog.get(sid)
        if not meta:
            audit.append({'sleeper_id':sid,'status':'OWNED_ID_ABSENT_FROM_FRESH_CATALOG'});continue
        gsis=sid_to_gsis.get(sid)
        pg=str(meta.get('gsis_id') or '').strip()
        if gsis and pg and pg!=gsis:gsis=None
        cid=gsis if gsis and gsis not in rows else 'SLEEPER:'+sid
        add(sid,cid)
    clubs=sorted(set(team(v) for v in roster.team.dropna()))
    for club in clubs:
        candidates=[sid for sid,m in catalog.items() if position(m.get('position'))=='DEF' and team(sid)==club]
        sid=club if club in candidates else candidates[0] if len(candidates)==1 else club
        rows['TEAM:'+club]={'canonical_player_id':'TEAM:'+club,'gsis_id':None,'sleeper_id':sid,'name':club+' D/ST',
             'position_model':'DEF','model_position':'DEF','fantasy_positions':['DEF'],'team':club,
             'entry_season':None,'identity_status':'CANONICAL_TEAM_DEFENSE','current_roster_week':latest,
             'injury_status':None,'provider_status':'TEAM','source_roster_status':'TEAM','position_source_disagreement':False}
    if len([r for r in rows.values() if r['position_model']=='DEF'])!=32:raise ValueError('C4_TEAM_UNIVERSE_NOT_32')
    if len({r['sleeper_id'] for r in rows.values()})!=len(rows):raise ValueError('C4_PROVIDER_FORECAST_UNIVERSE_COLLISION')
    return sorted(rows.values(),key=lambda r:(r['position_model'],r['canonical_player_id'])),audit

def pool_eligibility(entity,constraints,owned=False):
    status='ELIGIBLE';notes=[]
    for constraint in constraints:
        typ=constraint['type'];year=entity['entry_season']
        if typ=='nfl_entry_cohort_floor':
            if year is None:status='UNKNOWN_ENTRY_SEASON';notes.append('Exact NFL entry season unavailable')
            elif year<constraint['minimum_entry_season']:status='INELIGIBLE_COHORT';notes.append('Below fixed NFL entry-season floor')
        elif typ=='cohort_floor_with_legacy_cap':
            if year is None:notes.append('Legacy-cap classification unknown')
            elif year<=constraint['legacy_entry_season_max']:notes.append('Legacy acquisition cap applies; this is a projection, not acquisition advice')
        else:raise ValueError('C4_UNKNOWN_CUSTOM_PLAYER_POOL_RULE')
    return {'status':status,'notes':notes,'retained_owned_exception':owned and status!='ELIGIBLE'}

def projection_map(payload,week):
    rows=payload if isinstance(payload,list) else [{'player_id':sid,'stats':v} for sid,v in payload.items()] if isinstance(payload,dict) else []
    result={};invalid=[]
    for row in rows:
        if not isinstance(row,dict):continue
        if row.get('week') is not None and int(row['week'])!=week:invalid.append('ROW_WEEK_MISMATCH');continue
        if row.get('season') is not None and int(row['season'])!=2026:invalid.append('ROW_SEASON_MISMATCH');continue
        sid=str(row.get('player_id') or '')
        stats=row.get('stats')
        if not sid or not isinstance(stats,dict):continue
        if sid in result:raise ValueError('C4_DUPLICATE_PROVIDER_PROJECTION_ROW')
        result[sid]=stats
    return result,{'target_week':week,'status':'PUBLISHED_RAW_ROWS' if result else 'UNPUBLISHED_OR_NO_USABLE_ROWS',
                   'usable_player_rows':len(result),'invalid_rows':len(invalid),'missing_values_imputed':False}

def game_context(schedule):
    contexts={};first={};games=[]
    selected=schedule[schedule.season.eq(2026)&schedule.game_type.eq('REG')&schedule.week.isin([6,7,8])]
    for row in selected.itertuples(index=False):
        kick=kickoff_iso(row.gameday,row.gametime);week=int(row.week)
        games.append({'game_id':row.game_id,'week':week,'kickoff_at':kick,'home_team':team(row.home_team),'away_team':team(row.away_team)})
        for club,opp in [(row.home_team,row.away_team),(row.away_team,row.home_team)]:
            contexts[(week,team(club))]={'game_id':row.game_id,'opponent':team(opp),'kickoff_at':kick}
        first[week]=min(first.get(week,kick),kick)
    if set(first)!={6,7,8}:raise ValueError('C4_FUTURE_SCHEDULE_INCOMPLETE')
    return contexts,first,games

def verify_first_write(root,path):
    value=json.loads(path.read_text())
    for rel,h in value['artifacts'].items():
        if sha(root/rel)!=h:raise ValueError('C4_FIRST_WRITE_DIVERGENT_BYTES:'+rel)
    for rel,h in value['owners'].items():
        if sha(root/rel)!=h:raise ValueError('C4_RETRY_CODE_CHANGED_NEW_ISSUANCE_REQUIRED')
    if clock(value['issued_at'])>=clock(value['first_target_kickoff']):raise ValueError('C4_RETROSPECTIVE_ISSUANCE')
    return value

def issue(root,bundle_path,model_path=None):
    root=Path(root).resolve();bundle_path=Path(bundle_path).resolve()
    folder=bundle_path.parent/'issuance';manifest_path=folder/'capture-manifest.json'
    if manifest_path.exists():return verify_first_write(root,manifest_path)
    bundle=json.loads(bundle_path.read_text());cutoff=bundle['observation_cutoff'];refs={r['name']:r for r in bundle['responses']}
    needed=set(['schedule','players','weekly_rosters','sleeper_players'])|{lid+'-'+role for lid in bundle['league_ids'] for role in ['profile','rosters','users']}
    if not needed<=set(refs):raise ValueError('C4_CRITICAL_OBSERVATION_MISSING')
    if len(bundle['league_ids'])!=23:raise ValueError('C4_PORTFOLIO_SCOPE')
    folder.mkdir(parents=True,exist_ok=True)
    model_path=Path(model_path or root/MODEL/'model-lock.json').resolve();lock=json.loads(model_path.read_text())
    if lock['owner_sha256']!=sha(Path(__file__).with_name('component_baselines.py')):raise ValueError('C4_MODEL_OWNER_DRIFT')
    if lock['methodology_sha256']!=sha(root/METHOD) or clock(lock['fitted_at'])>clock(cutoff):raise ValueError('C4_MODEL_METHOD_OR_CUTOFF_DRIFT')
    training_manifest=root/TRAINING/'training-view.json'
    if sha(training_manifest)!=lock['training_view_sha256']:raise ValueError('C4_TRAINING_VIEW_DRIFT')
    training=json.loads(training_manifest.read_text())
    for ref in training['sources']:
        verified(root,ref,cutoff)
    for ref in lock['training_files']:
        if sha(root/ref['path'])!=ref['sha256']:raise ValueError('C4_MODEL_TRAINING_DATA_DRIFT')
    data={name:snapshot(root,refs[name],cutoff) for name in ['schedule','players','weekly_rosters','sleeper_players']}
    contexts,first,games=game_context(data['schedule']);actual_start=now()
    target_weeks=[w for w in [6,7,8] if clock(first[w])>clock(actual_start)]
    if not target_weeks:raise ValueError('C4_NO_FUTURE_TARGET_WEEKS')
    contracts=json.loads((root/'config/contracts/runtime-contracts.json').read_text())
    portfolio=load_portfolio_config(root/'config/league-portfolio.json')
    profiles=[];ownership={};users={};user_handle=portfolio['sleeper_username'].casefold()
    for lid in bundle['league_ids']:
        live=snapshot(root,refs[lid+'-profile'],cutoff);rosters=snapshot(root,refs[lid+'-rosters'],cutoff)
        userrows=snapshot(root,refs[lid+'-users'],cutoff)
        if str(live.get('season'))!='2026' or str(live.get('league_id'))!=lid:raise ValueError('C4_LIVE_PROFILE_BINDING')
        configured=entry_for(portfolio,lid) or {}
        positions=sorted(position_universe(live['roster_positions'],contracts))
        profile={'league_id':lid,'league_name':live['name'],'roster_positions':live['roster_positions'],
            'positions':positions,'scoring_settings':live['scoring_settings'],'research_constraints':configured.get('research_constraints',[]),
            'format':configured.get('format'),'source_profile_sha256':refs[lid+'-profile']['sha256'],
            'source_observed_at':refs[lid+'-profile']['observed_at']}
        write(folder/'profiles'/(lid+'.json'),profile);profiles.append(profile)
        user_ids={str(u['user_id']) for u in userrows if str(u.get('display_name','')).casefold()==user_handle or str(u.get('username','')).casefold()==user_handle}
        names={str(u['user_id']):u.get('display_name') or u.get('username') or str(u['user_id']) for u in userrows}
        owned={}
        for r in rosters:
            owner=str(r.get('owner_id'));coowners={str(x) for x in r.get('co_owners') or []}
            for sid in (r.get('players') or [])+(r.get('reserve') or [])+(r.get('taxi') or []):
                sid=str(sid)
                if sid in owned and owned[sid]['roster_id']!=r['roster_id']:raise ValueError('C4_DUPLICATE_LEAGUE_OWNERSHIP')
                owned[sid]={'roster_id':r['roster_id'],'owner_name':names.get(owner,owner),
                            'user_owned':owner in user_ids or bool(coowners&user_ids)}
        ownership[lid]=owned;users[lid]={'matched_user_ids':sorted(user_ids),'user_handle':portfolio['sleeper_username']}
    all_owned={sid for owned in ownership.values() for sid in owned}
    bridge=pd.read_csv(root/'data/research/components/2026-10-14/c0-c1-v1/identity-bridge.csv.gz',dtype={'sleeper_id':'string'})
    entities,identity_audit=universe(data['sleeper_players'],data['weekly_rosters'],data['players'],bridge,all_owned)
    write(folder/'universe.json',{'entities':entities,'identity_audit':identity_audit,'user_bindings':users,
                                'known_owned_provider_ids':len(all_owned),'membership_assumption':'CUTOFF_STATE_HELD_FIXED_THROUGH_HORIZON'})
    projection_maps={};projection_status=[]
    for week in [6,7,8]:
        name='sleeper_projections' if week==6 else 'sleeper_projections_week_'+str(week)
        if name in refs:
            projection_maps[week],status=projection_map(snapshot(root,refs[name],cutoff),week)
            status['source_observed_at']=refs[name]['observed_at'];status['source_sha256']=refs[name]['sha256']
        else:
            projection_maps[week]={};status={'target_week':week,'status':'ENDPOINT_UNAVAILABLE','usable_player_rows':0}
        projection_status.append(status)
    write(folder/'sleeper-projection-coverage.json',projection_status)
    wanted=['canonical_player_id','season','week','position_model','week_state','stat_activity',*lock['components']]
    current=pd.read_csv(root/TRAINING/'training-2026.csv.gz',usecols=wanted,low_memory=False)
    if current.week.gt(5).any():raise ValueError('C4_TARGET_STAT_LEAKAGE')
    histories={cid:g for cid,g in current.groupby('canonical_player_id',sort=False)};empty=current.iloc[0:0]
    writers={name:JsonLines(folder/(name+'.jsonl.gz')) for name in ['weekly-components','weekly-league-scores','three-week-summaries','model-parameters']}
    league_counts=Counter();comparators=Counter();param_fallback=Counter();cohort_counts=Counter();adjustments=0
    for index,entity in enumerate(entities):
        cid=entity['canonical_player_id'];sid=entity['sleeper_id'];pos=entity['position_model'];model_pos=entity['model_position']
        hist=histories.get(cid,empty)
        eligible_profiles=[]
        for profile in profiles:
            lid=profile['league_id'];owned=sid in ownership[lid]
            if not set(entity['fantasy_positions']).intersection(profile['positions']):continue
            eligibility=pool_eligibility(entity,profile['research_constraints'],owned)
            if eligibility['status']!='ELIGIBLE' and not owned:
                cohort_counts[(lid,eligibility['status'])]+=1;continue
            rules=rules_for(profile['scoring_settings'],pos,entity['fantasy_positions'],contracts)
            eligible_profiles.append((profile,rules,eligibility,ownership[lid].get(sid)))
        if not eligible_profiles:continue
        for model in MODELS:
            params=parameters(lock,hist,model_pos,model);param_id=hashlib.sha256((cid+'|'+model).encode()).hexdigest()[:20]
            writers['model-parameters'].append({'parameter_id':param_id,'canonical_player_id':cid,**params})
            param_fallback[(model,pos)]+=int(params['quality']['fallback_components']>0)
            sums={p['league_id']:np.zeros(lock['draws']) for p,_,_,_ in eligible_profiles}
            for week in target_weeks:
                context=contexts.get((week,entity['team']))
                bye=bool(entity['team'] and context is None)
                injury=str(entity['injury_status'] or '').upper();roster_status=str(entity['source_roster_status'] or '').upper()
                availability=1.;assumptions=[]
                if entity['team'] is None:availability=0.;assumptions.append('NO_OBSERVED_CURRENT_TEAM_HELD_UNAVAILABLE')
                if injury in {'IR','PUP','SUSPENDED'} or roster_status in {'PUP','RES'}:
                    availability=0.;assumptions.append('RESERVE_UNAVAILABILITY_CARRIED_THROUGH_THREE_WEEKS_UNCALIBRATED')
                elif injury=='OUT' and week==6:
                    availability=0.;assumptions.append('LATEST_PROVIDER_OUT_CARRIED_FIRST_WEEK_ONLY_UNCALIBRATED')
                samples,audit=scenarios(lock,params,cid,week,bye=bye,availability=availability)
                validate_scenarios(samples,model_pos,bye);adjustments+=audit['constraint_adjusted_cells']
                relevant={c:v for c,v in samples.items() if c.startswith('dst_')==(pos=='DEF')}
                means={c:float(v.mean()) for c,v in relevant.items() if not c.startswith(('prob_','dst_prob_'))}
                probabilities={c:float(v.mean()) for c,v in relevant.items() if c.startswith(('prob_','dst_prob_'))}
                writers['weekly-components'].append({'canonical_player_id':cid,'sleeper_id':sid,'name':entity['name'],
                    'position_model':pos,'model_position':model_pos,'fantasy_positions':entity['fantasy_positions'],
                    'team':entity['team'],'opponent':context['opponent'] if context else None,'game_id':context['game_id'] if context else None,
                    'season':2026,'week':week,'model_id':model,'parameter_id':param_id,'bye':bye,
                    'stat_activity_probability':audit['stat_activity_probability'],'conditional_parameters_ref':param_id,
                    'means':means,'event_probabilities':probabilities,'assumptions':assumptions,
                    'identity_status':entity['identity_status'],'fallback_components':params['quality']['fallback_components'],
                    'intervals_calibrated':False,'provider_semantics_certified':False})
                for profile,rules,eligibility,owned in eligible_profiles:
                    lid=profile['league_id'];draws,score=score_scenarios(samples,rules);sums[lid]+=draws
                    comparator=sleeper_comparison(projection_maps[week].get(sid),rules)
                    shared_keys=set(comparator['contributions'])
                    matched_total=math.fsum(score['contributions'][k]['points'] for k in shared_keys)
                    comparator['fie_matched_term_subtotal']=matched_total if shared_keys else None
                    comparator['matched_term_delta']=matched_total-comparator['supported_subtotal'] if shared_keys else None
                    writers['weekly-league-scores'].append({'league_id':lid,'league_name':profile['league_name'],
                        'canonical_player_id':cid,'sleeper_id':sid,'name':entity['name'],'position_model':pos,
                        'season':2026,'week':week,'model_id':model,'parameter_id':param_id,'bye':bye,
                        'eligibility':eligibility,'ownership':owned,'means':{k:score[k] for k in ['mean','p10','p50','p90']},
                        'contributions':score['contributions'],'scoring_arithmetic_complete':True,
                        'provider_exact_certified':False,'sleeper':comparator,'assumptions':assumptions})
                    league_counts[(lid,week,model,pos)]+=1;comparators[(lid,week,comparator['status'])]+=1
            for profile,_,eligibility,owned in eligible_profiles:
                values=sums[profile['league_id']];total=float(values.mean());weeks=len(target_weeks)
                writers['three-week-summaries'].append({'league_id':profile['league_id'],'canonical_player_id':cid,
                    'sleeper_id':sid,'name':entity['name'],'position_model':pos,'team':entity['team'],
                    'model_id':model,'target_weeks':target_weeks,'sum':total,'mean':total/weeks,
                    'p10_sum':float(np.quantile(values,.1)),'p50_sum':float(np.quantile(values,.5)),
                    'p90_sum':float(np.quantile(values,.9)),'ownership':owned,'eligibility':eligibility,
                    'cross_week_dependence':'INDEPENDENT_CONDITIONAL_SCENARIOS_NO_ROLE_OR_MEDICAL_COVARIANCE',
                    'provider_exact_certified':False,'intervals_calibrated':False})
        if (index+1)%200==0:print('C4_FORECAST_ENTITIES',index+1,'of',len(entities),flush=True)
    for writer in writers.values():writer.close()
    issued=now();first_target=min(first[w] for w in target_weeks)
    if clock(issued)>=clock(first_target):raise ValueError('C4_PROCESSING_CROSSED_FIRST_KICKOFF_NOT_A_PROSPECTIVE_CAPTURE')
    coverage={'league_week_model_position_rows':[{'league_id':lid,'week':week,'model_id':model,'position':p,'rows':n}
                   for (lid,week,model,p),n in sorted(league_counts.items())],
              'comparator_coverage':[{'league_id':lid,'week':w,'status':status,'rows_both_models':n} for (lid,w,status),n in sorted(comparators.items())],
              'fallback_entities':[{'model_id':m,'position':p,'entities':n} for (m,p),n in sorted(param_fallback.items())],
              'pool_exclusions':[{'league_id':lid,'status':status,'rows':n} for (lid,status),n in sorted(cohort_counts.items())],
              'constraint_adjusted_draw_cells':adjustments,'numeric_complete':True,'provider_semantics_certified':False}
    write(folder/'coverage.json',coverage)
    # Comparison attempts are separate from old first-write archives.
    direct={'status':'SEPARATE_FIRST_WRITE_COMPARISON_RECEIPT',
            'receipt_path':(bundle_path.parent/'comparisons'/'direct-comparator-attempt.json').relative_to(root).as_posix(),
            'same_cutoff_required':True,
            'older_captures_policy':'PRESERVED_SECONDARY_UNMATCHED_CUTOFF_COMPARISON'}
    write(folder/'comparison-policy.json',direct)
    artifacts={p.relative_to(root).as_posix():sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='capture-manifest.json'}
    owners={rel:sha(root/rel) for rel in ['research/component_baselines.py','research/component_training_view.py','research/component_scoring.py',
         'research/issue_component_forecasts.py','research/capture_component_observations.py',METHOD.as_posix(),
         'config/component-projection-contract-v1.json','config/contracts/runtime-contracts.json','config/league-portfolio.json']}
    manifest={'schema':'fie-component-prospective-capture-v1','status':'CAPTURED_EXPERIMENTAL_NUMERIC_COMPLETE',
       'season':2026,'intended_target_weeks':[6,7,8],'target_weeks':target_weeks,'missed_target_weeks':[w for w in [6,7,8] if w not in target_weeks],
       'observation_cutoff':cutoff,'issued_at':issued,'first_target_kickoff':first_target,'schedule_games':games,
       'official_schedule_reference':'https://www.nfl.com/schedules/2026/by-week/week-6',
       'enabled_leagues':23,'model_ids':MODELS,'entities_in_universe':len(entities),'rows':{n:w.rows for n,w in writers.items()},
       'model_lock':{'path':model_path.relative_to(root).as_posix(),'sha256':sha(model_path),'fitted_at':lock['fitted_at']},
       'observation_bundle':{'path':bundle_path.relative_to(root).as_posix(),'sha256':sha(bundle_path)},
       'training_view':{'path':training_manifest.relative_to(root).as_posix(),'sha256':sha(training_manifest)},
       'numeric_forecast_complete':True,'provider_scoring_certified':False,'source_semantics_fully_certified':False,
       'calibration_validated':False,'sleeper_forecasts_used_as_features':False,
       'research_only':True,'ranking_eligible':False,'recommendation_eligible':False,'transaction_eligible':False,
       'app_integration':False,'C5_evaluation_started':False,'artifacts':artifacts,'owners':owners,
       'limitations':['MASKED_OUTCOME_SELECTION_CAN_BIAS_PRIORS','STAT_ACTIVITY_PROXY_NOT_MEDICAL_PROBABILITY',
          'MARGINAL_ENTITY_CONSTRAINTS_NOT_NFL_TEAM_BUDGET_MODEL','STATIC_CUTOFF_TEAM_AND_RESERVE_ASSUMPTIONS',
          'SPARSE_PROVIDER_COMPARISON_FIELDS_NOT_ZERO_FILLED','EXPERIMENTAL_UNCALIBRATED_INTERVALS']}
    write(manifest_path,manifest);return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--observation-bundle',type=Path,required=True);p.add_argument('--model-lock',type=Path)
    a=p.parse_args();value=issue(a.root,a.observation_bundle,a.model_lock)
    print(json.dumps({k:value[k] for k in ['status','issued_at','target_weeks','enabled_leagues','rows']}))

if __name__=='__main__':main()
