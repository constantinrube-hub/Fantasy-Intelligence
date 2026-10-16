"""Preserve original pregame report outputs for review; never use them to fit."""
import argparse,collections
from pathlib import Path
from recovery_common import *
def build(output,reference_model,root=ROOT):
    lock=read(root/reference_model/'pipeline-lock.json');parent=root/output
    if parent.exists() and any(parent.iterdir()):raise ValueError('NEW_ARCHIVE_EXPORT_REQUIRED')
    sources=['FIE_Step1_Individual_Efficiency_Weeks_6_8_2026-10-15','FIE_Step2_Recovered_Completion_2026-10-15','FIE_Step3_Receiving_Defense_2026-10-15','FIE_Step4_WR_Hierarchy_2026-10-15']
    outputs=[]
    for stage,name in enumerate(sources,1):
        path=root/BASE/'reference'/(name+'.json');d=read(path);keys=d['keys'];model=f'ARCHIVED_STEP_{stage}';folder=parent/f'step{stage}';out=folder/'issuance';out.mkdir(parents=True)
        raw=[]
        for r in d['rows']:
            vals={k:v for k,v in zip(keys,r[10]) if k.startswith('dst_')==(r[2]=='DEF')};raw.append({'model_id':model,'canonical_player_id':r[0],'name':r[1],'position_model':r[2],'season':2026,'week':r[4],'means':{k:v for k,v in vals.items() if not k.startswith(('prob_','dst_prob_'))},'event_probabilities':{k:v for k,v in vals.items() if k.startswith(('prob_','dst_prob_'))},'bye':r[7]})
        scored=[{'model_id':model,'canonical_player_id':r[0],'week':r[1],'league_id':str(r[2]),'mean':r[3],'p10':r[4],'p50':r[5],'p90':r[6]} for r in d['scores']]
        lines(out/'weekly-components.jsonl.gz',raw);lines(out/'weekly-league-scores.jsonl.gz',scored);write(folder/'pipeline-lock.json',lock)
        write(out/'capture-manifest.json',{'model_id':model,'replay_only':False,'issued_at':None,'reference_observation_cutoff':read(root/lock['bundle_path'])['observation_cutoff'],'timing_status':'ORIGINAL_PREGAME_REPORT_OUTPUT_SOURCE_CLOCK_NOT_INDEPENDENTLY_CERTIFIED','source_report_path':path.relative_to(root).as_posix(),'source_report_sha256':sha(path),'original_scenario_archives_not_recovered':True,'artifacts':closure(out,root),'fitting_input':False});outputs.append(folder.relative_to(root))
    return outputs
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reference-model',type=Path,required=True);a=p.parse_args();build(a.output,a.reference_model)
