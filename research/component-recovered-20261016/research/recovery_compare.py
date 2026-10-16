"""Compare regenerated outputs with archived report tables without fitting to them."""
import argparse,json,math
from pathlib import Path
from recovery_common import *
def compare(base,reference,output,root=ROOT):
    d=read(root/reference);ks=d['keys'];ref={(r[0],r[4]):dict(zip(ks,r[10])) for r in d['rows']};score={(r[0],r[1],str(r[2])):r[3:7] for r in d['scores']};count=bad=0;max_delta=0;examples=[]
    for r in rows(root/base/'issuance/weekly-components.jsonl.gz'):
        target=ref[(r['canonical_player_id'],r['week'])]
        for k,v in {**r['means'],**r['event_probabilities']}.items():
            count+=1;delta=abs(v-target[k]);max_delta=max(max_delta,delta)
            if delta>1e-10:
                bad+=1
                if len(examples)<12:examples.append({'player':r['name'],'week':r['week'],'component':k,'regenerated':v,'archived':target[k]})
    sn=sb=0;sd=0
    for r in rows(root/base/'issuance/weekly-league-scores.jsonl.gz'):
        expected=score[(r['canonical_player_id'],r['week'],str(r['league_id']))]
        for key,value in zip(['mean','p10','p50','p90'],expected):sn+=1;delta=abs(r[key]-value);sd=max(sd,delta);sb+=delta>1e-10
    value={'status':'EXACT_REPRODUCTION' if not bad and not sb else 'RECONSTRUCTED_MODEL_DIFFERENCES','components_compared':count,'different_components':bad,'maximum_component_difference':max_delta,'score_values_compared':sn,'different_score_values':sb,'maximum_score_difference':sd,'examples':examples,'reference_path':reference.as_posix(),'reference_sha256':sha(root/reference),'fitted_to_forecast_outputs':False}
    write(root/output,value);print(json.dumps({k:v for k,v in value.items() if k!='examples'}));return value
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();compare(a.base,a.reference,a.output)
