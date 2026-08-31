#!/usr/bin/env python3
"""Capture/validate pilot equivalence around the unified orchestration layer."""
from __future__ import annotations
import argparse,json,math
from collections import Counter
from pathlib import Path
import pandas as pd
from fie_research_pipeline_contract import ROOT, PILOT_LEAGUE_ID, league_root, load_json, sha256_file, strategy_dir, write_json

def compact_gate(meta):
    if not isinstance(meta,dict): return None
    keys=('status','reason','folds','n_test','v972_prior_gate_status','all_v972_folds_exact_scoring_replay','all_m9_folds_exact_scoring_replay','exact_m9_comparator_gate','football_model_promotion_review_ready','expected_season_points_ready','ppg_mae_head_to_head_gate_vs_exact_m9','expected_season_mae_head_to_head_gate_vs_exact_m9','full_schedule_mae_head_to_head_gate_vs_exact_m9','standalone_noninferiority','weighted_metrics')
    return {k:meta.get(k) for k in keys if k in meta}
def snapshot(lid,season):
    root=league_root(lid);s=strategy_dir(lid,season);stack=load_json(s/'strategy_stack.json',{});v2=load_json(s/'preseason_v2.json',{});v974=load_json(s/'preseason_v974_validation.json',{});v975=load_json(s/'preseason_v975_validation.json',{})
    params=[]
    if (s/'preseason_v975_params.csv').is_file():
        d=pd.read_csv(s/'preseason_v975_params.csv'); cols=[c for c in ('test_season','weight_v972','calibration_enabled','intercept','slope') if c in d.columns]; params=d[cols].where(pd.notna(d),None).to_dict('records')
    return {
      'league_id':str(lid),'season':int(season),
      'm1_m9_hashes':{f'milestone{i}':sha256_file(root/f'milestone{i}.json') for i in range(1,10)},'season_board_sha256':sha256_file(root/'performance'/str(season)/'season_board.csv'),
      'v971_positions':{p:(m or {}).get('status') for p,m in sorted((v2.get('per_position') or {}).items())},
      'v972':(stack.get('phase_readiness') or {}).get('season_projection_v972'),
      'v974':{'status':v974.get('status'),'promotion_review':v974.get('football_model_promotion_review_positions',[]),'expected_ready':v974.get('expected_season_points_ready_positions',[]),'positions':{p:compact_gate(m) for p,m in sorted((v974.get('per_position') or {}).items())}},
      'v975':{'status':v975.get('status'),'promotion_review':v975.get('football_model_promotion_review_positions',[]),'expected_ready':v975.get('expected_season_points_ready_positions',[]),'qb':compact_gate(((v975.get('per_position') or {}).get('QB') or {})),'params':params},
      'market':{'resolved_adp_key':(stack.get('provenance') or {}).get('resolved_adp_key'),'profile_expected_adp_key':(stack.get('provenance') or {}).get('profile_expected_adp_key')},
      'replacement_points':(stack.get('league_value_meta') or {}).get('replacement_points'),
      'governance':{'v974_activation':v974.get('production_activation_allowed'),'v975_activation':v975.get('production_activation_allowed'),'strategy_football_uses_adp':(stack.get('governance') or {}).get('football_model_uses_adp')},
    }
def compare(a,b):
    diffs=[]
    def rec(path,x,y):
        if isinstance(x,dict) and isinstance(y,dict):
            for k in sorted(set(x)|set(y)):
                rec(path+[str(k)],x.get(k),y.get(k))
            return
        if isinstance(x,list) and isinstance(y,list):
            if len(x)!=len(y): diffs.append(('.'.join(path)+'.length',len(x),len(y))); return
            for i,(xx,yy) in enumerate(zip(x,y)): rec(path+[str(i)],xx,yy)
            return
        if isinstance(x,(int,float)) and isinstance(y,(int,float)) and not isinstance(x,bool) and not isinstance(y,bool):
            if math.isfinite(float(x)) and math.isfinite(float(y)) and abs(float(x)-float(y))<=1e-10*max(1,abs(float(x)),abs(float(y))): return
        if x!=y: diffs.append(('.'.join(path),x,y))
    rec([],a,b); return diffs
def main(argv=None):
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    for name in ('capture','validate'):
        p=sub.add_parser(name);p.add_argument('--league-id',default=PILOT_LEAGUE_ID);p.add_argument('--season',type=int,default=2026);p.add_argument('--file',required=True)
    a=ap.parse_args(argv);cur=snapshot(a.league_id,a.season);path=Path(a.file)
    if a.cmd=='capture': write_json(path,cur); print(json.dumps({'status':'captured','league_id':a.league_id,'file':str(path)},indent=2));return 0
    base=load_json(path,{});diffs=compare(base,cur)
    if diffs:
        print(json.dumps({'status':'FAIL','league_id':a.league_id,'difference_count':len(diffs),'differences':diffs[:50]},indent=2,default=str));return 2
    print(json.dumps({'status':'PASS','league_id':a.league_id,'checks':'M1-M9 + V971/V972/V974/V975 + ADP key + replacement exact-equivalence'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
