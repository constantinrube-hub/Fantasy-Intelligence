"""C2–C4 closure gate: frozen bytes, numeric coverage, arithmetic and timing."""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import json
import math
from pathlib import Path
import subprocess
import sys
import numpy as np
from component_registry import ROOT
from component_scoring import rules_for,validate_scenarios
from issue_component_forecasts import verify_first_write,snapshot,game_context,ALLOWED,pool_eligibility
from prospective_research_io import sha,clock,replay_response,verified,now,write
from validate_component_outcomes import validate as c1_validate
from build_component_outcomes import BASE as C1

DEFAULT=Path('data/research/components/2026-10-14/c2-c4-v1/captures/20261014T174651230972Z/issuance/capture-manifest.json')

def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:yield json.loads(line)

def validate(root,path,tests=True):
    root=Path(root).resolve();path=Path(path).resolve();folder=path.parent
    if tests:subprocess.run([sys.executable,'-m','unittest','discover','-s','research','-p','integrity_component_*test.py'],cwd=root,check=True)
    preserved=c1_validate(root,C1,tests=False)
    manifest=verify_first_write(root,path);bundle_path=root/manifest['observation_bundle']['path']
    if sha(bundle_path)!=manifest['observation_bundle']['sha256']:raise ValueError('C4_OBSERVATION_BUNDLE_DRIFT')
    bundle=json.loads(bundle_path.read_text());cutoff=bundle['observation_cutoff']
    for ref in bundle['responses']:replay_response(root,ref,cutoff)
    refs={r['name']:r for r in bundle['responses']}
    schedule=snapshot(root,refs['schedule'],cutoff);_,first,_=game_context(schedule)
    if manifest['target_weeks']!=[6,7,8] or manifest['missed_target_weeks']:raise ValueError('THIS_CLOSURE_REQUIRES_COMPLETE_WEEKS_6_8')
    if clock(manifest['first_target_kickoff'])!=clock(first[6]):raise ValueError('C4_CALENDAR_KICKOFF_DRIFT')
    if not clock(manifest['model_lock']['fitted_at'])<=clock(cutoff)<=clock(manifest['issued_at'])<clock(first[6]):raise ValueError('C4_PROSPECTIVE_CLOCK_ORDER')
    contracts=json.loads((root/'config/contracts/runtime-contracts.json').read_text())
    profiles={p.stem:json.loads(p.read_text()) for p in (folder/'profiles').glob('*.json')}
    if set(profiles)!=set(bundle['league_ids']) or len(profiles)!=23:raise ValueError('C4_NOT_ALL_23_LEAGUES')
    universe=json.loads((folder/'universe.json').read_text());entities={r['canonical_player_id']:r for r in universe['entities']}
    shared={};shared_counts=Counter();params={}
    for row in lines(folder/'model-parameters.jsonl.gz'):
        params[row['parameter_id']]=row
        for value in row['components'].values():
            if value['recent_n']<0 or value['prior_n']<1:raise ValueError('C2_INVALID_PRIOR_OR_RECENT_SUPPORT')
            if value['rate'] is not None and not math.isfinite(value['rate']):raise ValueError('C2_INVALID_RATE')
    for row in lines(folder/'weekly-components.jsonl.gz'):
        key=(row['canonical_player_id'],row['model_id'],row['week'])
        if key in shared or row['parameter_id'] not in params:raise ValueError('C4_COMPONENT_ROW_KEY_OR_PARAMETERS')
        values={**row['means'],**row['event_probabilities']}
        if any(not math.isfinite(v) for v in values.values()):raise ValueError('C4_NONFINITE_COMPONENT')
        if any(not 0<=v<=1 for v in row['event_probabilities'].values()):raise ValueError('C4_INVALID_EVENT_PROBABILITY')
        if row['bye'] and any(v!=0 for v in values.values()):raise ValueError('C4_NONZERO_BYE_PREDICTION')
        all_comps=json.loads((root/manifest['model_lock']['path']).read_text())['components'] if not shared else all_comps
        validate_scenarios({c:np.array([values.get(c,0.)]) for c in all_comps},row['model_position'],row['bye'])
        if row['provider_semantics_certified'] or row['intervals_calibrated']:raise ValueError('C4_UNSUPPORTED_CERTIFICATION')
        shared[key]=row;shared_counts[(row['model_id'],row['week'],row['position_model'])]+=1
    keys=set();sums=Counter();league_counts=Counter();user_owned=Counter();owned_expected=set();comparators=Counter()
    for row in lines(folder/'weekly-league-scores.jsonl.gz'):
        lid=row['league_id'];cid=row['canonical_player_id'];model=row['model_id'];week=row['week'];key=(lid,cid,model,week)
        if key in keys or (cid,model,week) not in shared:raise ValueError('C4_LEAGUE_ROW_KEY')
        keys.add(key);entity=entities[cid];src=shared[(cid,model,week)]
        rules=rules_for(profiles[lid]['scoring_settings'],entity['position_model'],entity['fantasy_positions'],contracts)
        if set(row['contributions'])!={r['scoring_key'] for r in rules}:raise ValueError('C4_OMITTED_APPLICABLE_LEAGUE_SCORING_RULE')
        values={**src['means'],**src['event_probabilities']};total=0.
        for rule in rules:
            expected=values[rule['component']]*rule['weight'];actual=row['contributions'][rule['scoring_key']]['points']
            if not math.isclose(expected,actual,abs_tol=1e-9):raise ValueError('C3_COMPONENT_WEIGHT_ARITHMETIC')
            total+=expected
        if not math.isclose(total,row['means']['mean'],abs_tol=1e-9):raise ValueError('C3_TOTAL_SCORE_ARITHMETIC')
        sums[(lid,cid,model)]+=total;league_counts[(lid,model,week)]+=1
        if row['ownership'] and row['ownership']['user_owned']:user_owned[(lid,model,week)]+=1
        sleeper=row['sleeper'];comparators[(week,sleeper['status'])]+=1
        if sleeper['status']!='EXPLICIT_FIELDS_COMPLETE' and sleeper['points'] is not None:raise ValueError('C4_PARTIAL_PROVIDER_SCORE_REPORTED_COMPLETE')
        if sleeper.get('missing_fields_imputed',False) or sleeper.get('threshold_mean_plug_in_used',False):raise ValueError('C4_INVENTED_PROVIDER_FORECAST')
    summary_keys=set()
    for row in lines(folder/'three-week-summaries.jsonl.gz'):
        key=(row['league_id'],row['canonical_player_id'],row['model_id']);summary_keys.add(key)
        if not math.isclose(sums[key],row['sum'],abs_tol=1e-8) or not math.isclose(row['sum']/3,row['mean'],abs_tol=1e-8):raise ValueError('C3_HORIZON_SUM_MEAN')
    if summary_keys!=set(sums):raise ValueError('C4_MISSING_HORIZON_SUMMARY')
    catalog=snapshot(root,refs['sleeper_players'],cutoff)
    by_sid={r['sleeper_id']:r for r in entities.values()}
    for lid,profile in profiles.items():
        rosters=snapshot(root,refs[lid+'-rosters'],cutoff)
        for roster in rosters:
            for sid in set((roster.get('players') or [])+(roster.get('taxi') or [])+(roster.get('reserve') or [])):
                sid=str(sid);meta=catalog.get(sid,{})
                if sid in by_sid:positions=by_sid[sid]['fantasy_positions']
                else:positions=meta.get('fantasy_positions') or [meta.get('position')]
                if not set(positions).intersection(profile['positions']):continue
                if sid not in by_sid:raise ValueError('C4_OWNED_ELIGIBLE_ID_NOT_FORECAST:'+lid+':'+sid)
                cid=by_sid[sid]['canonical_player_id']
                for m in manifest['model_ids']:
                    for w in [6,7,8]:owned_expected.add((lid,cid,m,w))
        for m in manifest['model_ids']:
            for w in [6,7,8]:
                if not league_counts[(lid,m,w)]:raise ValueError('C4_EMPTY_LEAGUE_WEEK_MODEL')
    if not owned_expected<=keys:raise ValueError('C4_OWNED_ENTITY_MISSING_TARGET_MODEL')
    direct_path=bundle_path.parent/'comparisons/direct-comparator-attempt.json';direct=json.loads(direct_path.read_text())
    if direct['status'].startswith('ATTEMPTING') or direct['observation_cutoff']!=cutoff:raise ValueError('C4_DIRECT_COMPARISON_NOT_CLOSED_SAME_CUTOFF')
    for ref in direct['bindings'].values():verified(root,ref,direct['attempted_at'])
    for old in direct['older_captures']:
        if sha(root/old['path'])!=old['sha256']:raise ValueError('C4_OLD_FIRST_WRITE_REPLACED')
    for k in ['provider_scoring_certified','source_semantics_fully_certified','calibration_validated','sleeper_forecasts_used_as_features',
              'ranking_eligible','recommendation_eligible','transaction_eligible','app_integration','C5_evaluation_started']:
        if manifest[k] is not False:raise ValueError('C4_BOUNDARY:'+k)
    return {'status':'C2_C3_C4_LOCAL_CLOSURE_PASSED','validated_at':now(),'publication_receipt_required_separately':True,
        'capture_manifest_sha256':sha(path),'enabled_leagues':23,'target_weeks':[6,7,8],
        'weekly_component_rows':len(shared),'weekly_league_rows':len(keys),'horizon_rows':len(summary_keys),
        'owned_entity_model_week_rows_verified':len(owned_expected),'all126_raw_responses_verified':len(bundle['responses'])==126,
        'prior_parameters_verified':len(params),'user_owned_rows':[{'league_id':lid,'model_id':m,'week':w,'rows':n} for (lid,m,w),n in sorted(user_owned.items())],
        'league_rows':[{'league_id':lid,'model_id':m,'week':w,'rows':n} for (lid,m,w),n in sorted(league_counts.items())],
        'sleeper_coverage':[{'week':w,'status':s,'rows':n} for (w,s),n in sorted(comparators.items())],
        'direct_comparator_status':direct['status'],'C1_preserved':preserved['status'],
        'numeric_complete':True,'provider_exact_certified':False,'C5_started':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--capture',type=Path,default=DEFAULT);p.add_argument('--report',type=Path);a=p.parse_args()
    result=validate(a.root,a.capture)
    if a.report:write(a.report,result)
    print(json.dumps({k:result[k] for k in ['status','enabled_leagues','target_weeks','weekly_component_rows','weekly_league_rows','owned_entity_model_week_rows_verified','numeric_complete','provider_exact_certified','C5_started']}))
