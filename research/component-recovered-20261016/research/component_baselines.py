"""Frozen B0/B1 parameters, source-bound priors, and coherent entity scenarios."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from component_registry import ROOT, build
from component_training_view import BASE as TRAINING
from prospective_research_io import now, write, sha, clock

BASE=Path('data/research/components/2026-10-14/c2-c4-v1/model')
METHOD=Path('config/component-baseline-methodology-v1.json')
MODELS=['B0_ROLLING_COMPONENTS_V1','B1_SHRUNK_VOLUME_RATE_V1']
RATE_PARENT={
 'passing_completions':'passing_attempts','passing_interceptions':'passing_attempts',
 'passing_touchdowns':'passing_attempts','passing_first_downs':'passing_attempts',
 'passing_two_point_conversions':'passing_attempts','passing_pick_sixes':'passing_interceptions',
 'passing_completions_40_plus':'passing_completions',
 'passing_touchdowns_40_plus':'passing_touchdowns','passing_touchdowns_50_plus':'passing_touchdowns_40_plus',
 'rushing_touchdowns':'rushing_attempts','rushing_first_downs':'rushing_attempts',
 'rushing_two_point_conversions':'rushing_attempts','rushes_40_plus':'rushing_attempts',
 'rushing_touchdowns_40_plus':'rushing_touchdowns','rushing_touchdowns_50_plus':'rushing_touchdowns_40_plus',
 'receptions':'targets','receiving_touchdowns':'receptions','receiving_first_downs':'receptions',
 'receiving_two_point_conversions':'receptions','receptions_40_plus':'receptions',
 'receiving_touchdowns_40_plus':'receiving_touchdowns','receiving_touchdowns_50_plus':'receiving_touchdowns_40_plus',
 'fumbles_lost':'fumbles',
}
YARD_PARENT={
 'passing_yards':'passing_completions','rushing_yards':'rushing_attempts',
 'receiving_yards':'receptions','kick_return_yards':'kick_returns','punt_return_yards':'punt_returns',
 'idp_sack_yards':'idp_sacks','idp_interception_return_yards':'idp_interceptions',
 'idp_fumble_return_yards':'idp_fumble_recoveries','dst_interception_return_yards':'dst_interceptions',
 'dst_fumble_return_yards':'dst_fumble_recoveries',
 'passing_air_yards':'passing_attempts','receiving_air_yards':'targets',
 'receiving_yards_after_catch':'receptions',
}
FG_BANDS=['0_19','20_29','30_39','40_49','50_59','60p']
DISTANCE_MID={'0_19':16.,'20_29':25.,'30_39':35.,'40_49':45.,'50_59':55.,'60p':63.}
POINT_BANDS={'0':(0,0),'1_6':(1,6),'7_13':(7,13),'14_20':(14,20),'21_27':(21,27),'28_34':(28,34),'35p':(35,None)}
MEAN_DERIVED={'idp_tackles_total','kicker_fgm','kicker_fgm_50p','kicker_fgm_yds','kicker_fgmiss',
              'kicker_field_goal_attempts','kicker_extra_point_attempts',
              'source_passing_first_downs_including_td','source_rushing_first_downs_including_td','source_receiving_first_downs_including_td'}

def role(position,value):
    if not math.isfinite(float(value)):return 'UNKNOWN'
    value=float(value)
    if position=='DEF':return 'TEAM'
    if position=='K':return 'KICKER'
    lo,hi=(5,20) if position=='QB' else (2,10) if position=='RB' else (2,5) if position in {'WR','TE'} else (2,5)
    if value<=0:return 'ZERO'
    if value<=lo:return 'LOW'
    if value<=hi:return 'ROTATION'
    return 'HIGH'

def role_workload(frame):
    result=pd.Series(np.nan,index=frame.index,dtype=float)
    for pos,fields in {'QB':['passing_attempts'],'RB':['rushing_attempts','targets'],
                      'WR':['targets'],'TE':['targets'],'K':['kicker_field_goal_attempts'],
                      'DL':['idp_tackles_total'],'LB':['idp_tackles_total'],'DB':['idp_tackles_total']}.items():
        data=frame.reindex(columns=fields).apply(pd.to_numeric,errors='coerce')
        result.loc[frame.position_model.eq(pos)]=data.sum(axis=1,min_count=len(fields)).loc[frame.position_model.eq(pos)]
    result.loc[frame.position_model.eq('DEF')]=1.
    return result

def lagged_roles(frame):
    """Calendar-keyed lookback; target outcomes are never role features."""
    result=frame.copy();result['_workload']=role_workload(result)
    key=['canonical_player_id','season','week'];past=result[key+['_workload']]
    sums=pd.Series(0.,index=result.index);counts=pd.Series(0.,index=result.index)
    for lag in range(1,5):
        previous=past.copy();previous.week+=lag
        joined=result[key].merge(previous,on=key,how='left',validate='one_to_one')
        val=joined._workload
        sums+=val.fillna(0).to_numpy();counts+=val.notna().astype(int).to_numpy()
    average=sums.div(counts.replace(0,np.nan))
    result['lagged_workload']=average
    result['lagged_role']=[role(p,v) for p,v in zip(result.position_model,average)]
    return result.drop(columns='_workload')

def summary(values,exposure=None):
    values=pd.to_numeric(values,errors='coerce');values=values[np.isfinite(values)]
    n=len(values)
    if not n:return None
    positive=values[values.ne(0)]
    out={'n':n,'zero_exposures':int(values.eq(0).sum()),'nonzero_exposures':len(positive),
         'sum':float(values.sum()),'mean':float(values.mean()),
         'std':float(values.std(ddof=0)),'activity_rate':float(values.ne(0).mean()),
         'nonzero_mean':float(positive.mean()) if len(positive) else 0.,
         'nonzero_std':float(positive.std(ddof=0)) if len(positive) else 0.}
    if exposure is not None:
        exp=pd.to_numeric(exposure,errors='coerce').reindex(values.index)
        ok=exp.notna()&np.isfinite(exp)&exp.ge(0)
        # Nonzero production with zero parent exposure cannot enter a rate fit.
        ok &= ~((exp.eq(0))&values.ne(0))
        numerator=values.loc[ok];denominator=exp.loc[ok]
        out['paired_exposure_rows']=int(ok.sum());out['exposure_sum']=float(denominator.sum())
        out['rate_numerator']=float(numerator.sum())
        out['rate']=float(numerator.sum()/denominator.sum()) if denominator.sum()>0 else None
        positive_exp=denominator.gt(0)
        residual=numerator.loc[positive_exp]-denominator.loc[positive_exp]*(out['rate'] or 0.)
        out['per_opportunity_residual_scale']=float(np.sqrt((residual**2).sum()/denominator.loc[positive_exp].sum())) if positive_exp.any() else 0.
    return out

def fit(root,output=BASE):
    root=Path(root).resolve();folder=root/output;folder.mkdir(parents=True,exist_ok=True)
    model_path=folder/'model-lock.json'
    if model_path.exists():
        old=json.loads(model_path.read_text())
        if old['owner_sha256']!=sha(Path(__file__)) or old['methodology_sha256']!=sha(root/METHOD):
            raise ValueError('COMPONENT_MODEL_NEW_REVISION_REQUIRED')
        for ref in old['training_files']:
            if sha(root/ref['path'])!=ref['sha256']:raise ValueError('COMPONENT_MODEL_TRAINING_DRIFT')
        return old
    method=json.loads((root/METHOD).read_text());training=json.loads((root/TRAINING/'training-view.json').read_text())
    frames=[];refs=[]
    for year in [*method['historical_seasons'],method['current_season']]:
        path=root/TRAINING/f'training-{year}.csv.gz'
        wanted=['canonical_player_id','season','week','position_model','week_state','stat_activity',*training['components']]
        frame=pd.read_csv(path,usecols=wanted,low_memory=False)
        if not frame.season.eq(year).all() or (year==method['current_season'] and frame.week.gt(method['training_through_week']).any()):
            raise ValueError('COMPONENT_FUTURE_TRAINING_REJECTED')
        frames.append(frame);refs.append({'path':path.relative_to(root).as_posix(),'sha256':sha(path)})
    all_rows=lagged_roles(pd.concat(frames,ignore_index=True))
    all_rows=all_rows[all_rows.week_state.eq('COMPLETED_GAME')].copy()
    all_rows=all_rows[all_rows.position_model.isin(['QB','RB','WR','TE','K','DL','LB','DB','DEF'])]
    components=training['components'];pools={};support=[]
    for pos,group in all_rows.groupby('position_model',sort=True):
        subsets={'POSITION':group}
        subsets.update({'ROLE:'+r:g for r,g in group.groupby('lagged_role',sort=True)})
        for label,frame in subsets.items():
            pool={}
            activity=summary(frame.stat_activity)
            if activity:pool['_stat_activity']=activity
            # Conditional production and unconditional raw summaries are both
            # retained. Each component reports its own actual exposure mask.
            for comp in components:
                relevant=comp.startswith('dst_') if pos=='DEF' else not comp.startswith('dst_')
                if not relevant:continue
                source=frame[frame.stat_activity.eq(1)] if pos!='DEF' else frame
                parent=RATE_PARENT.get(comp) or YARD_PARENT.get(comp)
                data=summary(source[comp],source[parent] if parent in source else None)
                unconditional=summary(frame[comp])
                if data is None and unconditional is not None:
                    # All observed labels are zero: a declared zero conditional
                    # prior is still backed by actual observed zero exposure.
                    data=unconditional.copy();data['conditional_zero_prior']=True
                if data:
                    data['unconditional']=unconditional;pool[comp]=data
                    support.append({'position':pos,'pool':label,'component':comp,'conditional_n':data['n'],
                                    'zero_exposures':data['zero_exposures'],'nonzero_exposures':data['nonzero_exposures'],
                                    'mean':data['mean'],'rate':data.get('rate')})
            pools[pos+'|'+label]=pool
    # Entity-family fallback is trained, never an invented numeric constant.
    for family,frame in [('PLAYER',all_rows[all_rows.position_model.ne('DEF')]),('DEF',all_rows[all_rows.position_model.eq('DEF')])]:
        pool={};activity=summary(frame.stat_activity)
        if activity:pool['_stat_activity']=activity
        source=frame[frame.stat_activity.eq(1)]
        for comp in components:
            if comp.startswith('dst_')!=(family=='DEF'):continue
            parent=RATE_PARENT.get(comp) or YARD_PARENT.get(comp)
            data=summary(source[comp],source[parent] if parent in source else None)
            if data is None:data=summary(frame[comp])
            if data:pool[comp]=data
        pools['FAMILY|'+family]=pool
    # Borrow a fixed four-observation prior from the next validated population,
    # including for zero-only rare-event strata. Raw supports remain auditable.
    for pos in ['QB','RB','WR','TE','K','DL','LB','DB','DEF']:
        family=pools['FAMILY|'+('DEF' if pos=='DEF' else 'PLAYER')]
        coarse=pools.get(pos+'|POSITION',{})
        for comp,data in coarse.items():
            higher=family.get(comp)
            if higher:
                data['unsmoothed_mean']=data['mean']
                data['mean']=(data['sum']+4*higher['mean'])/(data['n']+4)
                data['hierarchical_prior_population']='FAMILY|'+('DEF' if pos=='DEF' else 'PLAYER')
                if data.get('rate') is not None and higher.get('rate') is not None:
                    data['rate']=(data.get('rate_numerator',0.)+20*higher['rate'])/(data.get('exposure_sum',0.)+20)
        for key,pool in pools.items():
            if not key.startswith(pos+'|ROLE:'):continue
            for comp,data in pool.items():
                higher=coarse.get(comp) or family.get(comp)
                if higher:
                    data['unsmoothed_mean']=data['mean']
                    data['mean']=(data['sum']+4*higher['mean'])/(data['n']+4)
                    data['hierarchical_prior_population']=pos+'|POSITION'
                    if data.get('rate') is not None and higher.get('rate') is not None:
                        data['rate']=(data.get('rate_numerator',0.)+20*higher['rate'])/(data.get('exposure_sum',0.)+20)
    missing=[]
    for pos in ['QB','RB','WR','TE','K','DL','LB','DB','DEF']:
        for comp in components:
            if comp.startswith('dst_')!=(pos=='DEF'):continue
            if not any(comp in pools.get(k,{}) for k in [pos+'|POSITION','FAMILY|'+('DEF' if pos=='DEF' else 'PLAYER')]):missing.append((pos,comp))
    if missing:raise ValueError('COMPONENT_PRIOR_UNAVAILABLE:'+str(missing[:10]))
    from build_component_outcomes import csv
    csv(pd.DataFrame(support),folder/'prior-support.csv.gz')
    value={'schema':'fie-component-baselines-lock-v1','model_ids':MODELS,'fitted_at':now(),
           'methodology_sha256':sha(root/METHOD),'owner_sha256':sha(Path(__file__)),
           'training_view_sha256':sha(root/TRAINING/'training-view.json'),'training_files':refs,
           'components':components,'pools':pools,'training_seasons':sorted(set(all_rows.season.astype(int))),
           'training_through_week':method['training_through_week'],'random_seed':method['random_seed'],
           'draws':method['draws_per_entity_week_model'],'sleeper_projection_feature_use':False,
           'source_semantics_fully_certified':False,'research_only':True,'transaction_eligible':False,
           'versions':{'numpy':np.__version__,'pandas':pd.__version__}}
    write(model_path,value);return value

def prior_for(lock,position,lagged_role,component):
    keys=[position+'|ROLE:'+lagged_role,position+'|POSITION','FAMILY|'+('DEF' if position=='DEF' else 'PLAYER')]
    for key in keys:
        data=lock['pools'].get(key,{}).get(component)
        if data is not None and data['n']>0:return data,key
    raise ValueError('COMPONENT_NO_VALIDATED_PRIOR:'+position+':'+component)

def parameters(lock,history,position,model):
    frame=history.sort_values('week').copy()
    recent=frame[frame.week.between(lock['training_through_week']-3,lock['training_through_week'])]
    workload=role_workload(recent).dropna()
    label=role(position,float(workload.mean()) if len(workload) else np.nan)
    prior,activity_pool=prior_for(lock,position,label,'_stat_activity')
    activity_history=recent if model==MODELS[0] else recent[recent.week_state.eq('COMPLETED_GAME')]
    active=pd.to_numeric(activity_history.stat_activity,errors='coerce').dropna() if len(activity_history) else pd.Series(dtype=float)
    if position=='DEF':probability=1.
    elif model==MODELS[0] and len(active):probability=float(active.mean())
    else:probability=float((active.sum()+4*prior['mean'])/(len(active)+4))
    out={};quality={'role':label,'recent_calendar_weeks':[2,3,4,5],'observed_activity_weeks':len(active),
                    'activity_prior_pool':activity_pool,'activity_probability':probability,'fallback_components':0,
                    'source_proxy_or_missingness_limits':True}
    for component in lock['components']:
        if component.startswith('dst_')!=(position=='DEF'):continue
        prior,pool=prior_for(lock,position,label,component)
        unconditional=pd.to_numeric(recent.get(component,pd.Series(dtype=float)),errors='coerce').dropna()
        observed=recent[recent.stat_activity.eq(1)] if position!='DEF' else recent
        values=pd.to_numeric(observed.get(component,pd.Series(dtype=float)),errors='coerce').dropna()
        if model==MODELS[0] and len(unconditional):
            raw_mean=float(unconditional.mean())
            mean=raw_mean/max(probability,1e-9) if probability>0 else 0.
            provenance='RECENT_RAW_COMPONENT_MEAN'
        else:
            mean=float((values.sum()+4*prior['mean'])/(len(values)+4))
            raw_mean=mean*probability;provenance='SHRUNK_CONDITIONAL_MEAN' if len(values) else 'POOLED_PRIOR_ONLY'
        parent=RATE_PARENT.get(component) or YARD_PARENT.get(component)
        rate=prior.get('rate');exposure=0.;numerator=0.;paired_n=0
        if parent and parent in observed:
            child=pd.to_numeric(observed[component],errors='coerce');den=pd.to_numeric(observed[parent],errors='coerce')
            mask=child.notna()&den.notna()&den.ge(0)&~(den.eq(0)&child.ne(0))
            exposure=float(den[mask].sum());numerator=float(child[mask].sum());paired_n=int(mask.sum())
            if model==MODELS[0] and exposure>0:rate=numerator/exposure
            elif rate is not None:rate=(numerator+20*rate)/(exposure+20)
            elif exposure>0:rate=numerator/exposure
        if provenance=='POOLED_PRIOR_ONLY' or not len(unconditional):quality['fallback_components']+=1
        if not all(math.isfinite(v) for v in [mean,raw_mean,prior['std']]):raise ValueError('COMPONENT_PARAMETER_NONFINITE')
        out[component]={'conditional_mean':mean,'raw_unconditional_mean':raw_mean,'std':prior['std'],
            'rate':rate,'parent':parent,'per_opportunity_scale':prior.get('per_opportunity_residual_scale',0.),
            'hurdle_probability':prior['activity_rate'],'nonzero_mean':prior['nonzero_mean'],'nonzero_std':prior['nonzero_std'],
            'provenance':provenance,'recent_n':len(unconditional),'paired_recent_n':paired_n,
            'recent_exposure':exposure,'prior_pool':pool,'prior_n':prior['n'],
            'prior_zero_exposures':prior['zero_exposures'],'prior_nonzero_exposures':prior['nonzero_exposures']}
    return {'position':position,'model_id':model,'components':out,'quality':quality,'stat_activity_probability':probability}

def seeded(lock,cid,model,week):
    seed=int.from_bytes(hashlib.sha256(f"{lock['random_seed']}|{cid}|{model}|{week}".encode()).digest()[:8],'big')
    return np.random.default_rng(seed)

def scenarios(lock,params,cid,week,*,bye=False,availability=1.):
    n=lock['draws'];rng=seeded(lock,cid,params['model_id'],week);specs=params['components']
    output={c:np.zeros(n,dtype=float) for c in lock['components']}
    probability=params['stat_activity_probability']*availability
    if bye or probability<=0:return output,{'constraint_adjusted_cells':0,'stat_activity_probability':0.}
    active=rng.random(n)<probability if params['position']!='DEF' else np.ones(n,dtype=bool)
    for c,s in specs.items():
        if c.startswith(('prob_','dst_prob_')) or c in MEAN_DERIVED:continue
        mean=s['conditional_mean']
        if ('yards' in c or c.endswith('_yds')):
            if c in YARD_PARENT:
                continue
            if c in {'dst_net_yards_allowed'}:
                output[c]=rng.normal(mean,max(s['std'],1e-6),n)
            else:
                h=min(1.,max(0.,s['hurdle_probability']))
                # Scale a sparse-yard hurdle so its expected mean equals the
                # estimated conditional weekly mean; do not force negative yards positive.
                loc=mean/max(h,1e-9) if h>0 else 0.
                output[c]=np.where(rng.random(n)<h,rng.normal(loc,max(s['nonzero_std'],1e-6),n),0.)
        elif c=='idp_sacks':output[c]=rng.poisson(max(0.,mean)*2,n)/2.
        else:output[c]=rng.poisson(max(0.,mean),n).astype(float)
    adjustments=0
    def cap(child,parent):
        nonlocal adjustments
        before=output[child].copy();output[child]=np.minimum(output[child],np.maximum(output[parent],0.))
        adjustments+=int(np.count_nonzero(before!=output[child]))
    # B1 samples child counts using the smoothed numerator/exposure rate.
    # B0 preserves its rolling marginal parameters then uses the same caps.
    for c,parent in RATE_PARENT.items():
        if c not in specs or parent not in output:continue
        if params['model_id']==MODELS[1] and specs[c]['rate'] is not None:
            output[c]=rng.binomial(np.maximum(np.rint(output[parent]),0).astype(int),np.clip(specs[c]['rate'],0,1)).astype(float)
        cap(c,parent)
    # Interceptions and completions consume disjoint pass attempts.
    remaining=np.maximum(output['passing_attempts']-output['passing_completions'],0.)
    before=output['passing_interceptions'].copy();output['passing_interceptions']=np.minimum(before,remaining)
    adjustments+=int(np.count_nonzero(before!=output['passing_interceptions']))
    cap('passing_touchdowns','passing_completions');cap('passing_pick_sixes','passing_interceptions')
    cap('receiving_touchdowns','receptions');cap('rushing_touchdowns','rushing_attempts')
    for prefix,parent,forty in [('passing','passing_completions_40_plus','passing_touchdowns_40_plus'),
                              ('rushing','rushes_40_plus','rushing_touchdowns_40_plus'),
                              ('receiving','receptions_40_plus','receiving_touchdowns_40_plus')]:
        cap(forty,parent);cap(forty,prefix+'_touchdowns');cap(prefix+'_touchdowns_50_plus',forty)
    for c,parent in YARD_PARENT.items():
        if c not in specs:continue
        s=specs[c];volume=output[parent]
        rate=s['rate']
        if rate is None:
            parent_mean=specs.get(parent,{}).get('conditional_mean',0.)
            rate=s['conditional_mean']/parent_mean if parent_mean>0 else 0.
        scale=max(s['per_opportunity_scale'],1e-6)
        output[c]=rng.normal(volume*rate,scale*np.sqrt(np.maximum(volume,0.)),n)
        output[c][volume<=0]=0.
    output['idp_tackles_total']=output['idp_tackles_solo']+output['idp_tackles_assisted']
    short=np.maximum(np.ceil(output['idp_sacks'])-output['idp_tackles_total'],0.)
    output['idp_tackles_assisted']+=short;output['idp_tackles_total']+=short
    output['idp_quarterback_hits']=np.maximum(output['idp_quarterback_hits'],np.ceil(output['idp_sacks']))
    cap('idp_tackles_for_loss','idp_tackles_total')
    output['idp_sack_yards']=np.maximum(output['idp_sack_yards'],0.)
    output['dst_blocked_kick_return_yards']=np.where(output['dst_blocked_kicks']>0,output['dst_blocked_kick_return_yards'],0.)
    for prefix in ['idp','dst']:
        budget=output[prefix+'_interceptions']+output[prefix+'_fumble_recoveries']+output[prefix+'_blocked_kicks']
        if prefix=='dst':budget+=output['dst_special_teams_touchdowns']
        before=output[prefix+'_defensive_touchdowns'].copy()
        output[prefix+'_defensive_touchdowns']=np.minimum(before,budget)
        adjustments+=int(np.count_nonzero(before!=output[prefix+'_defensive_touchdowns']))
    # First downs and touchdowns are disjoint credited events.
    output['passing_first_downs']=np.minimum(output['passing_first_downs'],np.maximum(output['passing_completions']-output['passing_touchdowns'],0.))
    output['rushing_first_downs']=np.minimum(output['rushing_first_downs'],np.maximum(output['rushing_attempts']-output['rushing_touchdowns'],0.))
    output['receiving_first_downs']=np.minimum(output['receiving_first_downs'],np.maximum(output['receptions']-output['receiving_touchdowns'],0.))
    for prefix in ['passing','rushing','receiving']:
        output['source_'+prefix+'_first_downs_including_td']=output[prefix+'_first_downs']+output[prefix+'_touchdowns']
    for band in FG_BANDS:
        c='kicker_fgm_'+band
        if c not in output:output[c]=np.zeros(n)
        c='kicker_fgmiss_'+band
        if c not in output:output[c]=np.zeros(n)
    output['kicker_fgm']=sum(output['kicker_fgm_'+b] for b in FG_BANDS)
    output['kicker_fgm_50p']=output['kicker_fgm_50_59']+output['kicker_fgm_60p']
    output['kicker_fgmiss']=sum(output['kicker_fgmiss_'+b] for b in FG_BANDS)
    output['kicker_field_goal_attempts']=output['kicker_fgm']+output['kicker_fgmiss']
    output['kicker_extra_point_attempts']=output['kicker_xpm']+output['kicker_xpmiss']
    output['kicker_fgm_yds']=sum(output['kicker_fgm_'+b]*DISTANCE_MID[b] for b in FG_BANDS)
    cap('kicker_blocked_field_goals','kicker_fgmiss');cap('kicker_blocked_extra_points','kicker_xpmiss')
    for c in output:
        output[c]=output[c]*active
        if 'yards' in c or c.endswith('_yds'):output[c]=np.rint(output[c])
    # Derive all threshold events from this same signed-yard scenario.
    for c,(kind,lower,upper) in {'prob_pass_yd_300':('passing',300,399),'prob_pass_yd_400':('passing',400,None),
                                'prob_rush_yd_100':('rushing',100,199),'prob_rec_yd_100':('receiving',100,199)}.items():
        yards=output[kind+'_yards'];output[c]=(active & (yards>=lower) & ((yards<=upper) if upper is not None else True)).astype(float)
    points=output['dst_points_allowed']
    if params['position']=='DEF':
        points=np.maximum(np.rint(points),0);output['dst_points_allowed']=points
        for band,(lower,upper) in POINT_BANDS.items():
            output['dst_prob_pts_allow_'+band]=((points>=lower)&((points<=upper) if upper is not None else True)).astype(float)
    if any(not np.isfinite(v).all() for v in output.values()):raise ValueError('COMPONENT_SCENARIO_NONFINITE')
    return output,{'constraint_adjusted_cells':adjustments,'stat_activity_probability':probability}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,default=BASE);a=p.parse_args();result=fit(a.root,a.output)
    print(json.dumps({'model_ids':result['model_ids'],'components':len(result['components']),
                      'fitted_at':result['fitted_at'],'sleeper_projection_feature_use':False}))

if __name__=='__main__':main()
