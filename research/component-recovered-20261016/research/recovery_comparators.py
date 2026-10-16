"""Same-observation Basic B0/B1 and explicit-field Sleeper research baselines."""
import argparse,collections
from pathlib import Path
import numpy as np
import pandas as pd
from recovery_common import *
from recovery_pipeline import prepare,contexts_for
from recovery_engine import configure,available
from component_baselines import MODELS,parameters,scenarios
from component_scoring import rules_for,score_scenarios,sleeper_comparison
from component_registry import mapping
from issue_component_forecasts import snapshot,pool_eligibility,projection_map
JsonLines=AtomicJsonLines
def generate(output,reference,root=ROOT):
    out=root/output
    if out.exists() and any(out.iterdir()):raise ValueError('NEW_COMPARATOR_REVISION_REQUIRED')
    lockref=read(root/reference/'pipeline-lock.json');bundle_path=Path(lockref['bundle_path']);fitted=read(root/lockref['fitted_path']);start=lockref['target_weeks'][0]
    bundle,data,es,unused,lock,profiles,owned,off,defense,pools,hrefs,train=prepare(root,bundle_path,start-1,Path(lockref['training_path']).parent,lockref['replay'])
    contexts,first,games=contexts_for(data['schedule'],start);configure(fitted,0,{},start)
    history=pd.read_csv(train,low_memory=False);history=history[history.week.le(start-1)];hs={k:g for k,g in history.groupby('canonical_player_id')}
    refs={r['name']:r for r in bundle['responses']};projections={};coverage=[]
    for week in lockref['target_weeks']:
        names=[f'sleeper_projections_week_{week}']+(['sleeper_projections'] if week==6 else [])
        ref=next((refs[x] for x in names if x in refs),None)
        if ref:projections[week],receipt=projection_map(snapshot(root,ref,bundle['observation_cutoff']),week);coverage.append(receipt)
        else:projections[week]={};coverage.append({'week':week,'status':'NO_PUBLISHED_PROJECTION'})
    out.mkdir(parents=True,exist_ok=True);folder=out/'issuance';folder.mkdir();raw=JsonLines(folder/'weekly-components.jsonl.gz');scores=JsonLines(folder/'weekly-league-scores.jsonl.gz');contracts=read(root/'config/contracts/runtime-contracts.json');old={p.stem:read(p) for p in (root/OLD/'profiles').glob('*.json')};missing_scores=0
    for e in es:
        cid=e['canonical_player_id'];pos=e['position_model'];ps={model:parameters(lock,hs.get(cid,history.iloc[:0]),e['model_position'],model) for model in MODELS}
        for week in lockref['target_weeks']:
            bye=(week,e['team']) not in contexts
            batches={}
            for model in MODELS:
                samples,_=scenarios(lock,ps[model],cid,week,bye=bye,availability=float(available(e,week)))
                relevant={k:v for k,v in samples.items() if k.startswith('dst_')==(pos=='DEF')};means={k:float(v.mean()) for k,v in relevant.items() if not k.startswith(('prob_','dst_prob_'))};probs={k:float(v.mean()) for k,v in relevant.items() if k.startswith(('prob_','dst_prob_'))}
                raw.append({'model_id':model,'canonical_player_id':cid,'season':2026,'week':week,'position_model':pos,'fantasy_positions':e['fantasy_positions'],'means':means,'event_probabilities':probs,'bye':bye});batches[model]=samples
            stats=projections[week].get(e['sleeper_id']);sraw={}
            if stats is not None:
                for key,value in stats.items():
                    if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value):continue
                    try:spec=mapping(key,contracts)
                    except ValueError:continue
                    if spec['mode']=='probability' and not 0<=value<=1:continue
                    sraw[spec['component']]=float(value)
                if 'rec_tgt' in stats:sraw['targets']=float(stats['rec_tgt'])
            raw.append({'model_id':'SLEEPER_EXPLICIT_FIELDS','canonical_player_id':cid,'season':2026,'week':week,'position_model':pos,'fantasy_positions':e['fantasy_positions'],'means':{k:v for k,v in sraw.items() if not k.startswith(('prob_','dst_prob_'))},'event_probabilities':{k:v for k,v in sraw.items() if k.startswith(('prob_','dst_prob_'))},'bye':bye})
            for p in profiles:
                lid=str(p['league_id']);constraints=old[lid];elig=pool_eligibility(e,constraints['research_constraints'],e['sleeper_id'] in owned[lid])
                if not set(e['fantasy_positions']).intersection(constraints['positions']) or (elig['status']!='ELIGIBLE' and e['sleeper_id'] not in owned[lid]):continue
                rules=rules_for(p['scoring_settings'],pos,e['fantasy_positions'],contracts)
                for model,samples in batches.items():
                    _,score=score_scenarios(samples,rules);scores.append({'model_id':model,'canonical_player_id':cid,'week':week,'season':2026,'league_id':lid,**score})
                comp=sleeper_comparison(stats,rules)
                if comp['points'] is not None:scores.append({'model_id':'SLEEPER_EXPLICIT_FIELDS','canonical_player_id':cid,'week':week,'season':2026,'league_id':lid,'mean':comp['points'],'p10':None,'p50':None,'p90':None,'raw_coverage':comp['status']})
                else:missing_scores+=1
    raw.close();scores.close();write(out/'pipeline-lock.json',lockref)
    write(folder/'capture-manifest.json',{'schema':'fie-component-comparator-issuance-v2','model_id':'BASIC_AND_SLEEPER','model_ids':[*MODELS,'SLEEPER_EXPLICIT_FIELDS'],'generated_at':now(),'replay_only':lockref['replay'],'issued_at':None if lockref['replay'] else now(),'reference_observation_cutoff':bundle['observation_cutoff'],'artifacts':closure(folder,root),'provider_projection_coverage':coverage,'sleeper_incomplete_league_scores':missing_scores,'missing_projection_values_imputed':False,'owner_sha256':sha(Path(__file__))});print('COMPARATORS_READY',raw.rows,scores.rows,missing_scores,'incomplete Sleeper scores',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);a=p.parse_args();generate(a.output,a.reference)
