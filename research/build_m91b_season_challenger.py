#!/usr/bin/env python3
"""FIE M9.1b: local-baseline residual + transition-context research challenger.

M9.1b is intentionally research-only. It keeps Sleeper as the external preseason
baseline and attempts to extract only FIE's *relative* football disagreement after
conditioning on comparable same-position Sleeper projections.

Key differences from M9.1:
- no global centering;
- no position-wide percentile transport;
- local same-position neighborhoods condition away level bias;
- the local FIE residual is converted to a zero-centered market-scale adjustment;
- adjustment is shrunk for limited local evidence and for empirically more volatile
  team transitions;
- team changes at QB/RB/WR/TE are rebuilt with current new-team context;
- common NFL team aliases (LA/LAR, JAC/JAX, WSH/WAS, etc.) cannot create fake moves;
- unresolved role context uses a current depth-order-matched *new-team* historical
  role template when available;
- derived M7 interaction features are recomputed after context replacement.

This file has no promotion or runtime-write path.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

import build_m91_season_challenger as m91
from build_m9_season_board import evaluate_position_spec
from fie_m7 import add_derived_driver_features

RESEARCH_BUILD = "M9.1b-LOCAL-RESIDUAL-TRANSITION-CONTEXT"
SCHEMA_VERSION = 1
OFFENSE = {"QB","RB","WR","TE"}
MIN_LOCAL_REFERENCE = 8
MAX_LOCAL_REFERENCE = 16

TEAM_ALIASES = {
    "LA":"LAR","STL":"LAR",
    "JAC":"JAX",
    "WSH":"WAS",
    "OAK":"LV",
    "SD":"LAC",
    "ARZ":"ARI",
    "BLT":"BAL",
    "CLV":"CLE",
    "HST":"HOU",
    "GNB":"GB",
    "KAN":"KC",
    "NWE":"NE",
    "NOR":"NO",
    "SFO":"SF",
    "TAM":"TB",
}

# Current projected raw fields. The first name is preferred; later names are
# explicit fallbacks. Receptions/receiving yards are used only as *share proxies*
# if Sleeper does not publish projected targets/air yards.
STAT_ALIASES = {
    "pass_att": ("pass_att","passing_att","passing_attempts"),
    "rush_att": ("rush_att","rushing_att","carries"),
    "rec_tgt": ("rec_tgt","targets","receiving_targets"),
    "rec": ("rec","receptions"),
    "air_yd": ("rec_air_yd","rec_air_yards","air_yd","air_yards"),
    "rec_yd": ("rec_yd","receiving_yards"),
    "rz_rush_att": ("rush_rz_att","rz_rush_att","red_zone_rush_att"),
    "inside5_rush_att": ("rush_att_inside_5","inside_5_rush_att","goal_line_rush_att"),
    "rz_tgt": ("rec_rz_tgt","rz_tgt","red_zone_targets"),
    "snap_share": ("offense_snap_share","off_snap_share","snap_share","snap_pct"),
}

ROLE_FEATURES = {
    "qb_pass_attempt_share_prior4","qb_rush_share_prior4",
    "inside_5_carry_share_prior4","snap_share_prior4","offense_snap_share_prior4",
    "carry_share_prior4","target_share_prior4","red_zone_carry_share_prior4",
    "red_zone_target_share_prior4","ngs_percent_share_of_intended_air_yards_prior4",
    "off_part_pass_plays_prior4","opportunity_change_score_prior1",
    "backfield_competition_index_prior4","backfield_competitor_count",
    "receiving_competition_index_prior4","receiving_competitor_count",
}
TEAM_ENV_FEATURES = {
    "team_pass_attempts_prior4_team","team_plays_prior4_team",
    "pfr_times_pressured_pct_prior4","pfr_times_sacked_prior4",
}
NO_ROLE_DONOR = {"opportunity_change_score_prior1"}


def num(x: Any) -> Optional[float]:
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None


def canonical_team(x: Any) -> str:
    t=str(x or "").strip().upper()
    return TEAM_ALIASES.get(t,t)


def stat_with_source(rec: dict, semantic: str) -> tuple[Optional[float], Optional[str]]:
    stats=(rec or {}).get("stats") or {}
    for key in STAT_ALIASES.get(semantic,()):
        x=num(stats.get(key))
        if x is not None:
            return x,key
    return None,None


def latest_availability(root: Path, season: int) -> Optional[Path]:
    d=root/str(season)
    files=sorted(d.glob("availability_*.jsonl.gz")) if d.is_dir() else []
    return files[-1] if files else None


def load_jsonl_gz(path: Optional[Path]) -> list[dict]:
    if path is None or not path.is_file():
        return []
    rows=[]
    with gzip.open(path,"rt",encoding="utf-8") as h:
        for line in h:
            line=line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def availability_index(rows: list[dict]) -> dict[str,dict]:
    return {str(r.get("sleeper_id") or ""):r for r in rows if r.get("sleeper_id")}


def build_enhanced_market_context(market: list[dict], games: int) -> tuple[dict,dict]:
    """Current-team role/environment context from Sleeper preseason components.

    Target share: projected targets when available, projected receptions otherwise.
    Air share: projected air yards when available, projected receiving yards otherwise.
    Fallbacks are explicitly recorded as proxies and never presented as raw targets.
    """
    team={}
    players={}
    for r in market:
        pos=str(r.get("position_model") or "").upper()
        tm=canonical_team(r.get("team"))
        cid=str(r.get("canonical_player_id") or "")
        if pos not in OFFENSE or not tm or not cid:
            continue

        pass_att, pass_src = stat_with_source(r,"pass_att")
        rush_att, rush_src = stat_with_source(r,"rush_att")
        tgt,tgt_src=stat_with_source(r,"rec_tgt")
        if tgt is None:
            tgt,tgt_src=stat_with_source(r,"rec")
            if tgt_src: tgt_src=f"proxy:{tgt_src}"
        air,air_src=stat_with_source(r,"air_yd")
        if air is None:
            air,air_src=stat_with_source(r,"rec_yd")
            if air_src: air_src=f"proxy:{air_src}"
        rzrush,rzrush_src=stat_with_source(r,"rz_rush_att")
        glrush,glrush_src=stat_with_source(r,"inside5_rush_att")
        rztgt,rztgt_src=stat_with_source(r,"rz_tgt")
        snap,snap_src=stat_with_source(r,"snap_share")

        p={
            "team":tm,"position":pos,
            "pass_att":pass_att,"rush_att":rush_att,"targets":tgt,"air_yards":air,
            "rz_rush_att":rzrush,"inside5_rush_att":glrush,"rz_targets":rztgt,
            "snap_share":snap,
            "sources":{
                "pass_att":pass_src,"rush_att":rush_src,"targets":tgt_src,"air_yards":air_src,
                "rz_rush_att":rzrush_src,"inside5_rush_att":glrush_src,"rz_targets":rztgt_src,
                "snap_share":snap_src,
            },
        }
        players[cid]=p
        z=team.setdefault(tm,{
            "pass_att":0.0,"rush_att":0.0,"targets":0.0,"air_yards":0.0,
            "rz_rush_att":0.0,"inside5_rush_att":0.0,"rz_targets":0.0,
            "receivers":0,"rb_rushers":0,
        })
        for key in ("pass_att","rush_att","targets","air_yards","rz_rush_att","inside5_rush_att","rz_targets"):
            if p.get(key) is not None:
                z[key]+=float(p[key])
        if pos in {"RB","WR","TE"} and (p.get("targets") or 0)>0:
            z["receivers"]+=1
        if pos=="RB" and (p.get("rush_att") or 0)>0:
            z["rb_rushers"]+=1

    out={}
    for cid,p in players.items():
        z=team[p["team"]]
        pos=p["position"]
        vals={}
        prov={}
        if z["pass_att"]>0:
            vals["team_pass_attempts_prior4_team"]=z["pass_att"]/max(1,games)
            prov["team_pass_attempts_prior4_team"]="current_team_market_total"
        if z["pass_att"]+z["rush_att"]>0:
            vals["team_plays_prior4_team"]=(z["pass_att"]+z["rush_att"])/max(1,games)
            prov["team_plays_prior4_team"]="current_team_market_total"
        if p.get("snap_share") is not None:
            snap=float(p["snap_share"])
            if snap>1.5: snap/=100.0
            vals["snap_share_prior4"]=snap
            vals["offense_snap_share_prior4"]=snap
            prov["snap_share_prior4"]=f"current_market:{p['sources'].get('snap_share')}"
            prov["offense_snap_share_prior4"]=f"current_market:{p['sources'].get('snap_share')}"
        if pos=="QB":
            if p.get("pass_att") is not None and z["pass_att"]>0:
                vals["qb_pass_attempt_share_prior4"]=float(p["pass_att"])/z["pass_att"]
                prov["qb_pass_attempt_share_prior4"]=f"current_market:{p['sources'].get('pass_att')}"
            if p.get("rush_att") is not None and z["rush_att"]>0:
                vals["qb_rush_share_prior4"]=float(p["rush_att"])/z["rush_att"]
                prov["qb_rush_share_prior4"]=f"current_market:{p['sources'].get('rush_att')}"
        teammates=[q for q in players.values() if q["team"]==p["team"]]
        if pos=="RB":
            if p.get("rush_att") is not None and z["rush_att"]>0:
                cs=float(p["rush_att"])/z["rush_att"]
                vals["carry_share_prior4"]=cs
                rb_shares=[
                    float(q["rush_att"])/z["rush_att"]
                    for q in teammates
                    if q["position"]=="RB" and q.get("rush_att") is not None
                ]
                vals["backfield_competition_index_prior4"]=max(0.0,sum(rb_shares)-cs)
                vals["backfield_competitor_count"]=float(max(
                    0,
                    sum(1 for share in rb_shares if share>=.15) - (1 if cs>=.15 else 0)
                ))
                prov["carry_share_prior4"]=f"current_market:{p['sources'].get('rush_att')}"
                prov["backfield_competition_index_prior4"]="sum_other_current_RB_carry_shares"
                prov["backfield_competitor_count"]="other_current_RBs_with_carry_share_gte_0.15"
        if pos in {"RB","WR","TE"}:
            if p.get("targets") is not None and z["targets"]>0:
                ts=float(p["targets"])/z["targets"]
                vals["target_share_prior4"]=ts
                recv_shares=[
                    float(q["targets"])/z["targets"]
                    for q in teammates
                    if q["position"] in {"RB","WR","TE"} and q.get("targets") is not None
                ]
                vals["receiving_competition_index_prior4"]=max(0.0,sum(recv_shares)-ts)
                vals["receiving_competitor_count"]=float(max(
                    0,
                    sum(1 for share in recv_shares if share>=.08) - (1 if ts>=.08 else 0)
                ))
                prov["target_share_prior4"]=f"current_market:{p['sources'].get('targets')}"
                prov["receiving_competition_index_prior4"]="sum_other_current_receiving_target_shares"
                prov["receiving_competitor_count"]="other_current_receivers_with_target_share_gte_0.08"
            if p.get("air_yards") is not None and z["air_yards"]>0:
                vals["ngs_percent_share_of_intended_air_yards_prior4"]=float(p["air_yards"])/z["air_yards"]
                prov["ngs_percent_share_of_intended_air_yards_prior4"]=f"current_market:{p['sources'].get('air_yards')}"
        if pos=="RB":
            if p.get("rz_rush_att") is not None and z["rz_rush_att"]>0:
                vals["red_zone_carry_share_prior4"]=float(p["rz_rush_att"])/z["rz_rush_att"]
                prov["red_zone_carry_share_prior4"]=f"current_market:{p['sources'].get('rz_rush_att')}"
            if p.get("inside5_rush_att") is not None and z["inside5_rush_att"]>0:
                vals["inside_5_carry_share_prior4"]=float(p["inside5_rush_att"])/z["inside5_rush_att"]
                prov["inside_5_carry_share_prior4"]=f"current_market:{p['sources'].get('inside5_rush_att')}"
        if pos in {"WR","TE","RB"}:
            if p.get("rz_targets") is not None and z["rz_targets"]>0:
                vals["red_zone_target_share_prior4"]=float(p["rz_targets"])/z["rz_targets"]
                prov["red_zone_target_share_prior4"]=f"current_market:{p['sources'].get('rz_targets')}"
        out[cid]={"values":{k:v for k,v in vals.items() if num(v) is not None},"provenance":prov}
    return out,team


def donor_rank_metric(row: pd.Series, pos: str) -> float:
    candidates=(
        ["offense_snap_share_prior4","carry_share_prior4","target_share_prior4"] if pos=="RB"
        else ["offense_snap_share_prior4","target_share_prior4"] if pos in {"WR","TE"}
        else ["snap_share_prior4","qb_pass_attempt_share_prior4"]
    )
    for c in candidates:
        if c in row.index:
            x=num(row.get(c))
            if x is not None:
                return x
    return -1e9


def depth_matched_role_donor(
    profiles: pd.DataFrame, *, team: str, pos: str, depth_order: Optional[int]
) -> Optional[dict]:
    if profiles.empty:
        return None
    team=canonical_team(team)
    z=profiles[
        profiles["position_model"].astype(str).str.upper().eq(pos)
        & profiles["profile_team"].map(canonical_team).eq(team)
    ].copy()
    if z.empty:
        return None
    z["_role_rank_metric"]=z.apply(lambda r:donor_rank_metric(r,pos),axis=1)
    z=z.sort_values("_role_rank_metric",ascending=False)
    idx=max(0,(int(depth_order)-1) if depth_order and int(depth_order)>0 else 0)
    idx=min(idx,len(z)-1)
    return z.iloc[idx].to_dict()


def team_environment_donor(profiles: pd.DataFrame, team: str, pos: str, feature: str) -> Optional[float]:
    if feature not in profiles.columns:
        return None
    z=profiles[
        profiles["position_model"].astype(str).str.upper().eq(pos)
        & profiles["profile_team"].map(canonical_team).eq(canonical_team(team))
    ]
    x=pd.to_numeric(z[feature],errors="coerce").dropna()
    return float(x.median()) if len(x) else None


CHANGE_METRICS={
    "QB":[("snap_share_prior4","snap_share"),("qb_rush_share_prior4","qb_rush_share")],
    "RB":[("offense_snap_share_prior4","offense_snap_share"),("carry_share_prior4","carry_share"),("target_share_prior4","target_share")],
    "WR":[("offense_snap_share_prior4","offense_snap_share"),("target_share_prior4","target_share")],
    "TE":[("offense_snap_share_prior4","offense_snap_share"),("target_share_prior4","target_share")],
}


def historical_change_scales(player_week: pd.DataFrame) -> dict:
    """Recreate M2's robust opportunity-change scale from completed weekly history."""
    out={}
    if player_week.empty:
        return out
    d=player_week.sort_values(["canonical_player_id","season","week"]).copy()
    for pos,pairs in CHANGE_METRICS.items():
        z=d[d.position_model.astype(str).str.upper().eq(pos)].copy()
        if z.empty: continue
        g=z.groupby(["canonical_player_id","season"],group_keys=False)
        out[pos]={}
        for _,raw in pairs:
            if raw not in z.columns: continue
            s=pd.to_numeric(z[raw],errors="coerce")
            recent=g[raw].transform(lambda q:pd.to_numeric(q,errors="coerce").rolling(3,min_periods=2).mean())
            base=g[raw].transform(lambda q:pd.to_numeric(q,errors="coerce").shift(3).rolling(5,min_periods=3).mean())
            delta=(recent-base).dropna()
            if len(delta)<50: continue
            med=float(delta.median())
            mad=float((delta-med).abs().median())
            scale=mad*1.4826 if mad>1e-6 else float(delta.std())
            if math.isfinite(scale) and scale>1e-6:
                out[pos][raw]={"median":med,"scale":float(scale),"n":int(len(delta))}
    return out


def transition_change_score(profile: dict, adapted: dict, pos: str, scales: dict) -> Optional[float]:
    zs=[]
    for feature,raw in CHANGE_METRICS.get(pos,[]):
        old=num(profile.get(feature)); cur=num(adapted.get(feature))
        sc=(scales.get(pos) or {}).get(raw)
        if old is None or cur is None or not sc:
            continue
        zs.append(((cur-old)-float(sc["median"]))/float(sc["scale"]))
    return max(zs) if zs else None


def required_features(spec: dict) -> set[str]:
    return {
        str(f)
        for t in (spec.get("targets") or [])
        for f in (t.get("features") or [])
    }


def adapt_transition_profile(
    profile: dict, *,
    cid: str, pos: str, current_team: str, spec: dict,
    context: dict, profiles: pd.DataFrame,
    availability: Optional[dict], change_scales: dict,
) -> tuple[dict,dict]:
    old=canonical_team(profile.get("profile_team"))
    cur=canonical_team(current_team)
    changed=bool(old and cur and old!=cur)
    if not changed:
        return dict(profile),{
            "team_changed":False,"status":"STABLE_TEAM",
            "current_context":[],"role_template":[],"team_environment":[],
            "cleared":[],"proxy_fields":[],"depth_order":None,
        }

    adapted=dict(profile)
    feats=required_features(spec)
    c=(context.get(cid) or {})
    current_vals=c.get("values") or {}
    current_prov=c.get("provenance") or {}
    depth=num((availability or {}).get("depth_chart_order"))
    depth_i=int(depth) if depth is not None and depth>=1 else None
    donor=depth_matched_role_donor(profiles,team=cur,pos=pos,depth_order=depth_i)
    audit={
        "team_changed":True,"status":"NEW_TEAM_CONTEXT_REBUILT_V2",
        "from_team":old,"to_team":cur,"depth_order":depth_i,
        "current_context":[],"role_template":[],"team_environment":[],
        "cleared":[],"proxy_fields":[],
    }

    for f in feats:
        if f in current_vals and num(current_vals[f]) is not None:
            adapted[f]=float(current_vals[f])
            audit["current_context"].append(f)
            if str(current_prov.get(f,"")).find("proxy:")>=0:
                audit["proxy_fields"].append(f)
            continue
        if f in TEAM_ENV_FEATURES:
            v=team_environment_donor(profiles,cur,pos,f)
            if v is not None:
                adapted[f]=v; audit["team_environment"].append(f); continue
        if f in ROLE_FEATURES and f not in NO_ROLE_DONOR and donor is not None:
            v=num(donor.get(f))
            if v is not None:
                adapted[f]=v; audit["role_template"].append(f); continue
        if f in ROLE_FEATURES or f in TEAM_ENV_FEATURES:
            adapted[f]=np.nan
            audit["cleared"].append(f)

    # Rebuild the change-score on its original robust-z scale when enough current
    # role components exist. Never carry the old team's change score.
    if "opportunity_change_score_prior1" in feats:
        score=transition_change_score(profile,adapted,pos,change_scales)
        if score is not None:
            adapted["opportunity_change_score_prior1"]=float(score)
            audit["current_context"].append("opportunity_change_score_prior1")
            audit["proxy_fields"].append("opportunity_change_score_prior1")
        else:
            adapted["opportunity_change_score_prior1"]=np.nan
            if "opportunity_change_score_prior1" not in audit["cleared"]:
                audit["cleared"].append("opportunity_change_score_prior1")

    adapted["profile_team"]=cur
    # Recompute interaction terms after changing their component features.
    one=add_derived_driver_features(pd.DataFrame([adapted]))
    adapted=one.iloc[0].to_dict()
    return adapted,audit


def local_baseline_residual_anchor(
    df: pd.DataFrame, *,
    min_reference: int=MIN_LOCAL_REFERENCE,
    max_reference: int=MAX_LOCAL_REFERENCE,
) -> tuple[pd.Series,pd.DataFrame]:
    """Sleeper + conservative local FIE residual correction.

    For each player:
      1. choose nearest same-position stable-team exact-replay players by Sleeper pts;
      2. robustly fit expected raw FIE given Sleeper inside that local neighborhood;
      3. calculate the player's FIE residual relative to that local expectation;
      4. convert residual percentile to a *zero-centered* local Sleeper point spread;
      5. shrink the adjustment by local sample reliability;
      6. for true team changes, additionally shrink by 1 / empirical transition
         volatility while the uncertainty interval is widened by that same volatility.

    Thus a player receiving an ordinary FIE result stays near Sleeper; a backup can
    never teleport into the starter distribution merely because raw FIE's level is
    biased for backups.
    """
    out=pd.Series(np.nan,index=df.index,dtype=float)
    audits=[]
    d=df.copy()
    d["_mkt"]=pd.to_numeric(d["sleeper_market_projection"],errors="coerce")
    d["_raw"]=pd.to_numeric(d["m91b_raw_fie_projection"],errors="coerce")
    exact=d["m91b_exact_scoring_replay"].fillna(False).astype(bool)
    changed=d["m91b_team_changed"].fillna(False).astype(bool)

    for pos,idx in d.groupby("position_model").groups.items():
        g=d.loc[list(idx)].copy()
        ref=g[
            exact.loc[g.index] & ~changed.loc[g.index]
            & g["_mkt"].notna() & g["_raw"].notna() & g["_mkt"].gt(0)
        ].copy()
        ref_kind="STABLE_TEAM_EXACT_REPLAY"
        if len(ref)<min_reference:
            ref=g[
                exact.loc[g.index] & g["_mkt"].notna() & g["_raw"].notna() & g["_mkt"].gt(0)
            ].copy()
            ref_kind="ALL_EXACT_REPLAY"
        if len(ref)<min_reference:
            audits.append({"position_model":pos,"status":"INSUFFICIENT_LOCAL_REFERENCE","reference_n":int(len(ref))})
            continue

        k=int(round(math.sqrt(len(ref))))
        k=max(min_reference,min(max_reference,k))
        for ridx,r in g[
            exact.loc[g.index] & g["_mkt"].notna() & g["_raw"].notna() & g["_mkt"].gt(0)
        ].iterrows():
            local=ref.assign(_distance=(ref["_mkt"]-float(r["_mkt"])).abs()).sort_values(
                ["_distance","_mkt"],ascending=[True,False]
            ).head(k)
            if len(local)<min_reference:
                continue
            X=local[["_mkt"]].to_numpy(float); y=local["_raw"].to_numpy(float)
            try:
                if local["_mkt"].nunique()<3:
                    raise ValueError("low local market variation")
                fit=HuberRegressor(epsilon=1.35,alpha=.5,max_iter=500).fit(X,y)
                expected_ref=fit.predict(X)
                expected=float(fit.predict([[float(r["_mkt"])]])[0])
                fit_method="HUBER_LOCAL"
            except Exception:
                offset=float(np.median(local["_raw"]-local["_mkt"]))
                expected_ref=local["_mkt"].to_numpy(float)+offset
                expected=float(r["_mkt"])+offset
                fit_method="MEDIAN_OFFSET_LOCAL"

            ref_resid=local["_raw"].to_numpy(float)-expected_ref
            residual=float(r["_raw"])-expected
            sr=np.sort(ref_resid); n=len(sr)
            left=np.searchsorted(sr,residual,side="left")
            right=np.searchsorted(sr,residual,side="right")
            q=float(np.clip(((left+right)/2.0+.5)/n,0.0,1.0))

            market_sorted=np.sort(local["_mkt"].to_numpy(float))
            qgrid=(np.arange(n,dtype=float)+.5)/n
            adjustment_distribution=market_sorted-float(np.median(market_sorted))
            raw_adjustment=float(np.interp(
                q,qgrid,adjustment_distribution,
                left=adjustment_distribution[0],right=adjustment_distribution[-1],
            ))

            # Equivalent-prior shrinkage: at the minimum acceptable local sample
            # (8), cross-sectional evidence receives 50% weight. This is deliberately
            # conservative until historical Sleeper residuals become available.
            local_reliability=float(n/(n+min_reference))
            transition_mult=max(1.0,float(r.get("m91b_uncertainty_spread_multiplier") or 1.0))
            transition_reliability=1.0/transition_mult if bool(r.get("m91b_team_changed")) else 1.0
            applied=raw_adjustment*local_reliability*transition_reliability
            projection=float(r["_mkt"])+applied
            out.loc[ridx]=projection

            d.loc[ridx,"m91b_local_expected_raw_fie"]=expected
            d.loc[ridx,"m91b_local_residual"]=residual
            d.loc[ridx,"m91b_local_residual_percentile"]=q
            d.loc[ridx,"m91b_local_reference_n"]=n
            d.loc[ridx,"m91b_local_fit_method"]=fit_method
            d.loc[ridx,"m91b_raw_market_scale_adjustment"]=raw_adjustment
            d.loc[ridx,"m91b_local_reliability"]=local_reliability
            d.loc[ridx,"m91b_transition_reliability"]=transition_reliability
            d.loc[ridx,"m91b_applied_adjustment"]=applied
            d.loc[ridx,"m91b_reference_kind"]=ref_kind

        audits.append({
            "position_model":pos,"status":"LOCAL_BASELINE_RESIDUAL_ANCHOR",
            "stable_reference_n":int(len(ref)),"adaptive_neighbor_n":k,
            "reference_kind":ref_kind,"minimum_reference":min_reference,
            "maximum_reference":max_reference,
        })

    # Copy audit columns created in local d back into caller df.
    for c in [c for c in d.columns if c.startswith("m91b_local_") or c in {
        "m91b_raw_market_scale_adjustment","m91b_transition_reliability",
        "m91b_applied_adjustment","m91b_reference_kind"
    }]:
        df[c]=d[c]
    return out,pd.DataFrame(audits)


def build(args) -> tuple[pd.DataFrame,dict]:
    # First run the successful M9.1 foundation in memory. We retain it for side-by-side
    # comparison but ignore its position-wide quantile projection as M9.1b's output.
    base,base_meta=m91.build(args)

    league_root=Path("data/research/leagues")/str(args.league_id)
    m1=m91.load_json(str(league_root/"milestone1.json"))
    m9_payload=m91.load_json(str(league_root/"milestone9.json"))
    scoring=(m1.get("scoring") or {}).get("settings",{})
    market_root=Path(args.market_root)
    market_path=Path(args.market_snapshot) if args.market_snapshot else m91.latest_market_snapshot(market_root,args.season)
    market=m91.load_market(str(market_path))
    market_by_cid=m91.build_market_record_index(market)
    enhanced_ctx,_=build_enhanced_market_context(market,args.games)

    player_week_path=Path(args.player_week) if args.player_week else Path(
        f".cache/fie-research/leagues/{args.league_id}/derived/player_week.csv.gz"
    )
    profiles,profile_path,profile_source=m91._profiles(
        m9_payload,
        override=args.profile_table,
        player_week_path=player_week_path,
        rehydrated_output=player_week_path.parent/"m9_preseason_latest_profiles_rehydrated.csv.gz",
    )
    by_pid={
        str(r["canonical_player_id"]):r
        for r in profiles.to_dict("records")
        if r.get("canonical_player_id") is not None
    }
    preseason=m9_payload.get("preseason_season_projection",{}) or {}
    specs=preseason.get("diagnostic_model_specs",{}) or preseason.get("model_specs",{}) or {}

    availability_path=Path(args.availability_snapshot) if args.availability_snapshot else latest_availability(
        Path(args.availability_root),args.season
    )
    avail_rows=load_jsonl_gz(availability_path)
    avail_by_sid=availability_index(avail_rows)

    pw=pd.read_csv(player_week_path,low_memory=False) if player_week_path.is_file() else pd.DataFrame()
    change_scales=historical_change_scales(pw)
    volatility=m91.transition_volatility(player_week_path)
    hist=m91.market_history_status(market_root,args.season)

    out=base.copy()
    # Initialize M9.1b fields from the fixed Sleeper baseline, never M9.1's projection.
    out["m91b_research_build"]=RESEARCH_BUILD
    out["m91b_projection"]=pd.to_numeric(out["sleeper_market_projection"],errors="coerce")
    out["m91b_raw_fie_projection"]=pd.to_numeric(out["m91_raw_fie_projection"],errors="coerce")
    out["m91b_exact_scoring_replay"]=out["m91_exact_scoring_replay"].fillna(False).astype(bool)
    out["m91b_team_changed"]=False
    out["m91b_team_transition_status"]="NO_PROFILE"
    out["m91b_context_current_fields"]=""
    out["m91b_context_role_template_fields"]=""
    out["m91b_context_team_environment_fields"]=""
    out["m91b_context_proxy_fields"]=""
    out["m91b_context_cleared_fields"]=""
    out["m91b_depth_chart_order"]=np.nan
    out["m91b_uncertainty_spread_multiplier"]=1.0
    out["m91b_status"]="BASELINE_ONLY"
    out["m91b_production_eligible"]=False

    for ridx,row in out.iterrows():
        pos=str(row.get("position_model") or "").upper()
        if pos not in OFFENSE: continue
        cid=str(row.get("canonical_player_id") or "")
        profile=by_pid.get(cid)
        market_pts=num(row.get("sleeper_market_projection"))
        if not profile or market_pts is None or not specs.get(pos):
            continue

        current_team=canonical_team(row.get("team"))
        profile_team=canonical_team(profile.get("profile_team"))
        changed=bool(current_team and profile_team and current_team!=profile_team)
        out.at[ridx,"m91b_team_changed"]=changed

        sid=str(row.get("sleeper_id") or "")
        avail=avail_by_sid.get(sid)
        spec=specs[pos]
        adapted,audit=adapt_transition_profile(
            profile,cid=cid,pos=pos,current_team=current_team,spec=spec,
            context=enhanced_ctx,profiles=profiles,availability=avail,
            change_scales=change_scales,
        )
        return_ctx=m91.sleeper_return_context(market_by_cid.get(cid,{}))
        ev=evaluate_position_spec(spec,adapted,scoring,pos,return_raw=return_ctx)
        exact=bool((ev.get("coverage") or {}).get("exact_linear_replay"))
        ppg=num(ev.get("ppg"))
        raw=ppg*args.games if exact and ppg is not None else None

        out.at[ridx,"m91b_raw_fie_projection"]=raw
        out.at[ridx,"m91b_exact_scoring_replay"]=exact
        out.at[ridx,"m91b_team_transition_status"]=audit.get("status")
        out.at[ridx,"m91b_context_current_fields"]="|".join(sorted(set(audit.get("current_context") or [])))
        out.at[ridx,"m91b_context_role_template_fields"]="|".join(sorted(set(audit.get("role_template") or [])))
        out.at[ridx,"m91b_context_team_environment_fields"]="|".join(sorted(set(audit.get("team_environment") or [])))
        out.at[ridx,"m91b_context_proxy_fields"]="|".join(sorted(set(audit.get("proxy_fields") or [])))
        out.at[ridx,"m91b_context_cleared_fields"]="|".join(sorted(set(audit.get("cleared") or [])))
        if audit.get("depth_order") is not None:
            out.at[ridx,"m91b_depth_chart_order"]=audit["depth_order"]

        mult=1.0
        if changed:
            mult=float((volatility.get(pos) or {}).get("spread_multiplier") or 1.0)
        out.at[ridx,"m91b_uncertainty_spread_multiplier"]=max(1.0,mult)
        if raw is not None:
            out.at[ridx,"m91b_status"]="RESEARCH_ONLY_TRANSITION_EXACT_REPLAY" if changed else "RESEARCH_ONLY_EXACT_REPLAY"
        else:
            out.at[ridx,"m91b_status"]="BASELINE_ONLY_DATA_OR_SCORING_GAP"

    anchored,calibration=local_baseline_residual_anchor(out)
    ok=anchored.notna()
    out.loc[ok,"m91b_projection"]=anchored.loc[ok]

    mkt=pd.to_numeric(out["sleeper_market_projection"],errors="coerce")
    proj=pd.to_numeric(out["m91b_projection"],errors="coerce")
    out["m91b_delta_vs_sleeper"]=proj-mkt
    out["m91b_delta_pct_vs_sleeper"]=np.where(mkt.abs()>1e-9,(proj-mkt)/mkt.abs()*100.0,np.nan)
    out["m91b_calibration_method"]=np.where(ok,"LOCAL_BASELINE_RESIDUAL_ANCHOR","BASELINE_ONLY")

    # Intervals: preserve M9's empirical position spread, widen true transitions,
    # recenter around the M9.1b point estimate.
    base_center=pd.to_numeric(out["fie_season_mean"],errors="coerce").where(
        pd.to_numeric(out["fie_season_mean"],errors="coerce").notna(),mkt
    )
    for qn in ("p10","p25","p50","p75","p90"):
        baseq=pd.to_numeric(out[qn],errors="coerce")
        spread=(baseq-base_center)*pd.to_numeric(out["m91b_uncertainty_spread_multiplier"],errors="coerce").fillna(1.0)
        out[f"m91b_{qn}"]=proj+spread

    out["m91b_position_rank"]=out.groupby("position_model")["m91b_projection"].rank(method="min",ascending=False)
    out["m91b_market_position_rank"]=out.groupby("position_model")["sleeper_market_projection"].rank(method="min",ascending=False)
    out["m91b_rank_delta_vs_market"]=out["m91b_market_position_rank"]-out["m91b_position_rank"]

    true_changes=int(out["m91b_team_changed"].fillna(False).astype(bool).sum())
    false_alias_fixed=int(
        out["team_changed"].fillna(False).astype(bool).sum()
        - true_changes
    )

    meta={
        "schema_version":SCHEMA_VERSION,
        "research_build":RESEARCH_BUILD,
        "league_id":str(args.league_id),"season":int(args.season),
        "status":"RESEARCH_ONLY_BLOCKED_PROMOTION",
        "production_eligible":False,"automatic_promotion":False,
        "sleeper_is_fixed_baseline":True,
        "adp_in_football_model":False,
        "calibration":{
            "method":"LOCAL_BASELINE_RESIDUAL_ANCHOR",
            "reference":"nearest same-position Sleeper baseline neighbors",
            "robust_fit":"Huber(raw_FIE ~ Sleeper) inside local neighborhood",
            "signal":"raw FIE minus locally expected raw FIE",
            "market_scale":"zero-centered local Sleeper projection distribution",
            "min_reference":MIN_LOCAL_REFERENCE,
            "max_reference":MAX_LOCAL_REFERENCE,
            "local_sample_shrinkage":"n/(n+min_reference)",
            "team_transition_mean_shrinkage":"1 / empirical transition volatility multiplier",
            "per_position":calibration.to_dict("records") if not calibration.empty else [],
        },
        "team_transition_policy":{
            "applies_to_positions":sorted(OFFENSE),
            "team_change_is_never_a_block_reason":True,
            "team_alias_normalization":TEAM_ALIASES,
            "old_team_context_carried":False,
            "priority":[
                "current new-team Sleeper projected components",
                "current Sleeper depth-order matched new-team historical role template",
                "new-team historical environment",
                "clear/impute only if no defensible new-team replacement exists",
            ],
            "interaction_features_recomputed_after_transition":True,
            "opportunity_change_score_rebuilt_on_historical_robust_scale":True,
        },
        "availability_snapshot":str(availability_path) if availability_path else None,
        "market_snapshot":str(market_path),
        "profile_table":str(profile_path),"profile_source":profile_source,
        "residual_model_gate":hist,
        "transition_volatility":volatility,
        "rows":int(len(out)),
        "exact_replay_rows":int(out["m91b_exact_scoring_replay"].fillna(False).astype(bool).sum()),
        "true_team_changes":true_changes,
        "team_alias_false_changes_fixed":false_alias_fixed,
        "notes":[
            "M9 and M9.1 remain untouched; M9.1b is side-by-side research only.",
            "Current-year calibration cannot establish positive alpha without historical Sleeper preseason baselines.",
            "Historical Actual-minus-Sleeper residual validation remains the promotion gate.",
        ],
    }
    return out,meta


FOCUS=[
    "Lamar Jackson","Kyler Murray","Malik Willis","Jaylen Waddle","David Montgomery",
    "Carson Wentz","Cam Ward","Geno Smith","Justin Fields",
]


def summary(df:pd.DataFrame,meta:dict,path:Path)->None:
    q=df[df["full_name"].astype(str).isin(FOCUS)].copy()
    cols=[
        "full_name","position_model","team","profile_team","team_changed","m91b_team_changed",
        "sleeper_market_projection","m91_projection","m91b_raw_fie_projection",
        "m91b_local_expected_raw_fie","m91b_local_residual","m91b_local_residual_percentile",
        "m91b_raw_market_scale_adjustment","m91b_local_reliability","m91b_transition_reliability",
        "m91b_applied_adjustment","m91b_projection","m91b_delta_vs_sleeper",
        "m91b_market_position_rank","m91b_position_rank","m91b_rank_delta_vs_market",
        "m91b_team_transition_status","m91b_depth_chart_order",
        "m91b_context_current_fields","m91b_context_role_template_fields",
        "m91b_context_team_environment_fields","m91b_context_proxy_fields",
        "m91b_context_cleared_fields","m91b_uncertainty_spread_multiplier",
    ]
    players=[]
    for r in q[[c for c in cols if c in q.columns]].to_dict("records"):
        players.append({k:(None if pd.isna(v) else v) for k,v in r.items()})
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({**meta,"focus_players":players},indent=2,allow_nan=False,default=str)+"\n")


def parse_args(argv=None):
    p=argparse.ArgumentParser(description="Build FIE M9.1b local residual research challenger")
    p.add_argument("--league-id",required=True)
    p.add_argument("--season",required=True,type=int)
    p.add_argument("--market-root",default="data/research/market/sleeper")
    p.add_argument("--market-snapshot",default="")
    p.add_argument("--availability-root",default="data/research/availability/sleeper")
    p.add_argument("--availability-snapshot",default="")
    p.add_argument("--profile-table",default="")
    p.add_argument("--player-week",default="")
    p.add_argument("--adp-key",default="adp_ppr")
    p.add_argument("--games",type=int,default=17)
    p.add_argument("--simulations",type=int,default=10000)
    p.add_argument("--seed",type=int,default=9412)
    p.add_argument("--active-probability",type=float,default=1.0)
    p.add_argument("--output-dir",default="")
    return p.parse_args(argv)


def main(argv=None):
    a=parse_args(argv)
    d=Path(a.output_dir) if a.output_dir else Path(
        f"data/research/leagues/{a.league_id}/performance/{a.season}/m91b_challenger"
    )
    d.mkdir(parents=True,exist_ok=True)
    df,meta=build(a)
    df.to_csv(d/"m91b_season_board.csv",index=False)
    (d/"m91b_meta.json").write_text(json.dumps(meta,indent=2,allow_nan=False,default=str)+"\n")
    summary(df,meta,d/"m91b_focus_summary.json")
    print(
        f"Wrote M9.1b rows={len(df)} exact={meta['exact_replay_rows']} "
        f"true_transitions={meta['true_team_changes']} alias_fixes={meta['team_alias_false_changes_fixed']} "
        f"residual_gate={meta['residual_model_gate']['status']}"
    )


if __name__=="__main__":
    main()
