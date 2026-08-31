#!/usr/bin/env python3
"""Integrate M9.1c into unified FIE research outputs without touching production math.

This is an evidence/report bridge only.

Hard invariants:
- M9 remains the selected production preseason model.
- canonical projection_points / VORP / ranks / replacement / actionability do not change.
- V9.7 validation challenger evidence remains intact.
- M9.1c is exposed separately as the official *preseason projection challenger*.
- historical Actual-minus-Sleeper residual validation remains the promotion gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fie_research_pipeline_contract import (
    ROOT, league_root, load_json, pipeline_dir, sha256_file, utc_now, write_json,
)

OFFENSE={"QB","RB","WR","TE"}
CANONICAL_LOCKED_COLUMNS=(
    "projection_points","projection_ppg","p10","p25","p50","p75","p90",
    "position_rank","overall_rank","replacement_points","vorp",
    "market_position_rank","market_overall_rank",
    "rank_edge_position","rank_edge_overall","value_label",
    "actionable_signal","model_selected","model_status","projection_source",
    "projection_basis","interval_source",
)
M91C_PREFIX="preseason_challenger_"


def finite(v:Any)->float|None:
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def norm_id(v:Any)->str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    s=str(v).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s=s[:-2]
    return "" if s.lower() in {"","nan","none","null","<na>"} else s


def join_key(row:dict)->str:
    cid=norm_id(row.get("canonical_player_id"))
    sid=norm_id(row.get("sleeper_id"))
    pid=norm_id(row.get("player_id"))
    return f"c:{cid}" if cid else (f"s:{sid}" if sid else (f"p:{pid}" if pid else ""))


def json_safe(v:Any)->Any:
    if isinstance(v,dict):
        return {str(k):json_safe(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,set)):
        return [json_safe(x) for x in v]
    if isinstance(v,np.generic):
        return json_safe(v.item())
    if isinstance(v,float):
        return v if math.isfinite(v) else None
    if v is pd.NA:
        return None
    try:
        if bool(pd.isna(v)):
            return None
    except Exception:
        pass
    return v


def stable_frame_hash(df:pd.DataFrame, columns:tuple[str,...])->str:
    cols=[c for c in columns if c in df.columns]
    keycols=[c for c in ("canonical_player_id","sleeper_id","player_id","position","name") if c in df.columns]
    use=[]
    for c in keycols+cols:
        if c not in use:
            use.append(c)
    x=df[use].copy()
    for c in x.columns:
        x[c]=x[c].map(lambda v:None if pd.isna(v) else v)
    rows=x.to_dict("records")
    rows.sort(key=lambda r:(
        str(r.get("canonical_player_id") or ""),
        str(r.get("sleeper_id") or ""),
        str(r.get("player_id") or ""),
        str(r.get("position") or ""),
        str(r.get("name") or ""),
    ))
    raw=(json.dumps(json_safe(rows),sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
    return hashlib.sha256(raw).hexdigest()


def load_m91c(league_id:str,season:int)->tuple[pd.DataFrame,dict,dict]:
    d=league_root(league_id)/"performance"/str(season)/"m91c_challenger"
    board=d/"m91c_season_board.csv"
    meta=d/"m91c_meta.json"
    evaluation=d/"m91c_evaluation.json"
    if not (board.is_file() and meta.is_file() and evaluation.is_file()):
        raise RuntimeError("M9.1c board/meta/evaluation missing")
    b=pd.read_csv(board,low_memory=False)
    m=load_json(meta,{})
    e=load_json(evaluation,{})
    if m.get("research_build")!="M9.1c-ROLE-COHORT-DENSITY-RELIABILITY":
        raise RuntimeError("unexpected M9.1c research_build")
    if m.get("production_eligible") is not False or m.get("automatic_promotion") is not False:
        raise RuntimeError("M9.1c governance contract violated")
    if m.get("sleeper_is_fixed_baseline") is not True:
        raise RuntimeError("M9.1c Sleeper baseline contract violated")
    return b,m,e


def challenger_map(m91c:pd.DataFrame,gate_status:str)->dict[str,dict]:
    out={}
    for r in m91c.to_dict("records"):
        key=join_key(r)
        if not key:
            continue
        proj=finite(r.get("m91c_projection"))
        market=finite(r.get("sleeper_market_projection"))
        out[key]={
            f"{M91C_PREFIX}model":"M9.1c",
            f"{M91C_PREFIX}projection":proj,
            f"{M91C_PREFIX}delta_vs_sleeper":finite(r.get("m91c_delta_vs_sleeper")),
            f"{M91C_PREFIX}raw_fie_projection":finite(r.get("m91c_raw_fie_projection")),
            f"{M91C_PREFIX}signal_z":finite(r.get("m91c_signal_z")),
            f"{M91C_PREFIX}signal_percentile":finite(r.get("m91c_signal_percentile")),
            f"{M91C_PREFIX}signal_extremity":finite(r.get("m91c_signal_extremity")),
            f"{M91C_PREFIX}reliability":finite(r.get("m91c_total_reliability")),
            f"{M91C_PREFIX}correction_cap":finite(r.get("m91c_correction_cap")),
            f"{M91C_PREFIX}role_cohort":r.get("m91c_role_cohort"),
            f"{M91C_PREFIX}status":r.get("m91c_status"),
            f"{M91C_PREFIX}exact_scoring":bool(r.get("m91c_exact_scoring_replay")),
            f"{M91C_PREFIX}team_changed":bool(r.get("m91c_team_changed")),
            f"{M91C_PREFIX}transition_status":r.get("m91c_team_transition_status"),
            f"{M91C_PREFIX}gate_status":gate_status,
            f"{M91C_PREFIX}applied":(
                proj is not None and market is not None and abs(proj-market)>1e-9
            ),
        }
    return out


def enrich_board(path:Path,cmap:dict[str,dict])->dict:
    df=pd.read_csv(path,low_memory=False)
    before=stable_frame_hash(df,CANONICAL_LOCKED_COLUMNS)
    matched=0
    for i,r in df.iterrows():
        if str(r.get("position") or "").upper() not in OFFENSE:
            continue
        ch=cmap.get(join_key(r.to_dict()))
        if not ch:
            continue
        matched+=1
        for k,v in ch.items():
            df.at[i,k]=v
    after=stable_frame_hash(df,CANONICAL_LOCKED_COLUMNS)
    if before!=after:
        raise RuntimeError("canonical final-board production columns changed during M9.1c integration")
    df.to_csv(path,index=False)
    return {
        "rows":int(len(df)),
        "matched_offense_rows":matched,
        "canonical_locked_hash_before":before,
        "canonical_locked_hash_after":after,
    }


def readiness_position_payload(pos:str,meta:dict,evaluation:dict)->dict:
    per={str(x.get("position_model")):x for x in evaluation.get("per_position",[]) if isinstance(x,dict)}
    p=per.get(pos,{})
    gate=meta.get("residual_model_gate") or {}
    return {
        "model":"M9.1c",
        "role":"OFFICIAL_PRESEASON_PROJECTION_CHALLENGER",
        "status":meta.get("status"),
        "production_eligible":False,
        "automatic_promotion":False,
        "historical_residual_gate_status":gate.get("status"),
        "historical_residual_gate_semantics":gate.get("semantics"),
        "exact_rows":p.get("exact_rows"),
        "adjusted_rows":p.get("adjusted_rows"),
        "median_abs_adjustment":p.get("median_abs_adjustment"),
        "p90_abs_adjustment":p.get("p90_abs_adjustment"),
        "max_abs_adjustment":p.get("max_abs_adjustment"),
        "median_total_reliability":p.get("median_total_reliability"),
        "spearman_vs_sleeper":p.get("spearman_m91c_vs_sleeper"),
    }


def enrich_readiness(path:Path,meta:dict,evaluation:dict)->dict:
    obj=load_json(path,{})
    positions=obj.get("positions") or {}
    prior={}
    for pos in OFFENSE:
        p=positions.get(pos) or {}
        prior[pos]=p.get("best_research_challenger")
        # Preserve V9.7 model-validation challenger semantics separately.
        p["model_validation_challenger"]=p.get("best_research_challenger")
        p["official_preseason_projection_challenger"]="M9.1c"
        p["preseason_projection_challenger"]=readiness_position_payload(pos,meta,evaluation)
        positions[pos]=p
    obj["positions"]=positions
    obj.setdefault("governance",{})["m91c_production_activation"]=False
    obj["governance"]["m91c_historical_residual_gate_required"]=True
    obj["preseason_projection_challenger"]={
        "model":"M9.1c",
        "status":meta.get("status"),
        "production_eligible":False,
        "automatic_promotion":False,
        "residual_model_gate":meta.get("residual_model_gate"),
        "team_transition_policy":meta.get("team_transition_policy"),
        "transition_volatility":meta.get("transition_volatility"),
    }
    write_json(path,obj)
    return {"prior_model_validation_challenger":prior}


def row_challenger(r:dict)->dict|None:
    model=r.get(f"{M91C_PREFIX}model")
    if not model:
        return None
    return {
        "model":model,
        "projection":finite(r.get(f"{M91C_PREFIX}projection")),
        "delta_vs_sleeper":finite(r.get(f"{M91C_PREFIX}delta_vs_sleeper")),
        "raw_fie_projection":finite(r.get(f"{M91C_PREFIX}raw_fie_projection")),
        "signal_z":finite(r.get(f"{M91C_PREFIX}signal_z")),
        "signal_percentile":finite(r.get(f"{M91C_PREFIX}signal_percentile")),
        "signal_extremity":finite(r.get(f"{M91C_PREFIX}signal_extremity")),
        "reliability":finite(r.get(f"{M91C_PREFIX}reliability")),
        "correction_cap":finite(r.get(f"{M91C_PREFIX}correction_cap")),
        "role_cohort":r.get(f"{M91C_PREFIX}role_cohort"),
        "status":r.get(f"{M91C_PREFIX}status"),
        "exact_scoring":bool(r.get(f"{M91C_PREFIX}exact_scoring")),
        "team_changed":bool(r.get(f"{M91C_PREFIX}team_changed")),
        "transition_status":r.get(f"{M91C_PREFIX}transition_status"),
        "historical_residual_gate_status":r.get(f"{M91C_PREFIX}gate_status"),
    }


def enrich_nested_player_rows(obj:Any,cmap:dict[str,dict])->int:
    count=0
    if isinstance(obj,list):
        for x in obj:
            count+=enrich_nested_player_rows(x,cmap)
        return count
    if not isinstance(obj,dict):
        return 0
    key=join_key(obj)
    if key and key in cmap and str(obj.get("position") or "").upper() in OFFENSE:
        tmp=dict(obj)
        tmp.update(cmap[key])
        obj["preseason_projection_challenger"]=row_challenger(tmp)
        count+=1
    for v in obj.values():
        count+=enrich_nested_player_rows(v,cmap)
    return count


def top_signal_rows(cmap:dict[str,dict],board:pd.DataFrame,n:int=10)->tuple[list[dict],list[dict]]:
    rows=[]
    for r in board.to_dict("records"):
        if str(r.get("position") or "").upper() not in OFFENSE:
            continue
        ch=cmap.get(join_key(r))
        if not ch:
            continue
        d=finite(ch.get(f"{M91C_PREFIX}delta_vs_sleeper"))
        if d is None:
            continue
        rows.append({
            "name":r.get("name"),"team":r.get("team"),"position":r.get("position"),
            "sleeper_projection":finite(r.get("projection_points")) if str(r.get("projection_basis"))=="MARKET_BASE" else None,
            "m91c_projection":ch.get(f"{M91C_PREFIX}projection"),
            "delta_vs_sleeper":d,
            "signal_z":ch.get(f"{M91C_PREFIX}signal_z"),
            "reliability":ch.get(f"{M91C_PREFIX}reliability"),
            "role_cohort":ch.get(f"{M91C_PREFIX}role_cohort"),
            "team_changed":ch.get(f"{M91C_PREFIX}team_changed"),
        })
    pos=sorted([x for x in rows if x["delta_vs_sleeper"]>0],key=lambda x:-x["delta_vs_sleeper"])[:n]
    neg=sorted([x for x in rows if x["delta_vs_sleeper"]<0],key=lambda x:x["delta_vs_sleeper"])[:n]
    return pos,neg


def md_table(rows:list[dict])->str:
    out=["| Player | Pos | Team | M9.1c Δ vs Sleeper | Signal z | Reliability | Cohort |",
         "|---|---|---|---:|---:|---:|---|"]
    for r in rows:
        def f(x,d=1):
            return "—" if x is None else f"{float(x):.{d}f}".rstrip("0").rstrip(".")
        out.append(
            f"| {r.get('name') or '—'} | {r.get('position') or '—'} | {r.get('team') or '—'} | "
            f"{f(r.get('delta_vs_sleeper'))} | {f(r.get('signal_z'),2)} | "
            f"{f(r.get('reliability'),2)} | {r.get('role_cohort') or '—'} |"
        )
    return "\n".join(out)


def enrich_reports(out:Path,cmap:dict[str,dict],meta:dict,evaluation:dict,board:pd.DataFrame)->dict:
    report_path=out/"league-report.json"
    summary_path=out/"report-summary.json"
    md_path=out/"league-report.md"
    report=load_json(report_path,{})
    summary=load_json(summary_path,{})
    rc=enrich_nested_player_rows(report,cmap)
    sc=enrich_nested_player_rows(summary,cmap)

    challenger={
        "model":"M9.1c",
        "role":"OFFICIAL_PRESEASON_PROJECTION_CHALLENGER",
        "status":meta.get("status"),
        "production_eligible":False,
        "automatic_promotion":False,
        "residual_model_gate":meta.get("residual_model_gate"),
        "per_position":evaluation.get("per_position"),
        "role_cohort_counts":evaluation.get("role_cohort_counts"),
        "transition_context_coverage":evaluation.get("transition_context_coverage"),
    }
    report["preseason_projection_challenger"]=challenger
    summary["preseason_projection_challenger"]=challenger

    pos,neg=top_signal_rows(cmap,board)
    report["m91c_largest_positive_adjustments"]=pos
    report["m91c_largest_negative_adjustments"]=neg
    summary["m91c_largest_positive_adjustments"]=pos[:5]
    summary["m91c_largest_negative_adjustments"]=neg[:5]

    write_json(report_path,report)
    write_json(summary_path,summary)

    existing=md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    marker="## M9.1c Preseason Projection Challenger"
    base=existing.split(marker)[0].rstrip()
    appendix=(
        f"\n\n{marker}\n\n"
        "M9 remains the governed production preseason model. M9.1c is research-only "
        "and changes no canonical VORP, replacement, ranking, or actionability field. "
        "Its current promotion gate remains the historical Actual-minus-Sleeper preseason residual test.\n\n"
        "### Largest positive M9.1c adjustments\n\n"
        f"{md_table(pos)}\n\n"
        "### Largest negative M9.1c adjustments\n\n"
        f"{md_table(neg)}\n"
    )
    md_path.write_text(base+appendix,encoding="utf-8")
    return {"report_player_rows_enriched":rc,"summary_player_rows_enriched":sc}


def enrich_board_meta(path:Path,meta:dict,evaluation:dict)->None:
    obj=load_json(path,{})
    obj["preseason_projection_challenger"]={
        "model":"M9.1c",
        "status":meta.get("status"),
        "production_eligible":False,
        "automatic_promotion":False,
        "residual_model_gate":meta.get("residual_model_gate"),
        "evaluation_file":"../m91c_challenger/m91c_evaluation.json",
    }
    write_json(path,obj)


def main(argv=None)->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--league-id",required=True)
    ap.add_argument("--season",type=int,required=True)
    ap.add_argument("--output-dir",default="")
    a=ap.parse_args(argv)

    out=Path(a.output_dir) if a.output_dir else pipeline_dir(a.league_id,a.season)
    readiness=out/"readiness.json"
    board_path=out/"final_player_board.csv"
    board_meta=out/"board-meta.json"
    for p in (readiness,board_path,out/"league-report.json",out/"report-summary.json"):
        if not p.is_file():
            raise RuntimeError(f"unified pipeline artifact missing: {p}")

    m91c,meta,evaluation=load_m91c(a.league_id,a.season)
    gate_status=str((meta.get("residual_model_gate") or {}).get("status") or "UNKNOWN")
    cmap=challenger_map(m91c,gate_status)

    before_sha=sha256_file(board_path)
    board_result=enrich_board(board_path,cmap)
    integrated_board=pd.read_csv(board_path,low_memory=False)
    ready_result=enrich_readiness(readiness,meta,evaluation)
    report_result=enrich_reports(out,cmap,meta,evaluation,integrated_board)
    if board_meta.is_file():
        enrich_board_meta(board_meta,meta,evaluation)

    audit={
        "schema":"fie-m91c-unified-integration-v1",
        "league_id":str(a.league_id),
        "season":int(a.season),
        "generated_at":utc_now(),
        "status":"complete_research_only",
        "official_preseason_projection_challenger":"M9.1c",
        "production_model_unchanged":"M9",
        "production_activation":False,
        "historical_residual_gate_status":gate_status,
        "m91c_source":{
            "meta":str(league_root(a.league_id)/"performance"/str(a.season)/"m91c_challenger"/"m91c_meta.json"),
            "evaluation":str(league_root(a.league_id)/"performance"/str(a.season)/"m91c_challenger"/"m91c_evaluation.json"),
        },
        "board_before_file_sha256":before_sha,
        "board_after_file_sha256":sha256_file(board_path),
        **board_result,
        **ready_result,
        **report_result,
        "canonical_production_columns_unchanged":(
            board_result["canonical_locked_hash_before"]==
            board_result["canonical_locked_hash_after"]
        ),
    }
    if not audit["canonical_production_columns_unchanged"]:
        raise RuntimeError("production board invariant failed")
    write_json(out/"m91c-integration.json",audit)

    # Extension metadata rather than a new core stage: existing stage contract and
    # validators remain backward compatible during the integration pilot.
    manifest_path=out/"stage-manifest.json"
    if manifest_path.is_file():
        manifest=load_json(manifest_path,{})
        manifest.setdefault("extensions",{})["m91c_preseason_projection_challenger"]={
            "status":"complete_research_only",
            "model":"M9.1c",
            "production_activation":False,
            "historical_residual_gate_status":gate_status,
            "integration_audit_sha256":sha256_file(out/"m91c-integration.json"),
        }
        write_json(manifest_path,manifest)

    print(json.dumps({
        "league_id":a.league_id,
        "season":a.season,
        "status":"complete_research_only",
        "official_preseason_projection_challenger":"M9.1c",
        "production_model":"M9",
        "matched_offense_rows":board_result["matched_offense_rows"],
        "canonical_production_columns_unchanged":True,
        "historical_residual_gate_status":gate_status,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
