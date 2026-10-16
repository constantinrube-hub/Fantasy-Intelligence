"""Recover documented inference coefficients; fit individual rates from source history.

Saved player projection means and quantiles are never fitting inputs. Archived
defensive source coefficients are parsed separately from the comparison outputs.
Fresh defensive refits have a distinct version; original WR training code is lost.
"""
import argparse,gzip,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from recovery_common import *
from component_source_contract import team,position
METRICS={'catch_probability':('receptions','targets'),
         'receiving_yards_per_reception':('receiving_yards','receptions'),
         'rushing_yards_per_carry':('rushing_yards','rushing_attempts')}
NATIVE={'receptions':'receptions','targets':'targets','receiving_yards':'receiving_yards',
        'rushing_attempts':'carries','rushing_yards':'rushing_yards','rushing_touchdowns':'rushing_tds',
        'receiving_touchdowns':'receiving_tds'}
def pairs(frame,child,parent):
    a=pd.to_numeric(frame[child],errors='coerce');b=pd.to_numeric(frame[parent],errors='coerce')
    mask=a.notna()&b.notna()&b.gt(0)&np.isfinite(a)&np.isfinite(b)
    if child=='receptions':mask&=a.ge(0)&a.le(b)
    return mask
def individual(hist,current,entities):
    priors={};outputs={};audit={}
    for pos,g in hist.groupby('position_model'):
        priors[pos]={}
        for name,(child,parent) in METRICS.items():
            mask=pairs(g,child,parent);a=(g.loc[mask,child]*g.loc[mask,'weight']).sum();b=(g.loc[mask,parent]*g.loc[mask,'weight']).sum()
            if b>0:priors[pos][name]={'rate':float(a/b),'numerator':float(a),'exposure':float(b)}
    hs={cid:g for cid,g in hist.groupby('canonical_player_id')};cs={cid:g for cid,g in current.groupby('canonical_player_id')}
    for e in entities:
        if e['position_model'] not in {'QB','RB','WR','TE'}:continue
        cid=e['canonical_player_id'];pos=e['position_model'];h=hs.get(cid,hist.iloc[:0]);c=cs.get(cid,current.iloc[:0]);out={}
        for name,(child,parent) in METRICS.items():
            prior=priors[pos][name];hm=pairs(h,child,parent);cm=pairs(c,child,parent)
            hn=float((h.loc[hm,child]*h.loc[hm,'weight']).sum());hd=float((h.loc[hm,parent]*h.loc[hm,'weight']).sum());cn=float(c.loc[cm,child].sum());cd=float(c.loc[cm,parent].sum())
            historical=(hn+20*prior['rate'])/(hd+20);rate=(cn+20*historical)/(cd+20)
            out[name]={'rate':rate,'historical_numerator':hn,'historical_exposure':hd,'current_numerator':cn,'current_exposure':cd,'current_weight':cd/(cd+20),'position_prior':prior}
        outputs[cid]=out
    return outputs,priors
def from_tables(root):
    ref=root/BASE/'reference';rush={};receive={};wr={}
    for section in read(ref/'Step2_Recovered_Completion-sections.json'):
        club=section['name'].split()[0];rush[club]={}
        for role,table in zip(['QB','RB'],section['tables']):
            d={}
            for key,value in table[1:]:
                try:d[key]=json.loads(value)
                except ValueError:d[key]=value
            rush[club][role]=d
    for name,target,tag in [('Step3_Receiving_Defense-sections.json',receive,'RB/TE/WR'),('Step4_WR_Hierarchy-sections.json',wr,'WR1/WR2/WR3+')]:
        for section in read(ref/name):
            if tag not in section['name']:continue
            club=section['name'].split(':')[0];target[club]={}
            for row in section['tables'][0][1:]:
                role=row[0];v=list(map(float,row[1:]));target[club][role]={'observed':dict(zip(['targets','receptions','yards','touchdowns'],v[:4])),'weight_multiplier':v[4],'catch_probability':v[5],'ypr':v[6],'td_rate':v[7]}
    if (len(rush),len(receive),len(wr))!=(32,32,32):raise ValueError('DEFENSE_SOURCE_COVERAGE')
    return rush,receive,wr
def source_frames(root,bundle,through):
    refs={r['name']:r for r in bundle['responses']}
    raw=pd.read_csv(verified(root,refs['player_week'],bundle['observation_cutoff']),low_memory=False)
    current=raw[raw.week.le(through)&raw.season_type.eq('REG')].copy()
    current=current.rename(columns={'player_id':'canonical_player_id',**{v:k for k,v in NATIVE.items()}})
    current['position_model']=current.position.map(position);current['weight']=1.
    history=[]
    for year in range(2021,2026):
        frame=pd.read_csv(root/TRAINING/f'training-{year}.csv.gz',low_memory=False)
        frame['weight']=.5**(2025-year);history.append(frame)
    return pd.concat(history,ignore_index=True),current
def fit(root=ROOT,bundle_path=None,output=None,through=5,archived=True):
    bundle_path=Path(bundle_path or JOINT/'observations/observation-bundle.json');bundle=read(root/bundle_path)
    out=root/(output or BASE/'fit/fitted.json')
    if out.exists():raise ValueError('NEW_FIT_REVISION_REQUIRED')
    hist,current=source_frames(root,bundle,through)
    entities=read(root/JOINT/'entities.json')['entities']
    players,priors=individual(hist,current,entities)
    rush,receive,wr=from_tables(root)
    # Role TD priors are fitted from observed source values, not forecast outputs.
    td_priors={}
    for pos,g in hist.groupby('position_model'):
        td_priors[pos]={}
        for kind,parent in [('rushing','rushing_attempts'),('receiving','receptions')]:
            child=kind+'_touchdowns';m=pairs(g,child,parent);num=float((g.loc[m,child]*g.loc[m,'weight']).sum());den=float((g.loc[m,parent]*g.loc[m,'weight']).sum())
            td_priors[pos][kind]=(num/den if den>0 else 0.)
    offense={}
    for club,g in current.groupby('team'):
        offense[team(club)]={}
        for pos,x in g.groupby('position_model'):
            d={}
            for kind,parent in [('rushing','rushing_attempts'),('receiving','receptions')]:
                child=kind+'_touchdowns';m=pairs(x,child,parent);num=float(x.loc[m,child].sum());den=float(x.loc[m,parent].sum());d[kind]=(num+120*td_priors.get(pos,{}).get(kind,0))/(den+120)
            offense[team(club)][pos]=d
    if not archived:
        # Reconstructed refit: schedule-adjusted against individual source rates.
        # Distinct from the unavailable original historical fitting procedure.
        for club in receive:
            for pos in ['RB','TE','WR']:
                g=current[current.opponent.map(team).eq(club)&current.position_model.eq(pos)]
                target=float(g.targets.sum());rec=float(g.receptions.sum());yard=float(g.receiving_yards.sum());td=float(g.receiving_touchdowns.sum());p=priors[pos]
                expected_c=sum(float(x.targets)*players.get(x.canonical_player_id,{}).get('catch_probability',p['catch_probability'])['rate'] for x in g.itertuples())
                expected_y=sum(float(x.receptions)*players.get(x.canonical_player_id,{}).get('receiving_yards_per_reception',p['receiving_yards_per_reception'])['rate'] for x in g.itertuples())
                catch=(rec+40*p['catch_probability']['rate'])/(expected_c+40*p['catch_probability']['rate'])*p['catch_probability']['rate']
                ypr=(yard+40*p['receiving_yards_per_reception']['rate'])/(expected_y+40*p['receiving_yards_per_reception']['rate'])*p['receiving_yards_per_reception']['rate']
                receive[club][pos]={'observed':{'targets':target,'receptions':rec,'yards':yard,'touchdowns':td},'weight_multiplier':1.,'catch_probability':float(np.clip(catch,.01,.99)),'ypr':ypr,'td_rate':(td+120*td_priors[pos]['receiving'])/(rec+120)}
            for role in ['QB','RB']:
                g=current[current.opponent.map(team).eq(club)&current.position_model.eq(role)];den=float(g.rushing_attempts.sum());num=float(g.rushing_yards.sum());td=float(g.rushing_touchdowns.sum());prior=priors[role]['rushing_yards_per_carry']['rate']
                rush[club][role]={'carry_weight_multiplier':1.,'allowed_ypc':(num+40*prior)/(den+40),'allowed_td_rate':(td+120*td_priors[role]['rushing'])/(den+120)}
        # Fresh WR subtiers borrow the newly fitted coarse-WR profile until the
        # distinct historical tier refitter is supplied; never silently reuse old effects.
        wr={club:{role:dict(receive[club]['WR']) for role in ['WR1','WR2','WR3+']} for club in receive}
    value={'schema':'fie-recovered-component-fit-v2','version':'ARCHIVED_INFERENCE_WITH_RECONSTRUCTED_WR_OFFENSE' if archived else 'SOURCE_REFIT_COARSE_WR_V2','built_at':now(),'season':2026,'through_week':through,'bundle_path':bundle_path.as_posix(),'bundle_sha256':sha(root/bundle_path),'players':players,'position_priors':priors,'td_priors':td_priors,'offensive_role_td':offense,'rushing_defense':rush,'receiving_defense':receive,'wr_defense':wr,'weather_used':False,'training_sources':[{'path':(TRAINING/f'training-{y}.csv.gz').as_posix(),'sha256':sha(root/TRAINING/f'training-{y}.csv.gz')} for y in range(2021,2026)],'limitations':['ORIGINAL_WR_TRAINING_CODE_UNAVAILABLE','WR_OFFENSIVE_TD_PRIOR_USES_COARSE_POSITION_SOURCE_PRIOR','NO_PREDICTIVE_VALIDATION','FUTURE_REFIT_COARSE_WR_FALLBACK_EXPLICIT']}
    if archived:value['coefficient_sources']=[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in sorted((root/BASE/'reference').glob('*-sections.json'))]
    write(out,value);print('FITTED',out,len(players),'offensive identities',flush=True);return value
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path);p.add_argument('--output',type=Path);p.add_argument('--through-week',type=int,default=5);p.add_argument('--fresh',action='store_true');a=p.parse_args();fit(bundle_path=a.bundle,output=a.output,through=a.through_week,archived=not a.fresh)
