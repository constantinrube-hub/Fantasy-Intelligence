#!/usr/bin/env python3
"""FIE feature-evidence research layer.

This module explains *why* a metric does or does not survive FIE's production gates.
It is deliberately downstream of M1-M9 and fail-closed: nothing here changes runtime
projections.  It adds seven research phases:

1. feature evidence / coverage / redundancy / power matrix;
2. component-target validation (opportunity -> efficiency -> scoring mechanics);
3. multi-horizon evidence (same week, next week, next 3, ROS, floor, ceiling, breakout, next season);
4. regularized and nonlinear residual challengers under nested chronological CV;
5. pre-specified conditional/interaction tests beyond main effects;
6. data-expansion priorities based on observed coverage and uncertainty;
7. production-eligibility reporting under the same robust OOS gate, with zero auto-activation.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BUILD = "V9.4-FEATURE-EVIDENCE"
POSITIONS = ("QB", "RB", "WR", "TE")
MIN_TRAIN_WEEKLY = 80
MIN_TEST_WEEKLY = 15
MIN_FOLDS = 4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(xs: Iterable[float]) -> List[float]:
    out=[]
    for x in xs:
        try: v=float(x)
        except Exception: continue
        if math.isfinite(v): out.append(v)
    return out


def block_bootstrap_ci(values: Sequence[float], weights: Optional[Sequence[float]]=None,
                       iterations: int=4000, seed: int=89) -> Tuple[Optional[float],Optional[float]]:
    vals=finite(values)
    if len(vals)<3: return None,None
    a=np.asarray(vals,float)
    if weights is None: w=np.ones(len(a),float)
    else:
        raw=list(weights); w=np.asarray([float(raw[i]) if i<len(raw) and float(raw[i])>0 else 1.0 for i in range(len(a))])
    rng=np.random.default_rng(seed); draws=np.empty(iterations,float); n=len(a)
    for i in range(iterations):
        idx=rng.integers(0,n,n); draws[i]=np.average(a[idx],weights=w[idx])
    lo,hi=np.quantile(draws,[.025,.975]); return float(lo),float(hi)


def robust_gate(values: Sequence[float], weights: Optional[Sequence[float]]=None,
                min_mean: float=.01, min_folds: int=4, win_share: float=.67) -> dict:
    vals=finite(values); n=len(vals)
    if not vals:
        return {"folds":0,"mean":None,"positive_folds":0,"required_positive_folds":0,"ci95_low":None,"ci95_high":None,"robust":False}
    w=None if weights is None else list(weights)[:n]
    mean=float(np.average(vals,weights=w)) if w and len(w)==n else float(np.mean(vals))
    wins=sum(v>0 for v in vals); need=max(2,int(math.ceil(n*win_share)))
    lo,hi=block_bootstrap_ci(vals,w)
    return {"folds":n,"mean":mean,"positive_folds":wins,"required_positive_folds":need,
            "ci95_low":lo,"ci95_high":hi,
            "robust":bool(n>=min_folds and mean>=min_mean and wins>=need and lo is not None and lo>0)}


def sign_flip_p(values: Sequence[float]) -> Optional[float]:
    vals=np.asarray(finite(values),float)
    if len(vals)<3: return None
    obs=float(vals.mean()); n=len(vals)
    if n<=14:
        means=[]
        for signs in itertools.product((-1.0,1.0), repeat=n): means.append(float((vals*np.asarray(signs)).mean()))
        return float((np.sum(np.asarray(means)>=obs)+1)/(len(means)+1))
    rng=np.random.default_rng(94); means=[]
    for _ in range(20000): means.append(float((vals*rng.choice([-1.0,1.0],size=n)).mean()))
    return float((np.sum(np.asarray(means)>=obs)+1)/(len(means)+1))


def bh_qvalues(pairs: List[Tuple[int,Optional[float]]]) -> Dict[int,Optional[float]]:
    valid=[(i,float(p)) for i,p in pairs if p is not None and math.isfinite(float(p))]
    if not valid: return {i:None for i,_ in pairs}
    valid.sort(key=lambda x:x[1]); m=len(valid); qraw=[]
    for rank,(i,p) in enumerate(valid,1): qraw.append([i,min(1.0,p*m/rank)])
    running=1.0
    for k in range(len(qraw)-1,-1,-1): running=min(running,qraw[k][1]); qraw[k][1]=running
    out={i:q for i,q in qraw}
    for i,_ in pairs: out.setdefault(i,None)
    return out


def safe_corr(a,b,min_n=20) -> Tuple[Optional[float],int]:
    z=pd.DataFrame({"a":pd.to_numeric(a,errors="coerce"),"b":pd.to_numeric(b,errors="coerce")}).dropna()
    if len(z)<min_n or z.a.nunique()<2 or z.b.nunique()<2: return None,int(len(z))
    r=spearmanr(z.a,z.b).statistic
    return (float(r) if np.isfinite(r) else None),int(len(z))


def expanding_folds(seasons: Sequence[int], min_train_seasons=3, max_folds=6) -> List[Tuple[List[int],int]]:
    ss=sorted({int(x) for x in seasons if pd.notna(x)})
    folds=[]
    for i in range(min_train_seasons,len(ss)):
        folds.append((ss[:i],ss[i]))
    return folds[-max_folds:]


def add_horizons(df: pd.DataFrame) -> pd.DataFrame:
    d=df.sort_values(["canonical_player_id","season","week"]).copy()
    d["_fp"]=pd.to_numeric(d["fantasy_points"],errors="coerce")
    g=d.groupby(["canonical_player_id","season"],group_keys=False)["_fp"]
    shifts=[g.shift(-i) for i in (1,2,3)]
    d["future_fp_next1"]=shifts[0]
    d["future_fp_next3"]=pd.concat(shifts,axis=1).mean(axis=1,skipna=True)
    def ros(s):
        a=pd.to_numeric(s,errors="coerce").to_numpy(float); out=np.full(len(a),np.nan)
        for i in range(len(a)-1):
            q=a[i+1:]; q=q[np.isfinite(q)]
            if len(q): out[i]=float(q.mean())
        return pd.Series(out,index=s.index)
    d["future_fp_ros"]=g.transform(ros)
    d["fp_prior4_audit"]=g.transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
    return d.drop(columns=["_fp"])


def ridge(alpha=12.0):
    return Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler()),("model",Ridge(alpha=alpha))])


def elastic(alpha=.01,l1=.25):
    return Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler()),
                     ("model",ElasticNet(alpha=alpha,l1_ratio=l1,max_iter=8000,random_state=94))])


def histgb(lr=.05,leaves=15,l2=3.0):
    return Pipeline([("impute",SimpleImputer(strategy="median")),
                     ("model",HistGradientBoostingRegressor(learning_rate=lr,max_leaf_nodes=leaves,
                                                            l2_regularization=l2,max_iter=120,random_state=94))])


def partial_pool_model(features: Sequence[str], alpha: float=24.0):
    """Regularized player-intercept approximation to hierarchical partial pooling.

    Numeric driver effects are shared across the position. Player one-hot intercepts are
    strongly Ridge-shrunk toward zero; players unseen in a test fold therefore fall back
    to the pooled population component instead of receiving an invented player effect.
    """
    numeric=Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())])
    prep=ColumnTransformer([
        ("numeric",numeric,list(features)),
        ("player",OneHotEncoder(handle_unknown="ignore"),["canonical_player_id"]),
    ],remainder="drop")
    return Pipeline([("prepare",prep),("model",Ridge(alpha=alpha,solver="lsqr"))])


def merge_oos(df,oos,features):
    keys=["season","week","canonical_player_id","position_model"]
    keep=keys+[f for f in features if f in df.columns]
    return oos.merge(df[keep].drop_duplicates(keys),on=keys,how="left")


def validate_feature_increment(df,oos,pos,feature) -> Tuple[List[dict],dict]:
    z=merge_oos(df,oos,[feature]); z=z[z.position_model.eq(pos)].copy()
    z["fantasy_points"]=pd.to_numeric(z.fantasy_points,errors="coerce"); z["fie_projection"]=pd.to_numeric(z.fie_projection,errors="coerce")
    z["residual"]=z.fantasy_points-z.fie_projection
    rows=[]
    for train_seasons,test in expanding_folds(z.season.dropna().unique()):
        tr=z[z.season.isin(train_seasons)].dropna(subset=["residual"]); te=z[z.season.eq(test)].dropna(subset=["fantasy_points","fie_projection"])
        tr=tr[tr[[feature]].notna().any(axis=1)]; te=te[te[[feature]].notna().any(axis=1)]
        if len(tr)<MIN_TRAIN_WEEKLY or len(te)<MIN_TEST_WEEKLY: continue
        m=ridge(); m.fit(tr[[feature]],tr.residual); adj=np.clip(m.predict(te[[feature]]),-8,8)
        y=te.fantasy_points.to_numpy(float); base=te.fie_projection.to_numpy(float); pred=base+adj
        b=mean_absolute_error(y,base); a=mean_absolute_error(y,pred)
        rows.append({"test_season":int(test),"n_test":int(len(te)),"base_mae":float(b),"adjusted_mae":float(a),
                     "improvement":float((b-a)/b) if b>0 else None})
    vals=[r["improvement"] for r in rows if r["improvement"] is not None]; weights=[r["n_test"] for r in rows if r["improvement"] is not None]
    g=robust_gate(vals,weights); g["sign_flip_p"]=sign_flip_p(vals); return rows,g


def peer_redundancy(df,pos,family_features,feature) -> Tuple[Optional[float],Optional[str]]:
    z=df[df.position_model.eq(pos)]
    best=(None,None)
    for other in family_features:
        if other==feature or other not in z: continue
        r,n=safe_corr(z[feature],z[other],min_n=50)
        if r is not None and (best[0] is None or abs(r)>abs(best[0])): best=(r,other)
    return best


def estimated_folds_needed(gate:dict, folds:List[dict]) -> Optional[int]:
    vals=np.asarray(finite([r.get("improvement") for r in folds]),float)
    if len(vals)<3 or not gate.get("mean") or gate["mean"]<=0: return None
    sd=float(vals.std(ddof=1))
    if not np.isfinite(sd) or sd==0: return len(vals)
    need=int(math.ceil((1.96*sd/max(gate["mean"],1e-6))**2))
    return max(len(vals),min(20,need))


def classify_feature(row:dict) -> Tuple[str,str]:
    g=row["weekly_gate"]; sg=row.get("season_gate") or {}
    if row["coverage"]<.35 or row["non_null_n"]<100:
        return "insufficient_coverage","Too little observed history to make a stable incremental claim."
    if g.get("robust"):
        return "validated","Clears the unchanged chronological OOS promotion gate."
    if sg.get("robust"):
        return "horizon_specific","Does not clear the weekly gate but does clear next-season portability evidence."
    mean=g.get("mean"); lo=g.get("ci95_low"); hi=g.get("ci95_high")
    if mean is not None and mean>0 and (lo is None or lo<=0) and hi is not None and hi>0:
        return "promising_underpowered","Positive point estimate, but temporal-block uncertainty still crosses zero."
    if row.get("max_peer_abs_corr") is not None and row["max_peer_abs_corr"]>=.80:
        return "redundant_or_explanatory","Strong association overlaps heavily with another feature and adds little residual value."
    assoc=max(abs(row.get(k) or 0) for k in ["next1_spearman","next3_spearman","ros_spearman"])
    if assoc>=.10:
        return "descriptive_not_incremental","Predictive association exists, but it does not improve the already-informed FIE baseline."
    return "no_incremental_evidence","Current history shows little stable incremental predictive value."


def season_feature_gate(df,pos,feature) -> Tuple[List[dict],dict]:
    try:
        from preseason_projection import build_transition_table
    except Exception:
        return [],{"robust":False,"reason":"preseason_projection_unavailable"}
    trans,features,_=build_transition_table(df,pos)
    if trans.empty or feature not in trans.columns: return [],{"robust":False,"reason":"feature_not_in_transition_table"}
    rows=[]
    for train_seasons,test in expanding_folds(trans.target_season.dropna().unique(),min_train_seasons=3,max_folds=6):
        tr=trans[trans.target_season.isin(train_seasons)].dropna(subset=["target_fantasy_ppg"])
        te=trans[trans.target_season.eq(test)].dropna(subset=["target_fantasy_ppg"])
        tr=tr[tr[[feature]].notna().any(axis=1)]; te=te[te[[feature]].notna().any(axis=1)]
        if len(tr)<60 or len(te)<12: continue
        fs=["prev_fantasy_ppg",feature]; m=ridge(18); m.fit(tr[fs],tr.target_fantasy_ppg)
        pred=m.predict(te[fs]); base=pd.to_numeric(te.prev_fantasy_ppg,errors="coerce").to_numpy(float); y=te.target_fantasy_ppg.to_numpy(float)
        ok=np.isfinite(base)&np.isfinite(y)&np.isfinite(pred)
        if ok.sum()<12: continue
        b=mean_absolute_error(y[ok],base[ok]); a=mean_absolute_error(y[ok],pred[ok])
        rows.append({"test_season":int(test),"n_test":int(ok.sum()),"improvement":float((b-a)/b) if b>0 else None})
    vals=[r["improvement"] for r in rows if r.get("improvement") is not None]; weights=[r["n_test"] for r in rows if r.get("improvement") is not None]
    g=robust_gate(vals,weights); g["sign_flip_p"]=sign_flip_p(vals); return rows,g


def feature_matrix(df,oos,catalog) -> Tuple[List[dict],List[dict]]:
    d=add_horizons(df); rows=[]; fold_rows=[]
    for pos in POSITIONS:
        z=d[d.position_model.eq(pos)]
        for family,features in catalog.get(pos,{}).items():
            fam=[f for f in features if f in z]
            for f in fam:
                x=pd.to_numeric(z[f],errors="coerce"); n=int(x.notna().sum()); total=int(len(z)); seasons=sorted(int(s) for s in z.loc[x.notna(),"season"].dropna().unique())
                c1,n1=safe_corr(x,z.future_fp_next1); c3,n3=safe_corr(x,z.future_fp_next3); cr,nr=safe_corr(x,z.future_fp_ros); cs,ns=safe_corr(x,z.fantasy_points)
                pers,_=safe_corr(x,z.groupby(["canonical_player_id","season"])[f].shift(-1),min_n=30)
                weekly_folds,wg=validate_feature_increment(d,oos,pos,f); sf,sg=season_feature_gate(d,pos,f)
                fold_rows += [{"position":pos,"family":family,"feature":f,"scope":"weekly",**r} for r in weekly_folds]
                fold_rows += [{"position":pos,"family":family,"feature":f,"scope":"next_season",**r} for r in sf]
                pr,peer=peer_redundancy(z,pos,fam,f)
                rows.append({"position":pos,"family":family,"feature":f,"non_null_n":n,"total_n":total,"coverage":n/total if total else 0,
                             "player_n":int(z.loc[x.notna(),"canonical_player_id"].nunique()),"season_n":len(seasons),
                             "first_season":min(seasons) if seasons else None,"last_season":max(seasons) if seasons else None,
                             "same_week_spearman":cs,"same_week_n":ns,"next1_spearman":c1,"next1_n":n1,"next3_spearman":c3,"next3_n":n3,
                             "ros_spearman":cr,"ros_n":nr,"persistence_spearman":pers,
                             "max_peer_abs_corr":abs(pr) if pr is not None else None,"most_correlated_peer":peer,
                             "weekly_gate":wg,"season_gate":sg,"estimated_total_folds_needed":estimated_folds_needed(wg,weekly_folds)})
    # exploratory FDR by position; never replaces robust promotion gate
    for pos in POSITIONS:
        ix=[i for i,r in enumerate(rows) if r["position"]==pos]
        wq=bh_qvalues([(i,rows[i]["weekly_gate"].get("sign_flip_p")) for i in ix])
        sq=bh_qvalues([(i,(rows[i].get("season_gate") or {}).get("sign_flip_p")) for i in ix])
        for i in ix:
            rows[i]["weekly_fdr_q"]=wq.get(i); rows[i]["season_fdr_q"]=sq.get(i)
            rows[i]["multiplicity_support"]="weekly_fdr_supported" if wq.get(i) is not None and wq[i]<=.10 else "season_fdr_supported" if sq.get(i) is not None and sq[i]<=.10 else "not_fdr_supported_or_not_testable"
            status,reason=classify_feature(rows[i]); rows[i]["evidence_status"]=status; rows[i]["why"]=reason
    return rows,fold_rows



def horizon_validation(df: pd.DataFrame, catalog) -> List[dict]:
    """Phase 3: feature-by-feature incremental tests at decision-relevant horizons.

    Continuous horizons compare a baseline model using pregame 4-game fantasy history
    with the same model plus the candidate feature.  Tail/breakout outcomes use Brier
    score and thresholds estimated from the training seasons only.
    """
    d=add_horizons(df); out=[]
    for pos in POSITIONS:
        z=d[d.position_model.eq(pos)].copy()
        if "fp_prior4_audit" not in z: continue
        for family,features in catalog.get(pos,{}).items():
            for feature in [f for f in features if f in z]:
                for horizon,target in [("next_week","future_fp_next1"),("next_3_games","future_fp_next3"),("rest_of_season","future_fp_ros")]:
                    folds=[]
                    for trse,test in expanding_folds(z.season.dropna().unique()):
                        tr=z[z.season.isin(trse)].dropna(subset=[target,"fp_prior4_audit"]); te=z[z.season.eq(test)].dropna(subset=[target,"fp_prior4_audit"])
                        tr=tr[tr[[feature]].notna().any(axis=1)]; te=te[te[[feature]].notna().any(axis=1)]
                        if len(tr)<100 or len(te)<20: continue
                        b=ridge(18); m=ridge(18); b.fit(tr[["fp_prior4_audit"]],tr[target]); m.fit(tr[["fp_prior4_audit",feature]],tr[target])
                        y=te[target].to_numpy(float); pb=b.predict(te[["fp_prior4_audit"]]); pm=m.predict(te[["fp_prior4_audit",feature]])
                        be=mean_absolute_error(y,pb); me=mean_absolute_error(y,pm)
                        folds.append({"test_season":int(test),"n_test":int(len(te)),"improvement":float((be-me)/be) if be>0 else None})
                    vals=[r["improvement"] for r in folds if r.get("improvement") is not None]; weights=[r["n_test"] for r in folds if r.get("improvement") is not None]; gate=robust_gate(vals,weights); gate["sign_flip_p"]=sign_flip_p(vals)
                    out.append({"position":pos,"family":family,"feature":feature,"horizon":horizon,"metric":"mae","folds":folds,"gate":gate})
                # Tail and breakout classification; train-only thresholds prevent test-distribution leakage.
                for horizon in ("floor","ceiling","breakout"):
                    folds=[]; target="future_fp_next1" if horizon in {"floor","ceiling"} else "future_fp_next3"
                    for trse,test in expanding_folds(z.season.dropna().unique()):
                        tr=z[z.season.isin(trse)].dropna(subset=[target,"fp_prior4_audit"]); te=z[z.season.eq(test)].dropna(subset=[target,"fp_prior4_audit"])
                        tr=tr[tr[[feature]].notna().any(axis=1)]; te=te[te[[feature]].notna().any(axis=1)]
                        if len(tr)<120 or len(te)<25: continue
                        q25=float(tr[target].quantile(.25)); q60=float(tr[target].quantile(.60)); q75=float(tr[target].quantile(.75))
                        if horizon=="floor": ytr=(tr[target]<=q25).astype(int); yte=(te[target]<=q25).astype(int)
                        elif horizon=="ceiling": ytr=(tr[target]>=q75).astype(int); yte=(te[target]>=q75).astype(int)
                        else:
                            ytr=((tr[target]>=q60)&(tr[target]>=1.25*tr.fp_prior4_audit)).astype(int)
                            yte=((te[target]>=q60)&(te[target]>=1.25*te.fp_prior4_audit)).astype(int)
                        if ytr.nunique()<2 or yte.nunique()<2: continue
                        # Linear-probability Ridge is intentionally used here: with one or two
                        # predictors it is far cheaper than thousands of repeated logistic fits,
                        # while Brier score remains a proper out-of-sample probability loss after clipping.
                        base=ridge(18); model=ridge(18)
                        base.fit(tr[["fp_prior4_audit"]],ytr); model.fit(tr[["fp_prior4_audit",feature]],ytr)
                        pb=np.clip(base.predict(te[["fp_prior4_audit"]]),.001,.999); pm=np.clip(model.predict(te[["fp_prior4_audit",feature]]),.001,.999)
                        be=brier_score_loss(yte,pb); me=brier_score_loss(yte,pm)
                        folds.append({"test_season":int(test),"n_test":int(len(te)),"improvement":float((be-me)/be) if be>0 else None})
                    vals=[r["improvement"] for r in folds if r.get("improvement") is not None]; weights=[r["n_test"] for r in folds if r.get("improvement") is not None]; gate=robust_gate(vals,weights); gate["sign_flip_p"]=sign_flip_p(vals)
                    out.append({"position":pos,"family":family,"feature":feature,"horizon":horizon,"metric":"brier","folds":folds,"gate":gate})
    for pos in POSITIONS:
        for horizon in ("next_week","next_3_games","rest_of_season","floor","ceiling","breakout"):
            ix=[i for i,r in enumerate(out) if r["position"]==pos and r["horizon"]==horizon]
            q=bh_qvalues([(i,(out[i].get("gate") or {}).get("sign_flip_p")) for i in ix])
            for i in ix: out[i]["fdr_q"]=q.get(i)
    return out


def attach_horizon_status(features:List[dict], horizons:List[dict]) -> None:
    m={}
    for r in horizons:
        if (r.get("gate") or {}).get("robust"):
            m.setdefault((r["position"],r["feature"]),[]).append(r["horizon"])
    for r in features:
        hs=sorted(set(m.get((r["position"],r["feature"]),[])))
        if (r.get("season_gate") or {}).get("robust"): hs.append("next_season")
        r["validated_horizons"]=sorted(set(hs))
        if not (r.get("weekly_gate") or {}).get("robust") and hs:
            r["evidence_status"]="horizon_specific"
            r["why"]="Fails the same-week residual gate but clears at least one independently validated future/tail horizon: "+", ".join(sorted(set(hs)))


def _first_numeric(df,names):
    for n in names:
        if n in df and pd.to_numeric(df[n],errors="coerce").notna().any(): return pd.to_numeric(df[n],errors="coerce")
    return None


def component_targets(df,pos):
    z=df[df.position_model.eq(pos)].copy(); out={}
    if pos=="QB":
        att=_first_numeric(z,["attempts","passing_attempts"]); comp=_first_numeric(z,["completions"]); py=_first_numeric(z,["passing_yards"]); rush=_first_numeric(z,["carries","rushing_attempts"])
        if att is not None: out["pass_volume"]=att
        if rush is not None: out["rush_volume"]=rush
        if att is not None and comp is not None: out["completion_rate"]=comp/att.replace(0,np.nan)
        if att is not None and py is not None: out["yards_per_attempt"]=py/att.replace(0,np.nan)
    elif pos=="RB":
        car=_first_numeric(z,["carries","rushing_attempts"]); tar=_first_numeric(z,["targets"]); ry=_first_numeric(z,["rushing_yards"]); rec=_first_numeric(z,["receptions"])
        if car is not None: out["carry_volume"]=car
        if tar is not None: out["target_volume"]=tar
        if car is not None and ry is not None: out["rushing_efficiency"]=ry/car.replace(0,np.nan)
        if tar is not None and rec is not None: out["catch_conversion"]=rec/tar.replace(0,np.nan)
    else:
        tar=_first_numeric(z,["targets"]); rec=_first_numeric(z,["receptions"]); y=_first_numeric(z,["receiving_yards"])
        if tar is not None: out["target_volume"]=tar
        if tar is not None and rec is not None: out["catch_conversion"]=rec/tar.replace(0,np.nan)
        if tar is not None and y is not None: out["yards_per_target"]=y/tar.replace(0,np.nan)
    return z,out


def component_validation(df,catalog) -> List[dict]:
    """Phase 2: test each driver against the football component it could plausibly move.

    The baseline is a calibrated persistence model of the component itself.  A feature
    only receives credit when `current component + feature` improves next-game component
    prediction out of sample.  An all-feature component challenger is reported separately.
    """
    results=[]
    for pos in POSITIONS:
        z,targets=component_targets(df,pos)
        features=list(dict.fromkeys(f for fs in catalog.get(pos,{}).values() for f in fs if f in z and not str(f).startswith("premium_")))[:40]
        if not features: continue
        for name,current in targets.items():
            q=z[["season","week","canonical_player_id"]+features].copy(); q["current_target"]=current
            q=q.sort_values(["canonical_player_id","season","week"]); q["future_target"]=q.groupby(["canonical_player_id","season"])["current_target"].shift(-1)
            candidates=[(f,[f]) for f in features]+[("__all_features__",features)]
            for label,fs in candidates:
                folds=[]
                for trse,test in expanding_folds(q.season.dropna().unique()):
                    tr=q[q.season.isin(trse)].dropna(subset=["future_target","current_target"]); te=q[q.season.eq(test)].dropna(subset=["future_target","current_target"])
                    tr=tr[tr[fs].notna().any(axis=1)]; te=te[te[fs].notna().any(axis=1)]
                    if len(tr)<100 or len(te)<20: continue
                    base=ridge(18); full=ridge(18)
                    base.fit(tr[["current_target"]],tr.future_target); full.fit(tr[["current_target"]+fs],tr.future_target)
                    y=te.future_target.to_numpy(float); pb=base.predict(te[["current_target"]]); pf=full.predict(te[["current_target"]+fs])
                    be=mean_absolute_error(y,pb); fe=mean_absolute_error(y,pf)
                    folds.append({"test_season":int(test),"n_test":int(len(te)),"improvement":float((be-fe)/be) if be>0 else None})
                vals=[r["improvement"] for r in folds if r.get("improvement") is not None]; weights=[r["n_test"] for r in folds if r.get("improvement") is not None]
                g=robust_gate(vals,weights); g["sign_flip_p"]=sign_flip_p(vals)
                results.append({"position":pos,"component":name,"feature":label,"feature_n":len(fs),"folds":folds,"gate":g,
                                "status":"validated_component_signal" if g["robust"] else "diagnostic_component_signal"})
    for pos in POSITIONS:
        for component in sorted({r["component"] for r in results if r["position"]==pos}):
            ix=[i for i,r in enumerate(results) if r["position"]==pos and r["component"]==component and r["feature"]!="__all_features__"]
            q=bh_qvalues([(i,(results[i].get("gate") or {}).get("sign_flip_p")) for i in ix])
            for i in ix: results[i]["fdr_q"]=q.get(i)
    return results


def attach_component_status(features:List[dict], components:List[dict]) -> None:
    m={}
    for r in components:
        if r.get("feature")=="__all_features__": continue
        if (r.get("gate") or {}).get("robust"):
            m.setdefault((r["position"],r["feature"]),[]).append(r["component"])
    for r in features:
        comps=sorted(set(m.get((r["position"],r["feature"]),[])))
        r["validated_components"]=comps
        if not (r.get("weekly_gate") or {}).get("robust") and not r.get("validated_horizons") and comps:
            r["evidence_status"]="mechanism_specific"
            r["why"]="Does not clear the direct fantasy-point gate, but adds robust OOS information for the football component(s): "+", ".join(comps)


def inner_pick(tr,features,target,kind):
    seasons=sorted(int(x) for x in tr.season.dropna().unique())
    if len(seasons)<3: return None
    val=seasons[-1]; fit=tr[tr.season.lt(val)]; hold=tr[tr.season.eq(val)]
    if len(fit)<80 or len(hold)<15: return None
    if kind=="ridge": configs=[(6,), (12,), (24,), (48,)]
    elif kind=="elastic": configs=[(.002,.1),(.005,.3),(.01,.5),(.02,.8)]
    elif kind=="partial_pool": configs=[(12,), (24,), (48,), (96,)]
    else: configs=[(.04,7,1.),(.05,15,3.),(.07,15,5.)]
    best=None
    for cfg in configs:
        m=ridge(*cfg) if kind=="ridge" else elastic(*cfg) if kind=="elastic" else partial_pool_model(features,*cfg) if kind=="partial_pool" else histgb(*cfg)
        xcols=features+["canonical_player_id"] if kind=="partial_pool" else features
        try: m.fit(fit[xcols],fit[target]); p=m.predict(hold[xcols]); e=mean_absolute_error(hold[target],p)
        except Exception: continue
        if best is None or e<best[0]: best=(e,cfg)
    return best[1] if best else None


def challenger_validation(df,oos,catalog) -> List[dict]:
    allrows=[]
    for pos in POSITIONS:
        features=list(dict.fromkeys(f for fs in catalog.get(pos,{}).values() for f in fs if f in df and not str(f).startswith("premium_")))[:48]
        if not features: continue
        z=merge_oos(df,oos,features); z=z[z.position_model.eq(pos)].copy(); z["fantasy_points"]=pd.to_numeric(z.fantasy_points,errors="coerce"); z["fie_projection"]=pd.to_numeric(z.fie_projection,errors="coerce"); z["residual"]=z.fantasy_points-z.fie_projection
        for kind in ("ridge","elastic","partial_pool","histgb"):
            folds=[]
            for trse,test in expanding_folds(z.season.dropna().unique()):
                tr=z[z.season.isin(trse)].dropna(subset=["residual"]); te=z[z.season.eq(test)].dropna(subset=["fantasy_points","fie_projection"])
                tr=tr[tr[features].notna().any(axis=1)]; te=te[te[features].notna().any(axis=1)]
                if len(tr)<120 or len(te)<20: continue
                cfg=inner_pick(tr,features,"residual",kind)
                if cfg is None: cfg=(12,) if kind=="ridge" else (.01,.3) if kind=="elastic" else (24,) if kind=="partial_pool" else (.05,15,3.)
                m=ridge(*cfg) if kind=="ridge" else elastic(*cfg) if kind=="elastic" else partial_pool_model(features,*cfg) if kind=="partial_pool" else histgb(*cfg)
                xcols=features+["canonical_player_id"] if kind=="partial_pool" else features
                m.fit(tr[xcols],tr.residual); adj=np.clip(m.predict(te[xcols]),-8,8); y=te.fantasy_points.to_numpy(float); base=te.fie_projection.to_numpy(float); pred=base+adj
                b=mean_absolute_error(y,base); a=mean_absolute_error(y,pred); folds.append({"test_season":int(test),"n_test":int(len(te)),"improvement":float((b-a)/b) if b>0 else None,"config":list(cfg)})
            vals=[r["improvement"] for r in folds if r.get("improvement") is not None]; weights=[r["n_test"] for r in folds if r.get("improvement") is not None]; g=robust_gate(vals,weights); g["sign_flip_p"]=sign_flip_p(vals)
            allrows.append({"position":pos,"model":kind,"feature_n":len(features),"folds":folds,"gate":g})
    for pos in POSITIONS:
        ix=[i for i,r in enumerate(allrows) if r["position"]==pos]; q=bh_qvalues([(i,allrows[i]["gate"].get("sign_flip_p")) for i in ix])
        for i in ix:
            allrows[i]["fdr_q"]=q.get(i); allrows[i]["production_eligibility"]="eligible_for_manual_consumer_integration" if allrows[i]["gate"]["robust"] else "diagnostic_only"
    return allrows


INTERACTIONS={
 "QB":[("pressure_x_time","pfr_times_pressured_pct_prior4","ngs_avg_time_to_throw_prior4"),("pressure_x_cpoe","pfr_times_pressured_pct_prior4","ngs_completion_percentage_above_expectation_prior4"),("rush_x_goal","qb_rush_share_prior4","inside_5_carry_share_prior4")],
 "RB":[("role_x_ryoe","carry_share_prior4","ngs_rush_yards_over_expected_per_att_prior4"),("box_x_ryoe","ngs_percent_attempts_gte_eight_defenders_prior4","ngs_rush_yards_over_expected_per_att_prior4")],
 "WR":[("target_x_sep","target_share_prior4","ngs_avg_separation_prior4"),("target_x_air","target_share_prior4","ngs_percent_share_of_intended_air_yards_prior4")],
 "TE":[("target_x_sep","target_share_prior4","ngs_avg_separation_prior4"),("target_x_air","target_share_prior4","ngs_percent_share_of_intended_air_yards_prior4")],
}


def interaction_validation(df,oos) -> List[dict]:
    out=[]
    for pos,specs in INTERACTIONS.items():
        for name,a,b in specs:
            if a not in df or b not in df: continue
            d=df.copy(); inter=f"__fe_{name}"; d[inter]=pd.to_numeric(d[a],errors="coerce")*pd.to_numeric(d[b],errors="coerce")
            z=merge_oos(d,oos,[a,b,inter]); z=z[z.position_model.eq(pos)].copy(); z["fantasy_points"]=pd.to_numeric(z.fantasy_points,errors="coerce"); z["fie_projection"]=pd.to_numeric(z.fie_projection,errors="coerce"); z["residual"]=z.fantasy_points-z.fie_projection
            folds=[]
            for trse,test in expanding_folds(z.season.dropna().unique()):
                tr=z[z.season.isin(trse)].dropna(subset=["residual"]); te=z[z.season.eq(test)].dropna(subset=["fantasy_points","fie_projection"])
                tr=tr[tr[[a,b,inter]].notna().any(axis=1)]; te=te[te[[a,b,inter]].notna().any(axis=1)]
                if len(tr)<100 or len(te)<20: continue
                main=ridge(); full=ridge(); main.fit(tr[[a,b]],tr.residual); full.fit(tr[[a,b,inter]],tr.residual)
                y=te.fantasy_points.to_numpy(float); base=te.fie_projection.to_numpy(float); pm=base+np.clip(main.predict(te[[a,b]]),-8,8); pf=base+np.clip(full.predict(te[[a,b,inter]]),-8,8)
                ma=mean_absolute_error(y,pm); fa=mean_absolute_error(y,pf); folds.append({"test_season":int(test),"n_test":int(len(te)),"interaction_over_main_improvement":float((ma-fa)/ma) if ma>0 else None})
            vals=[r["interaction_over_main_improvement"] for r in folds if r.get("interaction_over_main_improvement") is not None]; weights=[r["n_test"] for r in folds if r.get("interaction_over_main_improvement") is not None]; g=robust_gate(vals,weights); g["sign_flip_p"]=sign_flip_p(vals)
            out.append({"position":pos,"interaction":name,"main_effects":[a,b],"folds":folds,"gate":g,"status":"validated_conditional_signal" if g["robust"] else "diagnostic_conditional_signal"})
    for pos in POSITIONS:
        ix=[i for i,r in enumerate(out) if r["position"]==pos]; q=bh_qvalues([(i,(out[i].get("gate") or {}).get("sign_flip_p")) for i in ix])
        for i in ix: out[i]["fdr_q"]=q.get(i)
    return out


def expansion_plan(features:List[dict]) -> List[dict]:
    out=[]
    for r in features:
        if r["evidence_status"] not in {"promising_underpowered","insufficient_coverage","horizon_specific","descriptive_not_incremental"}: continue
        action="collect_more_history" if r["evidence_status"]=="promising_underpowered" else "improve_source_coverage" if r["evidence_status"]=="insufficient_coverage" else "route_to_best_horizon" if r["evidence_status"]=="horizon_specific" else "test_predefined_condition_or_accept_redundancy"
        score=(40 if r["evidence_status"]=="promising_underpowered" else 30)+(1-r["coverage"])*25+min(20,abs(r.get("next3_spearman") or 0)*100)
        out.append({"position":r["position"],"feature":r["feature"],"status":r["evidence_status"],"priority_score":round(float(score),2),"recommended_action":action,
                    "current_coverage":r["coverage"],"current_seasons":r["season_n"],"estimated_total_temporal_folds_needed":r.get("estimated_total_folds_needed"),
                    "note":"Fold estimate is a planning heuristic from observed fold variance, not a guarantee of significance."})
    return sorted(out,key=lambda x:-x["priority_score"])


def summarize_m8(m8:dict) -> dict:
    mv=m8.get("matchup_validation",{}) if isinstance(m8,dict) else {}
    return {"validated_candidate_families":mv.get("validated_candidate_families",[]),
            "sequential_activation_positions":sorted((mv.get("sequential_activation",{}).get("model_specs") or {}).keys()),
            "rule":"Opponent-specific M8 evidence remains governed by M8 and is not pooled into M7 feature significance."}


def report_markdown(bundle:dict) -> str:
    lines=["# FIE Feature Evidence Research", "", f"Generated: {bundle['generated_at']}", "",
           "## Governance", "", "This layer is **research-only and fail-closed**. It does not alter FIE runtime projections. A candidate must still clear chronological out-of-sample testing, the temporal-block confidence interval, and downstream consumer integration before activation.", ""]
    feats=bundle["phase1_feature_evidence_matrix"]
    for pos in POSITIONS:
        p=[r for r in feats if r["position"]==pos]; counts={s:sum(r["evidence_status"]==s for r in p) for s in sorted({r["evidence_status"] for r in p})}
        lines += [f"## {pos}", "", "Status counts: "+", ".join(f"{k}={v}" for k,v in counts.items()) if counts else "No features available.", ""]
        top=sorted(p,key=lambda r:((r["weekly_gate"].get("mean") or -9)),reverse=True)[:8]
        if top:
            lines += ["| Feature | Family | Status | Coverage | Weekly ΔMAE | CI95 | Next3 ρ | Season gate |", "|---|---|---|---:|---:|---|---:|---|"]
            for r in top:
                g=r["weekly_gate"]; sg=r.get("season_gate") or {}; ci=f"{g.get('ci95_low'):.3f}..{g.get('ci95_high'):.3f}" if g.get('ci95_low') is not None else "n/a"
                lines.append(f"| {r['feature']} | {r['family']} | {r['evidence_status']} | {r['coverage']:.0%} | {(g.get('mean') or 0):.2%} | {ci} | {(r.get('next3_spearman') or 0):.3f} | {'PASS' if sg.get('robust') else 'no'} |")
            lines.append("")
    lines += ["## Phase 2: component targets",""]
    comp=bundle["phase2_component_validation"]; passed=[r for r in comp if r.get("feature")!="__all_features__" and (r.get("gate") or {}).get("robust")]
    if passed:
        for r in passed[:40]: lines.append(f"- {r['position']} {r['feature']} → {r['component']}: mean improvement={(r['gate'].get('mean') or 0):.2%}, FDR q={r.get('fdr_q')}")
    else: lines.append("- No individual component-specific feature gate cleared in this run.")
    for r in comp:
        if r.get("feature")=="__all_features__": lines.append(f"- {r['position']} {r['component']} all-feature challenger: {r['status']}, mean improvement={(r['gate'].get('mean') or 0):.2%}")
    lines += ["", "## Phase 3: validated future/tail horizons",""]
    robust=[r for r in bundle.get("phase3_multi_horizon_validation",[]) if (r.get("gate") or {}).get("robust")]
    if robust:
        for r in robust[:30]: lines.append(f"- {r['position']} {r['feature']} → {r['horizon']}: mean improvement={(r['gate'].get('mean') or 0):.2%}")
    else: lines.append("- No additional future/tail feature gate cleared in this run.")
    lines += ["", "## Phase 4: model challengers",""]
    for r in bundle["phase4_regularized_challengers"]:
        lines.append(f"- {r['position']} {r['model']}: mean ΔMAE={(r['gate'].get('mean') or 0):.2%}, CI low={r['gate'].get('ci95_low')}, {r['production_eligibility']}")
    lines += ["", "## Phase 5: conditional effects",""]
    for r in bundle["phase5_conditional_effects"]:
        lines.append(f"- {r['position']} {r['interaction']}: {r['status']}, incremental over main effects={(r['gate'].get('mean') or 0):.2%}")
    lines += ["", "## Phase 6: highest-priority data expansion",""]
    for r in bundle["phase6_data_expansion_plan"][:20]: lines.append(f"- {r['position']} {r['feature']}: {r['recommended_action']} (priority {r['priority_score']})")
    lines += ["", "## Phase 7: production gate", "", "No feature or challenger is auto-activated by this audit. `eligible_for_manual_consumer_integration` means only that the challenger cleared the same robust chronological gate and may be wired into a downstream model in a separate, revalidated change.", ""]
    return "\n".join(lines)


def json_safe(value):
    if isinstance(value,dict): return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [json_safe(v) for v in value]
    if isinstance(value,np.generic): value=value.item()
    if isinstance(value,float): return value if math.isfinite(value) else None
    return value


def write_outputs(bundle:dict,outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    safe=json_safe(bundle)
    (outdir/"feature_evidence.json").write_text(json.dumps(safe,indent=2,allow_nan=False))
    flat=[]
    for r in bundle["phase1_feature_evidence_matrix"]:
        q={k:v for k,v in r.items() if k not in {"weekly_gate","season_gate"}}; q.update({f"weekly_{k}":v for k,v in r["weekly_gate"].items()}); q.update({f"season_{k}":v for k,v in (r.get("season_gate") or {}).items()}); flat.append(q)
    pd.DataFrame(flat).to_csv(outdir/"feature_evidence_matrix.csv",index=False)
    pd.DataFrame(bundle["phase1_fold_evidence"]).to_csv(outdir/"feature_fold_evidence.csv",index=False)
    hflat=[]
    for r in bundle.get("phase3_multi_horizon_validation",[]):
        q={k:v for k,v in r.items() if k not in {"folds","gate"}}
        q.update({f"gate_{k}":v for k,v in (r.get("gate") or {}).items()}); hflat.append(q)
    pd.DataFrame(hflat).to_csv(outdir/"feature_horizon_validation.csv",index=False)
    pd.DataFrame(bundle["phase6_data_expansion_plan"]).to_csv(outdir/"data_expansion_plan.csv",index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!="folds"} for r in bundle["phase2_component_validation"]]).to_csv(outdir/"component_validation.csv",index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!="folds"} for r in bundle["phase4_regularized_challengers"]]).to_csv(outdir/"regularized_challengers.csv",index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!="folds"} for r in bundle["phase5_conditional_effects"]]).to_csv(outdir/"conditional_effects.csv",index=False)
    (outdir/"FEATURE_EVIDENCE_REPORT.md").write_text(report_markdown(bundle))


def load_live(args):
    from fie_m4 import feature_frame
    from fie_m7 import merge_optional_player_charting, add_derived_driver_features, available_catalog, load_oos
    df,team,identity,m1,m2,enrichment=feature_frame(args)
    df,optional=merge_optional_player_charting(df,args); df=add_derived_driver_features(df); catalog=available_catalog(df); oos=load_oos(args.derived_dir,args.fixture,df)
    return df,oos,catalog,{"enrichment":enrichment,"optional_charting":optional}


def run(args) -> dict:
    df,oos,catalog,source=load_live(args)
    frows,ffolds=feature_matrix(df,oos,catalog); horizons=horizon_validation(df,catalog); attach_horizon_status(frows,horizons)
    components=component_validation(df,catalog); attach_component_status(frows,components)
    challengers=challenger_validation(df,oos,catalog); interactions=interaction_validation(df,oos); expansion=expansion_plan(frows)
    m8={}
    p=Path(args.m8_bundle)
    if p.exists(): m8=json.loads(p.read_text())
    bundle={"schema_version":1,"research_build":BUILD,"generated_at":utc_now(),"status":"complete_research_only",
            "governance":{"auto_activation":False,"production_gate_unchanged":True,"multiple_testing":"exact fold-level sign-flip p-values + BH-FDR are exploratory safeguards; robust temporal-block gate remains authoritative","leakage_rule":"all validation uses chronological outer holdouts; challenger hyperparameters use only inner training-season validation"},
            "phase1_feature_evidence_matrix":frows,"phase1_fold_evidence":ffolds,"phase2_component_validation":components,
            "phase3_horizons":["same_week","next_week","next_3_games","rest_of_season","floor","ceiling","breakout","next_season"],
            "phase3_multi_horizon_validation":horizons,
            "phase4_regularized_challengers":challengers,"phase5_conditional_effects":interactions,"phase5_m8_matchup_evidence":summarize_m8(m8),
            "phase6_data_expansion_plan":expansion,
            "phase7_production_gate":{"rule":"No automatic activation. Only robust OOS candidates may proceed to a separate consumer integration and revalidation.",
                                      "eligible_challengers":[f"{r['position']}:{r['model']}" for r in challengers if r["production_eligibility"].startswith("eligible")]},
            "source_contract":source}
    return bundle


def fixture_data(seed=94):
    rng=np.random.default_rng(seed); rows=[]
    for season in range(2018,2026):
      for pidx,pos in enumerate(POSITIONS):
       for player in range(22):
        skill=rng.normal(); role=rng.normal()
        for week in range(1,15):
         opp=.65*role+.25*skill+rng.normal(scale=.45); eff=.55*skill+rng.normal(scale=.65); fp=8+3*opp+1.2*eff+rng.normal(scale=3)
         attempts=max(1.0,32+4*opp+rng.normal(scale=2)); carries=max(0.0,8+4*opp+rng.normal(scale=1.5)); targets=max(1.0,6+3*opp+rng.normal(scale=1))
         completions=max(0.0,attempts*np.clip(.63+.035*eff,.35,.85)); receptions=max(0.0,targets*np.clip(.66+.04*eff,.30,.95))
         rows.append({"season":season,"week":week,"canonical_player_id":f"{pos}{player}","position_model":pos,"fantasy_points":fp,
                      "attempts":attempts,"completions":completions,"passing_yards":attempts*max(3.0,7.1+.5*eff),
                      "carries":carries,"rushing_yards":carries*max(1.0,4.2+.45*eff),"targets":targets,"receptions":receptions,"receiving_yards":targets*max(2.0,8.5+1.1*eff),
                      "target_share_prior4":opp/10+.2,"offense_snap_share_prior4":.6+opp/20,"ngs_avg_separation_prior4":eff/4+3,
                      "carry_share_prior4":opp/10+.4,"ngs_rush_yards_over_expected_per_att_prior4":eff/3,
                      "qb_pass_attempt_share_prior4":.7+opp/20,"pfr_times_pressured_pct_prior4":.25-eff/30,"ngs_avg_time_to_throw_prior4":2.7+eff/20})
    d=pd.DataFrame(rows); o=d[["season","week","canonical_player_id","position_model","fantasy_points"]].copy(); o["fie_projection"]=d.fantasy_points*0.72+8*.28+rng.normal(scale=2.2,size=len(d)); return d,o


def self_test():
    d,o=fixture_data(); assert len(expanding_folds(d.season.unique()))>=4
    folds,g=validate_feature_increment(d,o,"WR","target_share_prior4"); assert len(folds)>=4 and g["mean"] is not None
    cats={p:{"fixture":[c for c in d.columns if c.endswith("prior4")]} for p in POSITIONS}
    comp=component_validation(d,cats); assert comp and all("gate" in x for x in comp)
    ch=challenger_validation(d,o,cats); assert ch and all("gate" in x for x in ch)
    inter=interaction_validation(d,o); assert isinstance(inter,list)
    print("PASS feature-evidence synthetic chronological integrity")


def parse_args(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--league-root",required=False,default="data/research")
    p.add_argument("--derived-dir",default="data/research/derived"); p.add_argument("--cache-dir",default=".cache/fie-research")
    p.add_argument("--seasons",default="2016-2025"); p.add_argument("--output-dir",required=False,default="data/research/feature-evidence")
    p.add_argument("--route-source",default=""); p.add_argument("--qb-coverage-source",default=""); p.add_argument("--fixture",action="store_true"); p.add_argument("--self-test",action="store_true")
    for i in range(1,10): p.add_argument(f"--m{i}-bundle",default=None)
    a=p.parse_args(argv)
    if a.self_test: return a
    lo,hi=map(int,str(a.seasons).split("-")); a.seasons=list(range(lo,hi+1))
    root=Path(a.league_root)
    for i in range(1,10):
        if getattr(a,f"m{i}_bundle") is None: setattr(a,f"m{i}_bundle",str(root/f"milestone{i}.json"))
    return a


def main(argv=None):
    a=parse_args(argv)
    if a.self_test: self_test(); return
    b=run(a); write_outputs(b,Path(a.output_dir)); print(f"Wrote feature evidence to {a.output_dir}: {len(b['phase1_feature_evidence_matrix'])} features")

if __name__=="__main__": main()
