"""Immutable raw/league forecast freeze and paired completed-week review."""
import argparse,collections,math
from pathlib import Path
import numpy as np
from recovery_common import *
from component_registry import mapping
from component_scoring import rules_for
from issue_component_forecasts import snapshot,projection_map
class Moments:
    def __init__(self):self.n=0;self.absolute=0.;self.square=0.;self.signed=0.;self.nonzero=0
    def append(self,pair):
        p,a=pair;e=p-a;self.n+=1;self.absolute+=abs(e);self.square+=e*e;self.signed+=e;self.nonzero+=a!=0
    def result(self):return {'n':self.n,'mae':self.absolute/self.n if self.n else None,'rmse':math.sqrt(self.square/self.n) if self.n else None,'bias':self.signed/self.n if self.n else None,'nonzero_actuals':self.nonzero}
class ReviewLines(AtomicJsonLines):
    def close(self):
        import gzip,io
        self.gz.close();raw=self.buffer.getvalue()
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
            while f.read(1048576):pass
        atomic_bytes(self.path,raw)
def lines(p,rs):
    w=ReviewLines(p)
    for r in rs:w.append(r)
    w.close()
def metrics(pairs):
    if isinstance(pairs,Moments):return pairs.result()
    if not pairs:return {'n':0,'mae':None,'rmse':None,'bias':None}
    e=np.array([p-a for p,a in pairs]);return {'n':len(e),'mae':float(np.abs(e).mean()),'rmse':float(np.sqrt(np.mean(e*e))),'bias':float(e.mean()),'nonzero_actuals':sum(a!=0 for _,a in pairs)}
def freeze(issuances,output,root=ROOT):
    out=root/output
    if out.exists() and any(out.iterdir()):raise ValueError('NEW_FREEZE_REQUIRED')
    out.mkdir(parents=True,exist_ok=True);sources=[];common=None;seen=set();models=set();row_count=0;writer=ReviewLines(out/'forecasts.jsonl.gz')
    for base in issuances:
        folder=root/base;m=read(folder/'issuance/capture-manifest.json');lock=read(folder/'pipeline-lock.json')
        if common is None:common=lock
        elif lock['bundle_sha256']!=common['bundle_sha256']:raise ValueError('FREEZE_DIFFERENT_OBSERVATION_SNAPSHOTS')
        for rel,h in m['artifacts'].items():
            if sha(root/rel)!=h:raise ValueError('FREEZE_ARTIFACT_DRIFT')
        scored=collections.defaultdict(dict)
        for r in rows(folder/'issuance/weekly-league-scores.jsonl.gz'):scored[(r.get('model_id',m['model_id']),r['canonical_player_id'],r['week'])][r['league_id']]={k:r.get(k) for k in ['mean','p10','p50','p90']}
        for r in rows(folder/'issuance/weekly-components.jsonl.gz'):
            model=r.get('model_id',m['model_id'])
            key=(model,r['canonical_player_id'],r['week'])
            if key in seen:raise ValueError('DUPLICATE_FREEZE_MODEL_PLAYER_WEEK')
            seen.add(key);models.add(model);row_count+=1
            writer.append({'model_id':model,'canonical_player_id':r['canonical_player_id'],'season':r['season'],'week':r['week'],'position_model':r['position_model'],'fantasy_positions':r.get('fantasy_positions',[r['position_model']]),'components':{**r['means'],**r['event_probabilities']},'scores':scored[(model,r['canonical_player_id'],r['week'])],'bye':r['bye'],'replay_only':m['replay_only'],'forecast_at':m.get('issued_at'),'original_cutoff':m['reference_observation_cutoff']})
        sources.append({'path':(base/'issuance/capture-manifest.json').as_posix(),'sha256':sha(folder/'issuance/capture-manifest.json')})
    writer.close();bundle=read(root/common['bundle_path']);profiles=[]
    for ref in bundle['responses']:
        if ref.get('role')=='profile':profiles.append(snapshot(root,ref,bundle['observation_cutoff']))
    write(out/'profiles.json',profiles);receipt={'schema':'fie-component-freeze-v2','built_at':now(),'models':sorted(models),'target_weeks':common['target_weeks'],'rows':row_count,'sources':sources,'bundle_path':common['bundle_path'],'bundle_sha256':common['bundle_sha256'],'artifacts':closure(out,root),'paired_observation_snapshots':True,'research_only':True}
    write(out/'freeze-receipt.json',receipt);return receipt
def review(freeze_dir,actual_dirs,output,root=ROOT):
    out=root/output
    if out.exists() and any(out.iterdir()):raise ValueError('NEW_REVIEW_REVISION_REQUIRED')
    frozen=root/freeze_dir;fr=read(frozen/'freeze-receipt.json')
    for rel,h in fr['artifacts'].items():
        if sha(root/rel)!=h:raise ValueError('FREEZE_DRIFT')
    actual={};refs=[]
    for base in actual_dirs:
        p=root/base;receipt=read(p/'actual-receipt.json')
        for rel,h in receipt['artifacts'].items():
            if sha(root/rel)!=h:raise ValueError('ACTUAL_REVISION_DRIFT')
        for r in rows(p/'actual-components.jsonl.gz'):
            key=(r['canonical_player_id'],r['season'],r['week'])
            if key in actual:raise ValueError('DUPLICATE_ACTUAL_REVISION_SELECT_ONE')
            actual[key]=r
        refs.append({'path':(base/'actual-receipt.json').as_posix(),'sha256':sha(p/'actual-receipt.json')})
    forecast=list(rows(frozen/'forecasts.jsonl.gz'));contracts=read(root/'config/contracts/runtime-contracts.json');profiles=read(frozen/'profiles.json');profilemap={str(p['league_id']):p for p in profiles};entities=read(root/JOINT/'entities.json')['entities'];em={e['canonical_player_id']:e for e in entities}
    out.mkdir(parents=True,exist_ok=True);grouped=collections.defaultdict(Moments);weekly=collections.defaultdict(Moments);paired=collections.defaultdict(dict);errors=ReviewLines(out/'component-errors.jsonl.gz');score_errors=ReviewLines(out/'league-errors.jsonl.gz');unknown=0;matched=0;horizon=collections.defaultdict(list);coverage_intervals=collections.defaultdict(list)
    sleeper={(r['canonical_player_id'],r['season'],r['week']):r for r in forecast if r['model_id']=='SLEEPER_EXPLICIT_FIELDS'};memberships=collections.defaultdict(set)
    for r in forecast:memberships[(r['canonical_player_id'],r['season'],r['week'])].update(r['scores'])
    for r in forecast:
        cid,season,week=r['canonical_player_id'],r['season'],r['week'];a=actual.get((cid,season,week));model=r['model_id'];pos=r['position_model']
        if a is None:unknown+=len(r['components']);continue
        if a['position_model']!=pos:continue
        for component,pred in r['components'].items():
            value=a['components'].get(component)
            if value is None:unknown+=1;continue
            matched+=1;grouped[(model,pos,component)].append((pred,value));weekly[(model,pos,component,week)].append((pred,value));paired[(cid,season,week,pos,component)][model]=(pred,value)
            errors.append({'model_id':model,'canonical_player_id':cid,'season':season,'week':week,'position_model':pos,'component':component,'forecast':pred,'actual':value,'error':pred-value,'actual_basis':a.get('basis',{}).get(component),'replay_only':r['replay_only']})
        for lid,sc in r['scores'].items():
            e=em.get(cid,{'fantasy_positions':[pos]});rules=rules_for(profilemap[lid]['scoring_settings'],pos,r.get('fantasy_positions',e['fantasy_positions']),contracts);missing=[x['component'] for x in rules if x['component'] not in a['components']]
            if missing:continue
            value=math.fsum(x['weight']*a['components'][x['component']] for x in rules);pred=sc['mean'];grouped[(model,pos,'LEAGUE:'+lid)].append((pred,value));weekly[(model,pos,'LEAGUE:'+lid,week)].append((pred,value));paired[(cid,season,week,pos,'LEAGUE:'+lid)][model]=(pred,value)
            score_errors.append({'model_id':model,'league_id':lid,'canonical_player_id':cid,'season':season,'week':week,'position_model':pos,'forecast':pred,'actual':value,'error':pred-value,'replay_only':r['replay_only'],'source_semantics':'DECLARED_ACTUAL_BASIS_NOT_FULL_PROVIDER_CERTIFICATION'})
            horizon[(model,lid,cid,season)].append((week,pred,value))
            if sc.get('p10') is not None and sc.get('p90') is not None:coverage_intervals[(model,pos,lid)].append(sc['p10']<=value<=sc['p90'])
        sr=sleeper.get((cid,season,week))
        if sr:
            for lid in memberships[(cid,season,week)]:
                required=rules_for(profilemap[lid]['scoring_settings'],pos,r.get('fantasy_positions',[pos]),contracts);subset=[x for x in required if x['component'] in sr['components']]
                if not subset or any(x['component'] not in r['components'] or x['component'] not in a['components'] for x in subset):continue
                pred=math.fsum(x['weight']*r['components'][x['component']] for x in subset);value=math.fsum(x['weight']*a['components'][x['component']] for x in subset);component='SLEEPER_MATCHED_LEAGUE:'+lid
                grouped[(model,pos,component)].append((pred,value));weekly[(model,pos,component,week)].append((pred,value));paired[(cid,season,week,pos,component)][model]=(pred,value)
                score_errors.append({'model_id':model,'league_id':lid,'canonical_player_id':cid,'season':season,'week':week,'position_model':pos,'forecast':pred,'actual':value,'error':pred-value,'score_scope':'SLEEPER_MATCHED_COMPONENT_SUBTOTAL','scoring_keys':[x['scoring_key'] for x in subset],'covered_rule_count':len(subset),'full_rule_count':len(required),'replay_only':r['replay_only']})
    groups=[{'model_id':m,'position':pos,'component':comp,**metrics(vals)} for (m,pos,comp),vals in sorted(grouped.items())]
    models=sorted(fr['models']);paired_rows=[];paired_weekly=[]
    for ai,a in enumerate(models):
        for b in models[ai+1:]:
            same=collections.defaultdict(lambda:[Moments(),Moments()]);same_week=collections.defaultdict(lambda:[Moments(),Moments()])
            for key,values in paired.items():
                if a in values and b in values:
                    same[(key[3],key[4])][0].append(values[a]);same[(key[3],key[4])][1].append(values[b]);same_week[(key[3],key[4],key[2])][0].append(values[a]);same_week[(key[3],key[4],key[2])][1].append(values[b])
            for (pos,comp),(aa,bb) in same.items():
                am,bm=metrics(aa),metrics(bb);paired_rows.append({'a':a,'b':b,'position':pos,'component':comp,'n':am['n'],'a_mae':am['mae'],'b_mae':bm['mae'],'delta_mae_a_minus_b':am['mae']-bm['mae']})
            for (pos,comp,week),(aa,bb) in same_week.items():
                am,bm=metrics(aa),metrics(bb);paired_weekly.append({'a':a,'b':b,'position':pos,'component':comp,'week':week,'lead_week':fr['target_weeks'].index(week),'n':am['n'],'a_mae':am['mae'],'b_mae':bm['mae'],'delta_mae_a_minus_b':am['mae']-bm['mae']})
    horizon_rows=[]
    for (model,lid,cid,season),values in horizon.items():
        if sorted(w for w,_,_ in values)!=fr['target_weeks']:continue
        horizon_rows.append({'model_id':model,'league_id':lid,'canonical_player_id':cid,'season':season,'forecast_sum':sum(p for _,p,_ in values),'actual_sum':sum(a for _,_,a in values)})
    errors.close();score_errors.close();lines(out/'paired-comparisons.jsonl.gz',paired_rows);lines(out/'paired-weekly-comparisons.jsonl.gz',paired_weekly);lines(out/'complete-three-week-results.jsonl.gz',horizon_rows)
    result={'schema':'fie-component-review-v2','built_at':now(),'status':'WAITING_FOR_OUTCOMES' if not matched else 'PARTIAL_OUTCOMES' if unknown else 'OBSERVED_COMPONENTS_AVAILABLE','matched_component_values':matched,'unmatched_or_unknown_component_values':unknown,'forecast_rows':len(forecast),'groups':groups,'paired_groups':len(paired_rows),'complete_three_week_rows':len(horizon_rows),'interval_coverage':[{'model_id':k[0],'position':k[1],'league_id':k[2],'n':len(v),'central_80_coverage':sum(v)/len(v)} for k,v in sorted(coverage_intervals.items())],'freeze_receipt_sha256':sha(frozen/'freeze-receipt.json'),'actual_sources':refs,'artifacts':closure(out,root),'missing_actuals_imputed':False,'original_WR_training_recovered':False,'predictive_superiority_claimed':False,'calibration_claimed':False}
    result['weekly_groups']=[{'model_id':m,'position':p,'component':c,'week':w,'lead_week':fr['target_weeks'].index(w),**metrics(v)} for (m,p,c,w),v in sorted(weekly.items())];result['reconstructed_forecast_rows']=sum(r['replay_only'] for r in forecast);result['archived_or_pregame_forecast_rows']=sum(not r['replay_only'] for r in forecast);result['evaluation_scope']='DIAGNOSTIC_ONLY_NO_PROMOTION'
    write(out/'review.json',result);print('REVIEW',result['status'],matched,'matched',flush=True);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    f=sub.add_parser('freeze');f.add_argument('--issuance',nargs='+',type=Path,required=True);f.add_argument('--output',type=Path,required=True)
    r=sub.add_parser('review');r.add_argument('--freeze',type=Path,required=True);r.add_argument('--actual',nargs='*',type=Path,default=[]);r.add_argument('--output',type=Path,required=True)
    a=p.parse_args();freeze(a.issuance,a.output) if a.cmd=='freeze' else review(a.freeze,a.actual,a.output)
