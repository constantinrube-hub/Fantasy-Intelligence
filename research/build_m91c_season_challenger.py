#!/usr/bin/env python3
"""FIE M9.1c: role-cohort, density-aware residual challenger.

Research only. M9/M9.1/M9.1b remain unchanged.

M9.1c keeps Sleeper as the fixed preseason baseline, but allows FIE to express a
player-specific disagreement only after:
1. assigning a current role cohort from Sleeper projection + projected opportunity
   + point-in-time depth order;
2. comparing the player only with stable-team exact-replay references in the same
   position AND role cohort;
3. removing the local systematic raw-FIE-vs-Sleeper level relationship;
4. measuring FIE's residual signal relative to those true comparables;
5. scaling the correction by neighborhood density/proximity and transition risk;
6. enforcing a data-derived correction cap.

For team changes, context replacement is upgraded again:
- current Sleeper projected workload remains first priority;
- M8's canonical prior-season NEW-team pressure/sack environment replaces old-team
  QB pressure context;
- historical role estimators use current projected workload to estimate missing
  snap/red-zone role;
- depth-matched new-team historical role templates remain fallback only;
- old-team contextual features never survive merely because replacement is hard.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

import build_m91_season_challenger as m91
import build_m91b_season_challenger as m91b
from build_m9_season_board import evaluate_position_spec
from fie_m7 import add_derived_driver_features
from fie_m8 import build_team_context
from fie_m3 import add_public_enrichment, add_lagged_advanced, ensure_core_priors

RESEARCH_BUILD="M9.1c-ROLE-COHORT-DENSITY-RELIABILITY"
SCHEMA_VERSION=1
OFFENSE={"QB","RB","WR","TE"}
COHORTS=("CLEAR_STARTER","STARTER","COMMITTEE_FRINGE","DEPTH")
MIN_REFERENCE=6
MAX_REFERENCE=12

ROLE_ESTIMATOR_SPECS={
    "QB":{
        "snap_share_prior4":["qb_pass_attempt_share_prior4","qb_rush_share_prior4"],
        "inside_5_carry_share_prior4":["qb_rush_share_prior4"],
    },
    "RB":{
        "offense_snap_share_prior4":["carry_share_prior4","target_share_prior4"],
        "red_zone_carry_share_prior4":["carry_share_prior4"],
        "inside_5_carry_share_prior4":["carry_share_prior4"],
        "red_zone_target_share_prior4":["target_share_prior4"],
    },
    "WR":{
        "offense_snap_share_prior4":["target_share_prior4"],
        "red_zone_target_share_prior4":["target_share_prior4"],
    },
    "TE":{
        "offense_snap_share_prior4":["target_share_prior4"],
        "red_zone_target_share_prior4":["target_share_prior4"],
    },
}


def num(x:Any)->Optional[float]:
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None


def json_safe(value:Any)->Any:
    """Convert numpy/pandas and non-finite audit values to strict JSON values."""
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,set)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        value=value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def latest_team_environment(
    player_week:pd.DataFrame, *,
    identity:Optional[pd.DataFrame]=None,
    cache_dir:Optional[Path]=None,
    seasons:Optional[list[int]]=None,
    profiles:Optional[pd.DataFrame]=None,
)->dict:
    """Build the prior-season NEW-team QB environment through the canonical M3→M8 path.

    The real M1 rehydrated table does not contain PFR/NGS advanced columns.
    M4's authoritative feature_frame first:
      1. merges public enrichment (PFR/NGS/participation),
      2. creates time-safe lagged advanced features,
      3. then later layers consume those features.

    M9.1c must therefore do the same before asking M8 to aggregate
    `pfr_times_pressured_pct_prior4` / `pfr_times_sacked_prior4`.
    """
    if player_week.empty:
        return {}

    raw_season=pd.to_numeric(player_week.get("season"),errors="coerce")
    valid_seasons=sorted({int(x) for x in raw_season.dropna().tolist()})
    use_seasons=seasons or valid_seasons
    if not use_seasons:
        return {}
    latest=max(use_seasons)

    enriched=player_week.copy()
    enrichment_meta={"feature_columns":[]}
    if identity is not None and not identity.empty and cache_dir is not None:
        # This is the same public-enrichment + lagging sequence used by
        # `fie_m4.feature_frame()`. SourceManager reuses the already-rehydrated
        # league cache and only fetches an optional source if genuinely absent.
        enriched,enrichment_meta=add_public_enrichment(
            enriched, identity, str(cache_dir), use_seasons
        )
        enriched=ensure_core_priors(enriched)
        enriched=add_lagged_advanced(
            enriched, enrichment_meta.get("feature_columns",[])
        )

    # M7 adds interactions only after the underlying advanced lagged inputs exist.
    enriched=add_derived_driver_features(enriched)

    season=pd.to_numeric(enriched.get("season"),errors="coerce")
    z=enriched[season.eq(latest)].copy()
    rows={}

    # Primary path: canonical M8 team aggregation.
    team=build_team_context(z)
    if not team.empty:
        team["team_canonical"]=team["team"].map(m91b.canonical_team)
        for tm,g in team.sort_values("week").groupby("team_canonical"):
            r=g.iloc[-1]
            vals={
                "profile_season":latest,
                "source":"M3_PUBLIC_ENRICHMENT_TO_M8_TEAM_ENVIRONMENT",
                "pfr_times_pressured_pct_prior4":num(r.get("off_pressure_environment")),
                "pfr_times_sacked_prior4":num(r.get("off_sack_environment")),
                "ngs_avg_time_to_throw_prior4":num(r.get("off_time_to_throw")),
            }
            if any(vals[k] is not None for k in (
                "pfr_times_pressured_pct_prior4","pfr_times_sacked_prior4"
            )):
                rows[str(tm)]=vals

    # Provenance-preserving direct fallback over the exact same M3-lagged fields.
    qb=z[z.position_model.astype(str).str.upper().eq("QB")].copy()
    if not qb.empty and "team" in qb.columns:
        qb["team_canonical"]=qb["team"].map(m91b.canonical_team)
        for tm,g in qb.sort_values("week").groupby("team_canonical"):
            existing=rows.get(str(tm),{})
            if (
                existing.get("pfr_times_pressured_pct_prior4") is not None
                and existing.get("pfr_times_sacked_prior4") is not None
            ):
                continue
            tail=g.tail(4)
            def _mean(col):
                if col not in tail.columns:
                    return None
                x=pd.to_numeric(tail[col],errors="coerce").dropna()
                return float(x.mean()) if len(x) else None
            vals={
                "profile_season":latest,
                "source":"M3_LAGGED_QB_NEW_TEAM_ENVIRONMENT",
                "pfr_times_pressured_pct_prior4":_mean("pfr_times_pressured_pct_prior4"),
                "pfr_times_sacked_prior4":_mean("pfr_times_sacked_prior4"),
                "ngs_avg_time_to_throw_prior4":_mean("ngs_avg_time_to_throw_prior4"),
            }
            if any(vals[k] is not None for k in (
                "pfr_times_pressured_pct_prior4","pfr_times_sacked_prior4"
            )):
                rows[str(tm)]=vals

    # Final fallback to the deterministic latest profile generated from the same
    # committed M9 feature contract. This is only used if an optional public source
    # genuinely lacks a team's coverage.
    if profiles is not None and not profiles.empty:
        q=profiles[profiles.position_model.astype(str).str.upper().eq("QB")].copy()
        if not q.empty and "profile_team" in q.columns:
            q["team_canonical"]=q["profile_team"].map(m91b.canonical_team)
            for tm,g in q.groupby("team_canonical"):
                existing=rows.get(str(tm),{})
                pressure=existing.get("pfr_times_pressured_pct_prior4")
                sacks=existing.get("pfr_times_sacked_prior4")
                if pressure is not None and sacks is not None:
                    continue
                def _median(col):
                    if col not in g.columns:
                        return None
                    x=pd.to_numeric(g[col],errors="coerce").dropna()
                    return float(x.median()) if len(x) else None
                vals={
                    "profile_season":latest,
                    "source":"M9_LATEST_PROFILE_NEW_TEAM_ENVIRONMENT",
                    "pfr_times_pressured_pct_prior4":(
                        pressure if pressure is not None
                        else _median("pfr_times_pressured_pct_prior4")
                    ),
                    "pfr_times_sacked_prior4":(
                        sacks if sacks is not None
                        else _median("pfr_times_sacked_prior4")
                    ),
                    "ngs_avg_time_to_throw_prior4":(
                        existing.get("ngs_avg_time_to_throw_prior4")
                        if existing.get("ngs_avg_time_to_throw_prior4") is not None
                        else _median("ngs_avg_time_to_throw_prior4")
                    ),
                }
                if any(vals[k] is not None for k in (
                    "pfr_times_pressured_pct_prior4","pfr_times_sacked_prior4"
                )):
                    rows[str(tm)]=vals
    return rows


def fit_role_estimators(player_week:pd.DataFrame)->tuple[dict,list[dict]]:
    """Historical football-role mapping, never fantasy-points regression.

    These regressions estimate a missing *role variable* from another current role
    variable (e.g. snap share from current target/carry share). They do not use
    Sleeper fantasy points or ADP and therefore do not create a second projection
    model.
    """
    models={}
    audit=[]
    if player_week.empty:
        return models,audit
    d=player_week.copy()
    for pos,targets in ROLE_ESTIMATOR_SPECS.items():
        z=d[d.position_model.astype(str).str.upper().eq(pos)].copy()
        for target,features in targets.items():
            fs=[f for f in features if f in z.columns]
            if target not in z.columns or not fs:
                audit.append({"position":pos,"target":target,"status":"UNAVAILABLE_COLUMNS","features":fs})
                continue
            q=z[[target]+fs].apply(pd.to_numeric,errors="coerce").dropna()
            if len(q)<100:
                audit.append({"position":pos,"target":target,"status":"INSUFFICIENT_HISTORY","n":int(len(q)),"features":fs})
                continue
            X=q[fs].to_numpy(float); y=q[target].to_numpy(float)
            try:
                model=HuberRegressor(epsilon=1.35,alpha=.5,max_iter=500).fit(X,y)
            except Exception as e:
                audit.append({"position":pos,"target":target,"status":"FIT_FAILED","n":int(len(q)),"error":str(e)})
                continue
            models[(pos,target)]=(model,fs)
            pred=model.predict(X)
            mae=float(np.mean(np.abs(y-pred)))
            audit.append({"position":pos,"target":target,"status":"FIT","n":int(len(q)),"features":fs,"in_sample_role_mae":mae})
    return models,audit


def apply_role_estimator(
    adapted:dict, *, pos:str, target:str, models:dict
)->Optional[float]:
    item=models.get((pos,target))
    if not item:
        return None
    model,fs=item
    vals=[]
    for f in fs:
        x=num(adapted.get(f))
        if x is None:
            return None
        vals.append(x)
    try:
        v=float(model.predict([vals])[0])
    except Exception:
        return None
    # These role quantities are shares/rates.
    return float(max(0.0,min(1.0,v)))


def replace_transition_context_v3(
    profile:dict, *,
    cid:str,pos:str,current_team:str,spec:dict,
    context:dict,profiles:pd.DataFrame,availability:Optional[dict],
    change_scales:dict,role_models:dict,team_environment:dict,
)->tuple[dict,dict]:
    """M9.1b transition adapter plus current-role and canonical M8 replacements."""
    adapted,audit=m91b.adapt_transition_profile(
        profile,cid=cid,pos=pos,current_team=current_team,spec=spec,
        context=context,profiles=profiles,availability=availability,
        change_scales=change_scales,
    )
    if not audit.get("team_changed"):
        audit["status"]="STABLE_TEAM"
        audit["role_estimator"]=[]
        audit["m8_team_environment"]=[]
        return adapted,audit

    audit["status"]="NEW_TEAM_CONTEXT_REBUILT_V3"
    audit["role_estimator"]=[]
    audit["m8_team_environment"]=[]
    cur=m91b.canonical_team(current_team)
    required=m91b.required_features(spec)

    # Replace explicit QB pressure/sack environment from the NEW team's canonical
    # M8 public protection context. This supersedes generic donor/imputation.
    tenv=team_environment.get(cur) or {}
    for f in ("pfr_times_pressured_pct_prior4","pfr_times_sacked_prior4"):
        if f in required and num(tenv.get(f)) is not None:
            adapted[f]=float(tenv[f])
            audit["m8_team_environment"].append(f)

    # When current workload gives enough information, estimate missing contextual
    # role directly from historical role relationships. This takes priority over
    # the depth-matched donor template because it uses THIS player's new-team load.
    for target in ROLE_ESTIMATOR_SPECS.get(pos,{}):
        if target not in required:
            continue
        current_market=set(audit.get("current_context") or [])
        if target in current_market:
            continue
        est=apply_role_estimator(adapted,pos=pos,target=target,models=role_models)
        if est is not None:
            adapted[target]=est
            audit["role_estimator"].append(target)

    # Rebuild transition change score after all v3 replacements.
    if "opportunity_change_score_prior1" in required:
        score=m91b.transition_change_score(profile,adapted,pos,change_scales)
        if score is not None:
            adapted["opportunity_change_score_prior1"]=float(score)
            if "opportunity_change_score_prior1" not in audit["current_context"]:
                audit["current_context"].append("opportunity_change_score_prior1")

    # Clean audit: anything now populated must not still be reported as cleared.
    populated=set(audit.get("current_context") or [])|set(audit.get("role_template") or [])|set(
        audit.get("team_environment") or []
    )|set(audit.get("role_estimator") or [])|set(audit.get("m8_team_environment") or [])
    audit["cleared"]=[f for f in (audit.get("cleared") or []) if f not in populated and num(adapted.get(f)) is None]

    # Derived interactions must reflect the new context, not old-team components.
    adapted=add_derived_driver_features(pd.DataFrame([adapted])).iloc[0].to_dict()
    return adapted,audit


def all_depth_orders(df:pd.DataFrame,availability:dict)->pd.Series:
    vals=[]
    for _,r in df.iterrows():
        rec=availability.get(str(r.get("sleeper_id") or "")) or {}
        d=num(rec.get("depth_chart_order"))
        vals.append(int(d) if d is not None and d>=1 else np.nan)
    return pd.Series(vals,index=df.index,dtype=float)


def assign_role_cohorts(
    df:pd.DataFrame, *, context:dict, availability:dict
)->pd.DataFrame:
    """Current role groups from baseline + new-team workload + depth order.

    Market projection is intentionally included because it is the baseline we are
    trying to improve. The cohort is not itself a FIE bonus. It prevents comparing
    players whose baseline roles are structurally different.
    """
    d=df.copy()
    d["m91c_market_percentile"]=np.nan
    mkt=pd.to_numeric(d["sleeper_market_projection"],errors="coerce")
    for pos,idx in d.groupby("position_model").groups.items():
        g=d.loc[list(idx)]
        valid=mkt.loc[g.index].gt(0)&mkt.loc[g.index].notna()
        ranks=mkt.loc[g.index][valid].rank(pct=True,method="average")
        d.loc[ranks.index,"m91c_market_percentile"]=ranks

    workload=[]
    for _,r in d.iterrows():
        cid=str(r.get("canonical_player_id") or "")
        pos=str(r.get("position_model") or "").upper()
        vals=(context.get(cid) or {}).get("values") or {}
        if pos=="QB":
            w=num(vals.get("qb_pass_attempt_share_prior4"))
        elif pos=="RB":
            cs=num(vals.get("carry_share_prior4")); ts=num(vals.get("target_share_prior4"))
            xs=[x for x in (cs,ts) if x is not None]
            w=max(xs) if xs else None
        elif pos in {"WR","TE"}:
            w=num(vals.get("target_share_prior4"))
        else:
            w=None
        workload.append(w)
    d["m91c_current_workload_share"]=workload
    d["m91c_workload_percentile"]=np.nan
    for pos,idx in d.groupby("position_model").groups.items():
        x=pd.to_numeric(d.loc[list(idx),"m91c_current_workload_share"],errors="coerce").dropna()
        if len(x):
            d.loc[x.index,"m91c_workload_percentile"]=x.rank(pct=True,method="average")

    d["m91c_depth_chart_order"]=all_depth_orders(d,availability)
    scores=[]
    cohorts=[]
    for _,r in d.iterrows():
        mp=num(r.get("m91c_market_percentile"))
        wp=num(r.get("m91c_workload_percentile"))
        dep=num(r.get("m91c_depth_chart_order"))
        pos=str(r.get("position_model") or "").upper()
        if mp is None:
            scores.append(np.nan);cohorts.append("UNRANKED");continue
        score=float(np.mean([x for x in (mp,wp) if x is not None]))
        # Depth order is a structural cap, not a projection bonus.
        if pos=="QB" and dep is not None and dep>=2:
            score=min(score,.24 if mp<.75 else .49)
        elif dep is not None and dep>=4:
            score=min(score,.24)
        elif pos in {"RB","WR","TE"} and dep is not None and dep>=3:
            score=min(score,.49)
        scores.append(score)
        if score>=.75: c="CLEAR_STARTER"
        elif score>=.50: c="STARTER"
        elif score>=.25: c="COMMITTEE_FRINGE"
        else: c="DEPTH"
        cohorts.append(c)
    d["m91c_role_score"]=scores
    d["m91c_role_cohort"]=cohorts
    return d


def robust_scale(x:np.ndarray)->float:
    a=np.asarray(x,dtype=float)
    a=a[np.isfinite(a)]
    if len(a)<2:return 0.0
    med=float(np.median(a));mad=float(np.median(np.abs(a-med)))
    if mad>1e-9:return mad*1.4826
    sd=float(np.std(a,ddof=1))
    return sd if math.isfinite(sd) else 0.0


def role_cohort_residual_anchor(
    df:pd.DataFrame,min_reference:int=MIN_REFERENCE,max_reference:int=MAX_REFERENCE
)->tuple[pd.Series,pd.DataFrame]:
    """Role-conditioned FIE residual with density/proximity reliability."""
    out=pd.Series(np.nan,index=df.index,dtype=float)
    d=df.copy()
    d["_mkt"]=pd.to_numeric(d["sleeper_market_projection"],errors="coerce")
    d["_raw"]=pd.to_numeric(d["m91c_raw_fie_projection"],errors="coerce")
    exact=d["m91c_exact_scoring_replay"].fillna(False).astype(bool)
    changed=d["m91c_team_changed"].fillna(False).astype(bool)
    audits=[]

    for pos,pidx in d.groupby("position_model").groups.items():
        gp=d.loc[list(pidx)]
        positive=gp["_mkt"].dropna()
        pos_iqr=float(positive.quantile(.75)-positive.quantile(.25)) if len(positive) else 0.0
        if pos_iqr<=1e-9:
            pos_iqr=max(1.0,float(positive.std() or 1.0))

        for cohort,cidx in gp.groupby("m91c_role_cohort").groups.items():
            if cohort=="UNRANKED":continue
            g=d.loc[list(cidx)]
            ref=g[
                exact.loc[g.index]&~changed.loc[g.index]&
                g["_mkt"].gt(0)&g["_raw"].notna()
            ].copy()
            if len(ref)<min_reference:
                audits.append({
                    "position_model":pos,"role_cohort":cohort,
                    "status":"INSUFFICIENT_SAME_COHORT_REFERENCE",
                    "reference_n":int(len(ref)),
                })
                continue

            k=max(min_reference,min(max_reference,int(round(math.sqrt(len(ref))*2))))
            for ridx,r in g[
                exact.loc[g.index]&g["_mkt"].gt(0)&g["_raw"].notna()
            ].iterrows():
                local=ref.assign(_distance=(ref["_mkt"]-float(r["_mkt"])).abs()).sort_values(
                    ["_distance","_mkt"],ascending=[True,False]
                ).head(k)
                if len(local)<min_reference:continue
                X=local[["_mkt"]].to_numpy(float);y=local["_raw"].to_numpy(float)
                try:
                    if local["_mkt"].nunique()<3:raise ValueError("low local variation")
                    fit=HuberRegressor(epsilon=1.35,alpha=.5,max_iter=500).fit(X,y)
                    expected_ref=fit.predict(X)
                    expected=float(fit.predict([[float(r["_mkt"])]])[0])
                    fit_method="HUBER_LOCAL_ROLE_COHORT"
                except Exception:
                    offset=float(np.median(local["_raw"]-local["_mkt"]))
                    expected_ref=local["_mkt"].to_numpy(float)+offset
                    expected=float(r["_mkt"])+offset
                    fit_method="MEDIAN_OFFSET_ROLE_COHORT"

                ref_resid=local["_raw"].to_numpy(float)-expected_ref
                resid=float(r["_raw"])-expected
                scale=robust_scale(ref_resid)
                signal_z=(resid-float(np.median(ref_resid)))/scale if scale>1e-9 else 0.0

                sr=np.sort(ref_resid);n=len(sr)
                left=np.searchsorted(sr,resid,side="left");right=np.searchsorted(sr,resid,side="right")
                q=float(np.clip(((left+right)/2.0+.5)/n,0.0,1.0))
                extremity=float(abs(q-.5)*2.0)

                ms=np.sort(local["_mkt"].to_numpy(float))
                qgrid=(np.arange(n,dtype=float)+.5)/n
                market_dev=ms-float(np.median(ms))
                market_scale_adj=float(np.interp(q,qgrid,market_dev,left=market_dev[0],right=market_dev[-1]))

                span=float(ms.max()-ms.min())
                median_distance=float(np.median(np.abs(ms-float(r["_mkt"]))))
                density_reliability=float(1.0/(1.0+span/pos_iqr))
                proximity_reliability=float(1.0/(1.0+2.0*median_distance/pos_iqr))
                transition_mult=max(1.0,float(r.get("m91c_uncertainty_spread_multiplier") or 1.0))
                transition_reliability=float(1.0/transition_mult) if bool(r.get("m91c_team_changed")) else 1.0
                reliability=density_reliability*proximity_reliability*transition_reliability

                pre_cap=market_scale_adj*reliability
                # Data-derived cap: correction may not exceed the typical distance
                # to its local comparables nor M9's smaller one-sided P10/P90 spread.
                p10=num(r.get("p10"));p50=num(r.get("p50"));p90=num(r.get("p90"))
                uncertainty_cap=None
                if p10 is not None and p50 is not None and p90 is not None:
                    uncertainty_cap=min(abs(p50-p10),abs(p90-p50))
                caps=[max(1.0,median_distance)]
                if uncertainty_cap is not None and uncertainty_cap>0:
                    caps.append(float(uncertainty_cap))
                cap=float(min(caps))
                applied=float(np.clip(pre_cap,-cap,cap))
                out.loc[ridx]=float(r["_mkt"])+applied

                d.loc[ridx,"m91c_local_expected_raw_fie"]=expected
                d.loc[ridx,"m91c_raw_fie_residual"]=resid
                d.loc[ridx,"m91c_signal_z"]=signal_z
                d.loc[ridx,"m91c_signal_percentile"]=q
                d.loc[ridx,"m91c_signal_extremity"]=extremity
                d.loc[ridx,"m91c_raw_market_scale_adjustment"]=market_scale_adj
                d.loc[ridx,"m91c_density_reliability"]=density_reliability
                d.loc[ridx,"m91c_proximity_reliability"]=proximity_reliability
                d.loc[ridx,"m91c_transition_reliability"]=transition_reliability
                d.loc[ridx,"m91c_total_reliability"]=reliability
                d.loc[ridx,"m91c_correction_cap"]=cap
                d.loc[ridx,"m91c_applied_adjustment"]=applied
                d.loc[ridx,"m91c_reference_n"]=n
                d.loc[ridx,"m91c_reference_market_span"]=span
                d.loc[ridx,"m91c_reference_median_distance"]=median_distance
                d.loc[ridx,"m91c_fit_method"]=fit_method
                d.loc[ridx,"m91c_reference_role_cohort"]=cohort

            audits.append({
                "position_model":pos,"role_cohort":cohort,
                "status":"ROLE_COHORT_LOCAL_RESIDUAL",
                "stable_reference_n":int(len(ref)),
                "adaptive_neighbor_n":int(k),
                "position_market_iqr":pos_iqr,
            })

    for c in [c for c in d.columns if c.startswith("m91c_")]:
        df[c]=d[c]
    return out,pd.DataFrame(audits)


def build(args)->tuple[pd.DataFrame,dict]:
    base,meta_b=m91b.build(args)
    league_root=Path("data/research/leagues")/str(args.league_id)
    m1=m91.load_json(str(league_root/"milestone1.json"))
    m9=m91.load_json(str(league_root/"milestone9.json"))
    scoring=(m1.get("scoring") or {}).get("settings",{})
    market_root=Path(args.market_root)
    market_path=Path(args.market_snapshot) if args.market_snapshot else m91.latest_market_snapshot(market_root,args.season)
    market=m91.load_market(str(market_path))
    market_by_cid=m91.build_market_record_index(market)
    context,_=m91b.build_enhanced_market_context(market,args.games)

    player_week_path=Path(args.player_week) if args.player_week else Path(
        f".cache/fie-research/leagues/{args.league_id}/derived/player_week.csv.gz"
    )
    pw=pd.read_csv(player_week_path,low_memory=False)
    profiles,profile_path,profile_source=m91._profiles(
        m9,override=args.profile_table,player_week_path=player_week_path,
        rehydrated_output=player_week_path.parent/"m9_preseason_latest_profiles_rehydrated.csv.gz",
    )
    by_pid={str(r["canonical_player_id"]):r for r in profiles.to_dict("records") if r.get("canonical_player_id") is not None}
    preseason=m9.get("preseason_season_projection",{}) or {}
    specs=preseason.get("diagnostic_model_specs",{}) or preseason.get("model_specs",{}) or {}

    availability_path=Path(args.availability_snapshot) if args.availability_snapshot else m91b.latest_availability(
        Path(args.availability_root),args.season
    )
    avail_rows=m91b.load_jsonl_gz(availability_path)
    availability=m91b.availability_index(avail_rows)
    change_scales=m91b.historical_change_scales(pw)
    role_models,role_model_audit=fit_role_estimators(pw)
    identity_path=player_week_path.parent/"player_identity.csv.gz"
    identity=pd.read_csv(identity_path,low_memory=False) if identity_path.is_file() else pd.DataFrame()
    history_seasons=sorted({
        int(x) for x in pd.to_numeric(pw.get("season"),errors="coerce").dropna().tolist()
    })
    new_team_env=latest_team_environment(
        pw,
        identity=identity,
        cache_dir=player_week_path.parent.parent,
        seasons=history_seasons,
        profiles=profiles,
    )
    volatility=m91.transition_volatility(player_week_path)
    residual_gate=m91.market_history_status(market_root,args.season)

    out=base.copy()
    out["m91c_research_build"]=RESEARCH_BUILD
    out["m91c_projection"]=pd.to_numeric(out["sleeper_market_projection"],errors="coerce")
    out["m91c_raw_fie_projection"]=pd.to_numeric(out["m91b_raw_fie_projection"],errors="coerce")
    out["m91c_exact_scoring_replay"]=out["m91b_exact_scoring_replay"].fillna(False).astype(bool)
    out["m91c_team_changed"]=out["m91b_team_changed"].fillna(False).astype(bool)
    out["m91c_uncertainty_spread_multiplier"]=pd.to_numeric(out["m91b_uncertainty_spread_multiplier"],errors="coerce").fillna(1.0)
    out["m91c_team_transition_status"]=out["m91b_team_transition_status"].astype(str)
    for c in (
        "m91c_context_current_fields","m91c_context_role_estimator_fields",
        "m91c_context_role_template_fields","m91c_context_m8_environment_fields",
        "m91c_context_other_team_environment_fields","m91c_context_proxy_fields",
        "m91c_context_cleared_fields",
    ):
        out[c]=""
    out["m91c_production_eligible"]=False
    out["m91c_status"]="BASELINE_ONLY"

    # Recompute only true team changers with v3 context. Stable players retain the
    # already exact M9.1b raw FIE result.
    for ridx,row in out[out["m91c_team_changed"]].iterrows():
        pos=str(row.get("position_model") or "").upper()
        cid=str(row.get("canonical_player_id") or "")
        profile=by_pid.get(cid)
        spec=specs.get(pos) or {}
        if pos not in OFFENSE or not profile or not spec:
            continue
        sid=str(row.get("sleeper_id") or "")
        adapted,audit=replace_transition_context_v3(
            profile,cid=cid,pos=pos,current_team=str(row.get("team") or ""),spec=spec,
            context=context,profiles=profiles,availability=availability.get(sid),
            change_scales=change_scales,role_models=role_models,team_environment=new_team_env,
        )
        return_ctx=m91.sleeper_return_context(market_by_cid.get(cid,{}))
        ev=evaluate_position_spec(spec,adapted,scoring,pos,return_raw=return_ctx)
        exact=bool((ev.get("coverage") or {}).get("exact_linear_replay"))
        ppg=num(ev.get("ppg"))
        raw=ppg*args.games if exact and ppg is not None else None

        out.at[ridx,"m91c_raw_fie_projection"]=raw
        out.at[ridx,"m91c_exact_scoring_replay"]=exact
        out.at[ridx,"m91c_team_transition_status"]=audit.get("status")
        out.at[ridx,"m91c_context_current_fields"]="|".join(sorted(set(audit.get("current_context") or [])))
        out.at[ridx,"m91c_context_role_estimator_fields"]="|".join(sorted(set(audit.get("role_estimator") or [])))
        out.at[ridx,"m91c_context_role_template_fields"]="|".join(sorted(set(audit.get("role_template") or [])))
        out.at[ridx,"m91c_context_m8_environment_fields"]="|".join(sorted(set(audit.get("m8_team_environment") or [])))
        out.at[ridx,"m91c_context_other_team_environment_fields"]="|".join(sorted(set(audit.get("team_environment") or [])))
        out.at[ridx,"m91c_context_proxy_fields"]="|".join(sorted(set(audit.get("proxy_fields") or [])))
        out.at[ridx,"m91c_context_cleared_fields"]="|".join(sorted(set(audit.get("cleared") or [])))
        out.at[ridx,"m91c_status"]="RESEARCH_ONLY_TRANSITION_EXACT_REPLAY" if raw is not None else "BASELINE_ONLY_DATA_OR_SCORING_GAP"

    stable=~out["m91c_team_changed"]
    out.loc[stable&out["m91c_exact_scoring_replay"],"m91c_status"]="RESEARCH_ONLY_EXACT_REPLAY"

    out=assign_role_cohorts(out,context=context,availability=availability)
    anchored,cal_audit=role_cohort_residual_anchor(out)
    ok=anchored.notna()
    out.loc[ok,"m91c_projection"]=anchored.loc[ok]
    out["m91c_calibration_method"]=np.where(ok,"ROLE_COHORT_LOCAL_RESIDUAL","BASELINE_ONLY")

    mkt=pd.to_numeric(out["sleeper_market_projection"],errors="coerce")
    proj=pd.to_numeric(out["m91c_projection"],errors="coerce")
    out["m91c_delta_vs_sleeper"]=proj-mkt
    out["m91c_delta_pct_vs_sleeper"]=np.where(mkt.abs()>1e-9,(proj-mkt)/mkt.abs()*100.0,np.nan)

    base_center=pd.to_numeric(out["fie_season_mean"],errors="coerce").where(
        pd.to_numeric(out["fie_season_mean"],errors="coerce").notna(),mkt
    )
    for qn in ("p10","p25","p50","p75","p90"):
        baseq=pd.to_numeric(out[qn],errors="coerce")
        spread=(baseq-base_center)*out["m91c_uncertainty_spread_multiplier"]
        out[f"m91c_{qn}"]=proj+spread

    out["m91c_position_rank"]=out.groupby("position_model")["m91c_projection"].rank(method="min",ascending=False)
    out["m91c_market_position_rank"]=out.groupby("position_model")["sleeper_market_projection"].rank(method="min",ascending=False)
    out["m91c_rank_delta_vs_market"]=out["m91c_market_position_rank"]-out["m91c_position_rank"]

    meta={
        "schema_version":SCHEMA_VERSION,"research_build":RESEARCH_BUILD,
        "league_id":str(args.league_id),"season":int(args.season),
        "status":"RESEARCH_ONLY_BLOCKED_PROMOTION",
        "production_eligible":False,"automatic_promotion":False,
        "sleeper_is_fixed_baseline":True,"adp_in_football_model":False,
        "calibration":{
            "method":"ROLE_COHORT_LOCAL_RESIDUAL",
            "role_inputs":["Sleeper projection percentile","current projected opportunity share","Sleeper depth_chart_order"],
            "cohorts":list(COHORTS),
            "same_cohort_only":True,
            "min_reference":MIN_REFERENCE,"max_reference":MAX_REFERENCE,
            "density_reliability":"1/(1 + local_market_span / position_market_IQR)",
            "proximity_reliability":"1/(1 + 2*median_neighbor_distance / position_market_IQR)",
            "transition_reliability":"1 / empirical team-change volatility multiplier",
            "correction_cap":"min(median local baseline distance, smaller M9 one-sided P10/P90 spread)",
            "signal_output":"raw FIE residual z-score + percentile/extremity are retained separately from applied correction",
            "audit":cal_audit.to_dict("records") if not cal_audit.empty else [],
        },
        "team_transition_policy":{
            "applies_to_positions":sorted(OFFENSE),
            "team_change_is_never_a_block_reason":True,
            "old_team_context_carried":False,
            "m8_new_team_environment":["pfr_times_pressured_pct_prior4","pfr_times_sacked_prior4"],
            "current_workload_role_estimators":ROLE_ESTIMATOR_SPECS,
            "role_estimator_audit":role_model_audit,
            "depth_template_is_fallback":True,
            "derived_interactions_recomputed":True,
        },
        "market_snapshot":str(market_path),
        "availability_snapshot":str(availability_path) if availability_path else None,
        "profile_table":str(profile_path),"profile_source":profile_source,
        "residual_model_gate":residual_gate,
        "transition_volatility":volatility,
        "rows":int(len(out)),
        "exact_replay_rows":int(out["m91c_exact_scoring_replay"].sum()),
        "true_team_changes":int(out["m91c_team_changed"].sum()),
        "adjusted_rows":int(ok.sum()),
        "notes":[
            "No production integration or activation path.",
            "Historical Actual-minus-Sleeper preseason validation remains required before promotion.",
            "M9.1c separates signal magnitude from applied correction reliability.",
        ],
    }
    return out,meta


FOCUS=[
 "Lamar Jackson","Kyler Murray","Malik Willis","Jaylen Waddle","David Montgomery",
 "Carson Wentz","Cam Ward","Geno Smith","Justin Fields","Shedeur Sanders",
 "Christian McCaffrey","Trey McBride","Jaxon Smith-Njigba","Aaron Rodgers",
]


def write_summary(df:pd.DataFrame,meta:dict,path:Path):
    q=df[df.full_name.astype(str).isin(FOCUS)].copy()
    cols=[
      "full_name","position_model","team","profile_team","m91c_team_changed",
      "sleeper_market_projection","m91_projection","m91b_projection",
      "m91c_raw_fie_projection","m91c_role_cohort","m91c_role_score",
      "m91c_depth_chart_order","m91c_current_workload_share",
      "m91c_local_expected_raw_fie","m91c_raw_fie_residual","m91c_signal_z",
      "m91c_signal_percentile","m91c_signal_extremity",
      "m91c_raw_market_scale_adjustment","m91c_density_reliability",
      "m91c_proximity_reliability","m91c_transition_reliability",
      "m91c_total_reliability","m91c_correction_cap","m91c_applied_adjustment",
      "m91c_projection","m91c_delta_vs_sleeper","m91c_market_position_rank",
      "m91c_position_rank","m91c_rank_delta_vs_market",
      "m91c_context_current_fields","m91c_context_role_estimator_fields",
      "m91c_context_role_template_fields","m91c_context_m8_environment_fields",
      "m91c_context_other_team_environment_fields","m91c_context_cleared_fields",
      "m91c_uncertainty_spread_multiplier",
    ]
    players=[]
    for r in q[[c for c in cols if c in q.columns]].to_dict("records"):
        players.append({k:(None if pd.isna(v) else v) for k,v in r.items()})
    path.write_text(json.dumps(json_safe({**meta,"focus_players":players}),indent=2,allow_nan=False,default=str)+"\n")


def write_evaluation(df:pd.DataFrame,meta:dict,path:Path):
    rows=[]
    for pos,g in df[df.position_model.astype(str).isin(OFFENSE)].groupby("position_model"):
        exact=g[g.m91c_exact_scoring_replay.fillna(False).astype(bool)].copy()
        mkt=pd.to_numeric(exact.sleeper_market_projection,errors="coerce")
        c=pd.to_numeric(exact.m91c_projection,errors="coerce")
        b=pd.to_numeric(exact.m91b_projection,errors="coerce")
        adj=(c-mkt).abs()
        valid=mkt.notna()&c.notna()
        rows.append({
            "position_model":pos,
            "exact_rows":int(len(exact)),
            "adjusted_rows":int(((c-mkt).abs()>1e-9).sum()),
            "spearman_m91c_vs_sleeper":float(c[valid].corr(mkt[valid],method="spearman")) if int(valid.sum())>=3 else None,
            "spearman_m91c_vs_m91b":float(c.corr(b,method="spearman")) if c.notna().sum()>=3 and b.notna().sum()>=3 else None,
            "median_abs_adjustment":float(adj.median()) if adj.notna().any() else None,
            "p90_abs_adjustment":float(adj.quantile(.90)) if adj.notna().any() else None,
            "max_abs_adjustment":float(adj.max()) if adj.notna().any() else None,
            "median_total_reliability":float(pd.to_numeric(exact.m91c_total_reliability,errors="coerce").median()) if "m91c_total_reliability" in exact else None,
        })
    transitions=df[df.m91c_team_changed.fillna(False).astype(bool)&df.position_model.astype(str).isin(OFFENSE)].copy()
    transition_by_pos=[]
    for pos,g in transitions.groupby("position_model"):
        transition_by_pos.append({
            "position_model":pos,
            "rows":int(len(g)),
            "exact_rows":int(g.m91c_exact_scoring_replay.fillna(False).astype(bool).sum()),
            "with_current_context":int(g.m91c_context_current_fields.fillna("").str.len().gt(0).sum()),
            "with_role_estimator":int(g.m91c_context_role_estimator_fields.fillna("").str.len().gt(0).sum()),
            "with_m8_environment":int(g.m91c_context_m8_environment_fields.fillna("").str.len().gt(0).sum()),
            "still_with_cleared_context":int(g.m91c_context_cleared_fields.fillna("").str.len().gt(0).sum()),
        })
    absadj=(pd.to_numeric(df.m91c_projection,errors="coerce")-pd.to_numeric(df.sleeper_market_projection,errors="coerce")).abs()
    top=df.assign(_absadj=absadj).sort_values("_absadj",ascending=False).head(30)
    top_cols=[
        "full_name","position_model","team","sleeper_market_projection","m91b_projection",
        "m91c_projection","m91c_delta_vs_sleeper","m91c_role_cohort","m91c_signal_z",
        "m91c_signal_extremity","m91c_total_reliability","m91c_correction_cap",
    ]
    payload={
        "research_build":RESEARCH_BUILD,
        "promotion_status":meta["status"],
        "per_position":rows,
        "role_cohort_counts":df[df.position_model.astype(str).isin(OFFENSE)].groupby(
            ["position_model","m91c_role_cohort"]
        ).size().reset_index(name="rows").to_dict("records"),
        "transition_context_coverage":transition_by_pos,
        "largest_applied_adjustments":[
            {k:(None if pd.isna(v) else v) for k,v in r.items()}
            for r in top[[c for c in top_cols if c in top]].to_dict("records")
        ],
    }
    path.write_text(json.dumps(json_safe(payload),indent=2,allow_nan=False,default=str)+"\n")


def parse_args(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--league-id",required=True);p.add_argument("--season",required=True,type=int)
    p.add_argument("--market-root",default="data/research/market/sleeper");p.add_argument("--market-snapshot",default="")
    p.add_argument("--availability-root",default="data/research/availability/sleeper");p.add_argument("--availability-snapshot",default="")
    p.add_argument("--profile-table",default="");p.add_argument("--player-week",default="")
    p.add_argument("--adp-key",default="adp_ppr");p.add_argument("--games",type=int,default=17)
    p.add_argument("--simulations",type=int,default=10000);p.add_argument("--seed",type=int,default=9413)
    p.add_argument("--active-probability",type=float,default=1.0);p.add_argument("--output-dir",default="")
    return p.parse_args(argv)


def main(argv=None):
    a=parse_args(argv)
    d=Path(a.output_dir) if a.output_dir else Path(f"data/research/leagues/{a.league_id}/performance/{a.season}/m91c_challenger")
    d.mkdir(parents=True,exist_ok=True)
    df,meta=build(a)
    df.to_csv(d/"m91c_season_board.csv",index=False)
    (d/"m91c_meta.json").write_text(json.dumps(json_safe(meta),indent=2,allow_nan=False,default=str)+"\n")
    write_summary(df,meta,d/"m91c_focus_summary.json")
    write_evaluation(df,meta,d/"m91c_evaluation.json")
    print(f"Wrote M9.1c rows={len(df)} exact={meta['exact_replay_rows']} transitions={meta['true_team_changes']} adjusted={meta['adjusted_rows']} gate={meta['residual_model_gate']['status']}")


if __name__=="__main__":main()
