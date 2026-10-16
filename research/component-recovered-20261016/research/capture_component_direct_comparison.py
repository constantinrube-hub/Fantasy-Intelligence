"""Replay the unchanged locked direct owner in a separate comparison namespace."""
from pathlib import Path
import argparse
import json
import traceback
from prospective_research_io import now,clock,sha,write,binding,verified
from capture_week6_research_sources import validate_manifest
from waiver_v2_expanded_runtime import load_lock,prepare,issued_rows
from issue_component_forecasts import snapshot,game_context

ROOT=Path(__file__).resolve().parents[1]

def capture(root,bundle_path):
    root=Path(root).resolve();bundle_path=Path(bundle_path).resolve()
    output=bundle_path.parent/'comparisons';receipt=output/'direct-comparator-attempt.json'
    if receipt.exists():
        value=json.loads(receipt.read_text())
        for ref in value['bindings'].values():verified(root,ref,value['attempted_at'])
        return value
    bundle=json.loads(bundle_path.read_text());envelope=bundle_path.parent/'source-envelope.json'
    source=validate_manifest(root,envelope);cutoff=bundle['observation_cutoff']
    schedule=snapshot(root,next(r for r in bundle['responses'] if r['name']=='schedule'),cutoff)
    _,first,_=game_context(schedule);output.mkdir(exist_ok=True)
    old=[]
    for rel in ['data/research/prospective/waiver-v2/forecasts/2026/week_06/capture.json',
                'data/research/prospective/waiver-expanded/forecasts/2026/week_06/capture.json']:
        path=root/rel
        if path.exists():
            value=json.loads(path.read_text());old.append({'path':rel,'sha256':sha(path),
              'captured_at':value.get('captured_at'),'status':value.get('status'),
              'comparison_class':'OLDER_CUTOFF_SECONDARY_ONLY_PRESERVED'})
    result={'schema':'fie-component-direct-comparison-v1','status':'ATTEMPTING_UNCHANGED_LOCKED_EXPANDED_OWNER',
        'observation_cutoff':cutoff,'target_weeks':[6,7,8],'first_target_kickoff':first[6],
        'bindings':{'observations':binding(root,bundle_path,cutoff),'source_envelope':binding(root,envelope,cutoff)},
        'same_cutoff':True,'coefficients_refitted':False,'original_archives_overwritten':False,
        'older_captures':old,'research_only':True,'production_M9_M10_changed':False,
        'interpretation':'Locked direct fantasy three-week mean and its fp_prior_4 baseline; QB/RB/WR/TE scope only'}
    try:
        lock,lock_path=load_lock(root)
        history_path=prepare(root,envelope,output/'locked-expanded-history',completed_week=5)
        at=now();rows,coverage=issued_rows(root,lock,source,json.loads(history_path.read_text()),at,first[6])
        at=now()
        if clock(at)>=clock(first[6]):raise ValueError('DIRECT_COMPARISON_MISSED_FIRST_KICKOFF')
        path=output/'locked-expanded-forecasts.json'
        write(path,{'issued_at':at,'observation_cutoff':cutoff,'target_weeks':[6,7,8],
                   'forecasts':rows,'coverage':coverage,'research_only':True,'app_integration':False})
        result['bindings'].update(model_lock=binding(root,lock_path,lock['frozen_at']),
          live_history=binding(root,history_path,json.loads(history_path.read_text())['prepared_at']),
          forecasts=binding(root,path,at))
        result.update(status='CAPTURED_SAME_CUTOFF_DIRECT_RESEARCH' if rows else 'BLOCKED_NO_SUPPORTED_DIRECT_ROWS',
                      coverage=coverage,rows=len(rows),numeric_rows=sum(r['forecast_mean'] is not None for r in rows))
    except Exception as error:
        result.update(status='BLOCKED_UNCHANGED_DIRECT_OWNER',reason=str(error),error_type=type(error).__name__)
        (output/'direct-error.log').write_text(traceback.format_exc())
    for original in old:
        if sha(root/original['path'])!=original['sha256']:raise ValueError('ORIGINAL_DIRECT_FIRST_WRITE_CHANGED')
    result['attempted_at']=now();result['owner_sha256']=sha(Path(__file__))
    write(receipt,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--observation-bundle',type=Path,required=True);a=p.parse_args()
    v=capture(a.root,a.observation_bundle);print(json.dumps({k:v[k] for k in ['status','attempted_at']}))
