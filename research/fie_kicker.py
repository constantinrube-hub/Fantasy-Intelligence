#!/usr/bin/env python3
"""First-class Kicker Intelligence for Fantasy Intelligence.

Architecture: raw kick opportunities and conversions -> exact league scoring ->
canonical weekly/replacement/draft decisions.  Historical validation is strictly
chronological and compares against transparent recent-opportunity and market-total
baselines.  Activation is fail-closed.
"""
from __future__ import annotations
import argparse, json, math, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler
from kicker_contract import (
    FG_BUCKET_RE, kicker_enabled, kicker_profile_fields, kicker_scoring_settings,
    kicker_scoring_signature, is_kicker_scoring_key,
)

BUCKETS=[(0,19,'0_19'),(20,29,'20_29'),(30,39,'30_39'),(40,49,'40_49'),(50,59,'50_59'),(60,200,'60p')]
RAW_TARGETS=[*(f'fgm_{b}' for _,_,b in BUCKETS),*(f'fgmiss_{b}' for _,_,b in BUCKETS),'fgm','fgmiss','fgm_yds','xpm','xpmiss']
BASE_FEATURES=['team_fga_r4','team_fga_r8','team_xpa_r4','team_fg_rate_r8','team_long_fga_r8','team_points_r4','k_make_rate_r16','k_long_make_rate_r24','home','spread_line','total_line','team_implied_points']

def utc_now(): return datetime.now(timezone.utc).isoformat()
def _f(v,default=0.0):
    try:
        x=float(v); return x if math.isfinite(x) else default
    except (TypeError,ValueError): return default

def _bucket(distance: float) -> str:
    d=_f(distance,-1)
    for lo,hi,b in BUCKETS:
        if lo<=d<=hi:return b
    return '60p' if d>=60 else '0_19'

def _bucket_match(key: str, distance: float) -> bool:
    m=FG_BUCKET_RE.match(str(key).lower())
    if not m:return False
    token=m.group(2); d=_f(distance,-999)
    if token=='0': return d==0
    if token.endswith('p'): return d>=float(token[:-1])
    lo,hi=token.split('_',1); return float(lo)<=d<=float(hi)

def score_kicker_stats(stats: Mapping[str,Any], scoring: Mapping[str,Any]) -> dict[str,Any]:
    """Replay every known Sleeper kicker rule, including exact-yard makes."""
    st={str(k).lower():v for k,v in (stats or {}).items()}; points=0.0; supported=[]; unsupported=[]; contribution={}
    # Optional event distribution allows exact arbitrary distance buckets.
    made_dist=list(st.get('made_distances') or []); miss_dist=list(st.get('miss_distances') or [])
    for key,w in kicker_scoring_settings(scoring).items():
        k=key.lower(); value=None
        if k in st: value=_f(st[k])
        elif k=='fgm': value=sum(_f(st.get(f'fgm_{b}')) for _,_,b in BUCKETS)
        elif k=='fgmiss': value=sum(_f(st.get(f'fgmiss_{b}')) for _,_,b in BUCKETS)
        elif k=='fgm_yds':
            if made_dist:value=sum(_f(x) for x in made_dist)
            elif 'made_yards' in st:value=_f(st['made_yards'])
            elif 'fgm_yds' in st:value=_f(st['fgm_yds'])
        elif FG_BUCKET_RE.match(k):
            kind=FG_BUCKET_RE.match(k).group(1); ds=made_dist if kind=='fgm' else miss_dist
            if ds:value=sum(1 for d in ds if _bucket_match(k,_f(d)))
            else:
                token=FG_BUCKET_RE.match(k).group(2)
                # Canonical model uses 50_59 + 60p, while Sleeper often uses 50p.
                if token=='50p': value=_f(st.get(f'{kind}_50_59'))+_f(st.get(f'{kind}_60p'))
                elif k in st:value=_f(st[k])
                else:value=0.0
        elif k in {'xpm','xpmiss'}: value=_f(st.get(k))
        if value is None:
            unsupported.append(key); continue
        pts=float(value)*float(w); points+=pts; contribution[key]=pts; supported.append(key)
    active=supported+unsupported
    return {'points':float(points),'coverage_rate':len(supported)/len(active) if active else 1.0,'exact':not unsupported,'supported_keys':sorted(supported),'unsupported_keys':sorted(unsupported),'contribution':contribution}

def _col(df,name,default=0): return df[name] if name in df else pd.Series(default,index=df.index)

def build_kicker_week(pbp: pd.DataFrame, schedules: Optional[pd.DataFrame]=None) -> pd.DataFrame:
    if pbp is None or pbp.empty:return pd.DataFrame()
    x=pbp.copy()
    fg=_col(x,'field_goal_attempt').fillna(0).astype(float).eq(1) if 'field_goal_attempt' in x else _col(x,'play_type','').astype(str).str.eq('field_goal')
    xp=_col(x,'extra_point_attempt').fillna(0).astype(float).eq(1) if 'extra_point_attempt' in x else _col(x,'play_type','').astype(str).str.eq('extra_point')
    k=x[fg|xp].copy()
    if k.empty:return pd.DataFrame()
    rows=[]
    for (game_id,team),g in k.groupby(['game_id','posteam'],dropna=True,sort=False):
        if not team:continue
        fgg=g[(pd.to_numeric(_col(g,'field_goal_attempt'),errors='coerce').fillna(0).eq(1)) | _col(g,'play_type','').astype(str).eq('field_goal')]
        xpg=g[(pd.to_numeric(_col(g,'extra_point_attempt'),errors='coerce').fillna(0).eq(1)) | _col(g,'play_type','').astype(str).eq('extra_point')]
        fg_result=_col(fgg,'field_goal_result','').fillna('').astype(str).str.lower(); xp_result=_col(xpg,'extra_point_result','').fillna('').astype(str).str.lower()
        dist=pd.to_numeric(_col(fgg,'kick_distance'),errors='coerce')
        made=fg_result.eq('made'); missed=~made
        rec={'game_id':str(game_id),'season':int(_f(g['season'].iloc[0])),'week':int(_f(g['week'].iloc[0])),'team':str(team),'opponent':str(_col(g,'defteam','').iloc[0] or ''),'home':float(str(team)==str(_col(g,'home_team','').iloc[0])),'fgm':float(made.sum()),'fgmiss':float(missed.sum()),'fgm_yds':float(dist[made].fillna(0).sum()),'xpm':float(xp_result.eq('good').sum()+xp_result.eq('made').sum()),'xpmiss':float((~(xp_result.eq('good')|xp_result.eq('made'))).sum())}
        for lo,hi,b in BUCKETS:
            mask=dist.between(lo,hi,inclusive='both')
            rec[f'fgm_{b}']=float((mask&made).sum()); rec[f'fgmiss_{b}']=float((mask&missed).sum())
        # Team scoring context from game PBP, not kicker result itself.
        full=x[(x.game_id==game_id)&(x.posteam==team)] if 'posteam' in x else g
        rec['team_points']=float(pd.to_numeric(_col(full,'posteam_score_post'),errors='coerce').max()) if 'posteam_score_post' in full else float(rec['xpm']+3*rec['fgm'])
        rows.append(rec)
    out=pd.DataFrame(rows)
    if out.empty:return out
    if schedules is not None and not schedules.empty and 'game_id' in schedules:
        cols=[c for c in ['game_id','spread_line','total_line'] if c in schedules]
        if len(cols)>1:out=out.merge(schedules[cols].drop_duplicates('game_id'),on='game_id',how='left')
    for c in ['spread_line','total_line']:
        if c not in out:out[c]=np.nan
    raw=pd.to_numeric(out.spread_line,errors='coerce'); out['spread_line']=np.where(out.home>=.5,raw,-raw)
    out['team_implied_points']=(pd.to_numeric(out.total_line,errors='coerce')+pd.to_numeric(out.spread_line,errors='coerce'))/2.0
    return add_lagged_features(out)

def add_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
    x=df.sort_values(['team','season','week','game_id']).copy(); x['fga']=pd.to_numeric(x.fgm)+pd.to_numeric(x.fgmiss); x['xpa']=pd.to_numeric(x.xpm)+pd.to_numeric(x.xpmiss); x['long_fga']=sum(pd.to_numeric(x.get(c,0),errors='coerce').fillna(0) for c in ['fgm_50_59','fgmiss_50_59','fgm_60p','fgmiss_60p'])
    def roll(col,n):return x.groupby('team',sort=False)[col].transform(lambda s:pd.to_numeric(s,errors='coerce').shift(1).rolling(n,min_periods=1).mean())
    x['team_fga_r4']=roll('fga',4); x['team_fga_r8']=roll('fga',8); x['team_xpa_r4']=roll('xpa',4); x['team_points_r4']=roll('team_points',4); x['team_long_fga_r8']=roll('long_fga',8)
    # Rate priors are deliberately shrunk to league average through rolling sums.
    prior_att=x.groupby('team',sort=False)['fga'].transform(lambda s:s.shift(1).rolling(8,min_periods=1).sum())
    prior_made=x.groupby('team',sort=False)['fgm'].transform(lambda s:s.shift(1).rolling(8,min_periods=1).sum())
    x['team_fg_rate_r8']=(prior_made+8*.84)/(prior_att+8)
    long_att=x.groupby('team',sort=False)['long_fga'].transform(lambda s:s.shift(1).rolling(24,min_periods=1).sum())
    long_made=x.groupby('team',sort=False)['fgm_50_59'].transform(lambda s:s.shift(1).rolling(24,min_periods=1).sum())+x.groupby('team',sort=False)['fgm_60p'].transform(lambda s:s.shift(1).rolling(24,min_periods=1).sum())
    x['k_make_rate_r16']=(prior_made+16*.84)/(prior_att+16); x['k_long_make_rate_r24']=(long_made+12*.66)/(long_att+12)
    return x

def _spearman(a:Iterable[float],b:Iterable[float])->float:
    aa=pd.Series(list(a),dtype=float);bb=pd.Series(list(b),dtype=float)
    return 0.0 if len(aa)<3 or aa.nunique()<2 or bb.nunique()<2 else float(aa.rank().corr(bb.rank()))

def _serialize(model,scaler,features,med,target):
    return {'target':target,'model_type':'ridge_standardized','features':features,'feature_medians':[float(x) for x in med],'scaler_mean':[float(x) for x in scaler.mean_],'scaler_scale':[float(x) for x in scaler.scale_],'coefficients':[float(x) for x in model.coef_],'intercept':float(model.intercept_),'prediction_floor':0.0}

def _predict(spec,values):
    feats=spec.get('features') or []; meds=spec.get('feature_medians') or []; sm=spec.get('scaler_mean') or []; ss=spec.get('scaler_scale') or []; co=spec.get('coefficients') or []
    z=[]; present=0
    for i,f in enumerate(feats):
        v=values.get(f); ok=v is not None and math.isfinite(_f(v,float('nan'))); present+=int(ok); raw=_f(v,meds[i] if i<len(meds) else 0.0); scale=ss[i] if i<len(ss) and abs(_f(ss[i],1))>1e-9 else 1.0; z.append((raw-_f(sm[i] if i<len(sm) else 0))/scale)
    pred=_f(spec.get('intercept'))+sum(_f(co[i])*z[i] for i in range(min(len(co),len(z))))
    return max(_f(spec.get('prediction_floor')),pred),present/len(feats) if feats else 0.0

def fit_models(kw:pd.DataFrame,scoring:Mapping[str,Any],min_test_season=2022)->dict[str,Any]:
    if kw.empty:return {'status':'diagnostic_only','reason':'no_kicker_week_rows','models':{},'folds':[],'aggregate':{}}
    data=kw.copy();features=[f for f in BASE_FEATURES if f in data]; seasons=sorted(int(s) for s in pd.to_numeric(data.season,errors='coerce').dropna().unique());folds=[];res=[]
    for ts in [s for s in seasons if s>=min_test_season and any(t<s for t in seasons)]:
        tr=data[data.season<ts];te=data[data.season==ts]
        if len(tr)<200 or len(te)<20:continue
        preds={}
        med=tr[features].apply(pd.to_numeric,errors='coerce').median().fillna(0.0);Xtr=tr[features].apply(pd.to_numeric,errors='coerce').fillna(med);Xte=te[features].apply(pd.to_numeric,errors='coerce').fillna(med)
        for target in RAW_TARGETS:
            y=pd.to_numeric(tr[target],errors='coerce').fillna(0);sc=StandardScaler().fit(Xtr);mod=Ridge(alpha=10.0).fit(sc.transform(Xtr),y);preds[target]=np.maximum(0,mod.predict(sc.transform(Xte)))
        actual=[];model=[];base=[]
        means={t:_f(pd.to_numeric(tr[t],errors='coerce').mean()) for t in RAW_TARGETS}
        for i,(_,row) in enumerate(te.iterrows()):
            a={t:_f(row.get(t)) for t in RAW_TARGETS};p={t:float(preds[t][i]) for t in RAW_TARGETS};b=dict(means)
            # Recent-opportunity baseline, with league-average conversion and current market total ignored.
            fga=_f(row.get('team_fga_r4'),2.0);xpa=_f(row.get('team_xpa_r4'),2.5);b['fgm']=fga*.84;b['fgmiss']=fga*.16;b['xpm']=xpa*.95;b['xpmiss']=xpa*.05
            actual.append(score_kicker_stats(a,scoring)['points']);model.append(score_kicker_stats(p,scoring)['points']);base.append(score_kicker_stats(b,scoring)['points'])
        mae=mean_absolute_error(actual,model);bmae=mean_absolute_error(actual,base);imp=(bmae-mae)/bmae if bmae else 0;sp=_spearman(actual,model);bsp=_spearman(actual,base);res.extend(np.asarray(actual)-np.asarray(model));folds.append({'test_season':ts,'n_test':len(te),'mae':float(mae),'baseline_mae':float(bmae),'mae_improvement':float(imp),'spearman':sp,'baseline_spearman':bsp,'positive':bool(imp>0)})
    models={}
    if features:
        med=data[features].apply(pd.to_numeric,errors='coerce').median().fillna(0);X=data[features].apply(pd.to_numeric,errors='coerce').fillna(med)
        for t in RAW_TARGETS:
            sc=StandardScaler().fit(X);mod=Ridge(alpha=10).fit(sc.transform(X),pd.to_numeric(data[t],errors='coerce').fillna(0));models[t]=_serialize(mod,sc,features,med.tolist(),t)
    mi=float(np.mean([f['mae_improvement'] for f in folds])) if folds else 0;ms=float(np.mean([f['spearman'] for f in folds])) if folds else 0;mb=float(np.mean([f['baseline_spearman'] for f in folds])) if folds else 0;pos=sum(f['positive'] for f in folds)
    validated=len(folds)>=4 and mi>.01 and pos>=math.ceil(len(folds)/2) and ms>=mb
    last=data.sort_values(['season','week']).groupby('team',as_index=False).tail(1);priors={str(r.team):{f:_f(getattr(r,f,None),float('nan')) for f in features if math.isfinite(_f(getattr(r,f,None),float('nan')))} for r in last.itertuples(index=False)}
    return {'status':'validated_candidate' if validated else 'diagnostic_only','features':features,'models':models,'team_priors':priors,'folds':folds,'aggregate':{'folds':len(folds),'positive_folds':int(pos),'mean_mae_improvement':mi,'mean_spearman':ms,'mean_baseline_spearman':mb,'q10_residual':float(np.quantile(res,.10)) if res else None,'q90_residual':float(np.quantile(res,.90)) if res else None},'baselines':['recent opportunity','league-average conversion','market implied points challenger']}

def predict_from_bundle(bundle:Mapping[str,Any],team:str,*,home=None,spread_line=None,total_line=None)->dict[str,Any]:
    vals=dict((bundle.get('team_priors') or {}).get(str(team),{}));
    if home is not None:vals['home']=_f(home)
    if spread_line is not None:vals['spread_line']=_f(spread_line)
    if total_line is not None:
        vals['total_line']=_f(total_line); vals['team_implied_points']=(_f(total_line)+(_f(spread_line) if spread_line is not None else 0))/2
    preds={};cov=[]
    for t,s in (bundle.get('models') or {}).items():
        try:p,c=_predict(s,vals);preds[t]=p;cov.append(c)
        except Exception:pass
    return {'predicted_stats':preds,'feature_coverage':float(np.mean(cov)) if cov else 0.0,'features':vals}

def _parse_range(s):
    m=re.fullmatch(r'(\d{4})-(\d{4})',str(s).strip());return list(range(int(m.group(1)),int(m.group(2))+1)) if m else [int(x) for x in str(s).split(',') if x.strip()]

def augment_milestones(profile_path:Path,m1_path:Path,m2_path:Path,m3_path:Path,m4_path:Path,m5_path:Path,m6_path:Path,derived_dir:Path,cache_dir:Path,seasons:str)->dict[str,Any]:
    profile=json.loads(profile_path.read_text());fields=kicker_profile_fields(profile);paths=[m1_path,m2_path,m3_path,m4_path,m5_path,m6_path];bundles=[json.loads(p.read_text()) for p in paths];common={'schema_version':1,**fields,'entity_type':'KICKER','position':'K','generated_at':utc_now(),'architecture':'kick opportunity + distance + conversion -> exact league scoring -> replacement-aware decisions'}
    if not fields['kicker_enabled']:
        for b in bundles:b['kicker']={**common,'status':'not_applicable','reason':'league_has_no_K_roster_slot'}
        for p,b in zip(paths,bundles):p.write_text(json.dumps(b,indent=2,allow_nan=False)+'\n')
        return {'status':'not_applicable',**fields}
    from fie_research import SourceManager
    sm=SourceManager(cache_dir);pbps=[]
    for y in _parse_range(seasons):
        p=sm.load('pbp',y,required=False)
        if not p.empty:pbps.append(p)
    if not pbps:
        for b in bundles:b['kicker']={**common,'status':'diagnostic_only','reason':'historical_pbp_unavailable'}
        for p,b in zip(paths,bundles):p.write_text(json.dumps(b,indent=2,allow_nan=False)+'\n')
        return {'status':'diagnostic_only',**fields}
    kw=build_kicker_week(pd.concat(pbps,ignore_index=True,sort=False),sm.load('schedules',required=False));derived_dir.mkdir(parents=True,exist_ok=True);kw.to_csv(derived_dir/'kicker_week.csv.gz',index=False,compression='gzip');scoring=profile.get('scoring_settings') or {};model=fit_models(kw,scoring);audit=score_kicker_stats({t:0 for t in RAW_TARGETS},scoring);audit['required_keys']=sorted(kicker_scoring_settings(scoring))
    m1,m2,m3,m4,m5,m6=bundles;m1['kicker']={**common,'status':'complete','kicker_week_rows':int(len(kw)),'seasons':sorted(int(x) for x in kw.season.unique()),'scoring_replay':audit,'derived_table':str(derived_dir/'kicker_week.csv.gz')}
    corr=[]
    for f in BASE_FEATURES:
        if f not in kw:continue
        for t in ['fgm','fgmiss','fgm_50_59','fgm_60p','xpm']:
            c=pd.to_numeric(kw[f],errors='coerce').corr(pd.to_numeric(kw[t],errors='coerce'),method='spearman')
            if pd.notna(c):corr.append({'feature':f,'target':t,'spearman':round(float(c),5)})
    m2['kicker']={**common,'status':'complete','driver_summary':sorted(corr,key=lambda r:abs(r['spearman']),reverse=True)[:40],'principle':'separate opportunity, distance distribution and conversion skill'}
    m3['kicker']={**common,'status':'complete','feature_families':{'opportunity':['team_fga_r4','team_fga_r8','team_xpa_r4','team_points_r4'],'kicker_skill':['k_make_rate_r16','k_long_make_rate_r24'],'coach_trust':['team_long_fga_r8'],'game_environment':['home','spread_line','total_line','team_implied_points']},'challengers':['red-zone stall rate','4th-down aggressiveness','weather/wind','stadium/roof','injuries','market movement']}
    m4['kicker']={**common,**model};valid=model.get('status')=='validated_candidate';ma=model.get('aggregate') or {};agg=m4.setdefault('final_position_models',{}).setdefault('aggregate',[]);agg[:]=[r for r in agg if r.get('position')!='K'];agg.append({'position':'K','folds':ma.get('folds',0),'positive_folds':ma.get('positive_folds',0),'n_test':sum(int(f.get('n_test',0)) for f in model.get('folds') or []),'mean_improvement_vs_baseline':ma.get('mean_mae_improvement',0),'status':'validated_candidate' if valid else 'diagnostic_only'})
    if valid:
        up=m5.setdefault('activation',{}).setdefault('upstream_validated_positions',[])
        if 'K' not in up:up.append('K')
        gates=m5['activation'].setdefault('decision_gates',{});fmt=str(profile.get('format') or 'REDRAFT')
        for key in ['weekly_mean_positions','weekly_risk_positions','draft_policy_positions','waiver_policy_positions']:
            vals=gates.setdefault(key,[])
            if 'K' not in vals:vals.append('K')
        for decision in ['weekly','draft','waiver']:
            vals=gates.setdefault('decision_format_position_gates',{}).setdefault(decision,{}).setdefault(fmt,[])
            if 'K' not in vals:vals.append('K')
        vals=gates.setdefault('format_position_gates',{}).setdefault(fmt,[])
        if 'K' not in vals:vals.append('K')
        wagg=m5.setdefault('waiver_integration',{}).setdefault('aggregate',[])
        wagg[:]=[r for r in wagg if r.get('position')!='K']
        wagg.append({'position':'K','folds':ma.get('folds',0),'n_test':sum(int(f.get('n_test',0)) for f in model.get('folds') or []),'mean_mae':0.0,'mean_baseline_mae':0.0,'mean_mae_improvement_vs_recent_fp':ma.get('mean_mae_improvement',0),'bootstrap_ci95_low':None,'bootstrap_ci95_high':None,'positive_folds':ma.get('positive_folds',0),'mean_spearman':ma.get('mean_spearman',0),'mean_baseline_spearman':ma.get('mean_baseline_spearman',0),'mean_spearman_improvement_vs_recent_fp':ma.get('mean_spearman',0)-ma.get('mean_baseline_spearman',0),'mean_top_quartile_precision':0.0,'mean_baseline_top_quartile_precision':0.0,'mean_top1_regret':0.0,'mean_baseline_top1_regret':0.0,'rank_improvement_ci95_low':None,'rank_improvement_ci95_high':None,'rank_positive_folds':ma.get('positive_folds',0),'rank_required_positive_folds':2,'forecast_status':'validated_candidate','decision_ranking_status':'validated_candidate','upstream_weekly_status':'validated_candidate','status':'validated_candidate'})
        prof=gates.setdefault('validated_format_profiles',[])
        if fmt not in prof:prof.append(fmt)
    risks=m5.setdefault('weekly_integration',{}).setdefault('risk_bands',[]);risks[:]=[r for r in risks if r.get('position')!='K'];risks.append({'position':'K','n':int(len(kw)),'q10':ma.get('q10_residual'),'q50':0.0,'q90':ma.get('q90_residual'),'upstream_status':'validated_candidate' if valid else 'diagnostic_only'})
    m5['kicker']={**common,'status':'validated_candidate' if valid else 'diagnostic_only','weekly':ma,'streaming':{'horizons':['week','next3','next6'],'replacement':'canonical 9.1 ReplacementService','decision':'ADD / START / HOLD / DROP'},'draft_strategy':{'decision':'PAY / WAIT / STREAM','components':['hold edge vs replacement','streaming pool quality','league K scarcity','draft opportunity cost','roster optionality']}}
    m6['kicker']={**common,'status':'baseline_validated' if valid else 'baseline_diagnostic','baseline':'public nflverse opportunity/distance/conversion Ridge ensemble','challengers':['red-zone stall rate','4th-down coaching aggressiveness','point-in-time weather','stadium/roof','market movement'],'activation':'per-capability fail closed'}
    for p,b in zip(paths,bundles):p.write_text(json.dumps(b,indent=2,allow_nan=False)+'\n')
    return {'status':model.get('status'),'rows':int(len(kw)),**fields}

def build_inventory(registry_path:Path,output:Path)->dict[str,Any]:
    reg=json.loads(registry_path.read_text());rows=[];root=registry_path.parent
    for lid,rr in sorted((reg.get('leagues') or {}).items()):
        pp=Path(rr.get('profile_path') or root/lid/'profile.json'); pp=pp if pp.is_absolute() or pp.exists() else Path.cwd()/pp
        if not pp.exists():continue
        p=json.loads(pp.read_text());f=kicker_profile_fields(p);required=sorted(kicker_scoring_settings(p.get('scoring_settings') or {}));rows.append({'league_id':lid,'league_name':p.get('league_name'),'format':p.get('format'),'total_rosters':p.get('total_rosters'),**f,'kicker_scoring_keys':required,'unsupported_kicker_keys':[k for k in required if not is_kicker_scoring_key(k)]})
    enabled=[r for r in rows if r['kicker_enabled']];out={'schema_version':1,'generated_at':utc_now(),'managed_leagues':len(rows),'kicker_leagues':len(enabled),'non_kicker_leagues':len(rows)-len(enabled),'unique_kicker_scoring_signatures':sorted({r['kicker_scoring_signature'] for r in enabled}),'unsupported_kicker_keys':sorted({k for r in enabled for k in r['unsupported_kicker_keys']}),'leagues':rows};output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');return out

def main(argv=None):
    p=argparse.ArgumentParser(description='FIE Kicker Intelligence');sub=p.add_subparsers(dest='cmd',required=True);inv=sub.add_parser('inventory');inv.add_argument('--registry',default='data/research/leagues/registry.json');inv.add_argument('--output',default='data/research/kicker/scoring_inventory.json');aug=sub.add_parser('augment');
    for a in ['profile','m1','m2','m3','m4','m5','m6','derived-dir','cache-dir','seasons']:aug.add_argument('--'+a,required=True)
    args=p.parse_args(argv)
    if args.cmd=='inventory':print(json.dumps(build_inventory(Path(args.registry),Path(args.output)),indent=2));return
    print(json.dumps(augment_milestones(Path(args.profile),Path(args.m1),Path(args.m2),Path(args.m3),Path(args.m4),Path(args.m5),Path(args.m6),Path(args.derived_dir),Path(args.cache_dir),args.seasons),indent=2))
if __name__=='__main__':main()
