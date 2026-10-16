#!/usr/bin/env python3
"""Orchestrate the V9.7.3-V10.4.2 FIE strategy research stack for one league."""
from __future__ import annotations
import argparse, hashlib, json, math, os
from pathlib import Path
import numpy as np
import pandas as pd

from fie_strategy_stack import (
    market_movement, adp_outcome_curves, build_league_value_board, draft_actions,
    actionable_findings, injury_redistribution, market_mistake_research, strategy_summary, verified_market_panel,
)
from preseason_projection_v2 import validate_component_preseason, build_v972_shadow_season_board
from preseason_projection_v3 import validate_preseason_head_to_head
from current_snapshot_storage import load_current_snapshot


def load_json(path):
    p=Path(path); return json.loads(p.read_text()) if p.is_file() else {}


def json_safe(value):
    """Convert pandas/numpy missing values to strict JSON null at artifact boundaries.

    This is serialization-only. It does not impute model inputs, change predictions,
    alter evidence gates, or reinterpret missing football/market information as zero.
    """
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return [json_safe(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        value = value.item()
    if value is pd.NA:
        return None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        missing = pd.isna(value)
        if isinstance(missing, (bool, np.bool_)) and bool(missing):
            return None
    except Exception:
        pass
    return value


def write_strict_json(path, obj):
    Path(path).write_text(
        json.dumps(json_safe(obj), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def scoring_from_m1(m1):
    return (m1.get("scoring") or {}).get("settings") or m1.get("scoring_settings") or {}


def verified_index(path: str):
    if not path or not Path(path).is_file(): return {}
    return load_json(path).get("verified_preseason_snapshots") or load_json(path)



def resolve_adp_key(profile: dict, requested: str) -> tuple[str, str]:
    """Choose the Sleeper ADP market from the existing league profile.

    AUTO is preferred so a dynasty/Superflex league cannot silently be compared
    with a redraft 1QB market.  An explicit override remains available for research
    comparisons and is recorded in provenance.
    """
    fmt=str(profile.get("format") or (profile.get("league") or {}).get("format") or "").upper()
    scoring=(profile.get("scoring_settings") or profile.get("scoring") or
             (profile.get("league") or {}).get("scoring_settings") or {})
    roster=(profile.get("roster_positions") or (profile.get("league") or {}).get("roster_positions") or [])
    sf=("SUPER_FLEX" in roster) or sum(1 for x in roster if str(x).upper()=="QB")>=2
    try: rec=float(scoring.get("rec",0) or 0)
    except Exception: rec=0.0
    dynasty="DYNASTY" in fmt
    if dynasty and sf: expected="adp_dynasty_2qb"
    elif dynasty and rec>=.75: expected="adp_dynasty_ppr"
    elif dynasty and rec>=.25: expected="adp_dynasty_half_ppr"
    elif dynasty: expected="adp_dynasty_std"
    elif sf: expected="adp_2qb"
    elif rec>=.75: expected="adp_ppr"
    elif rec>=.25: expected="adp_half_ppr"
    else: expected="adp_std"
    req=str(requested or "AUTO").strip()
    return (expected if req.upper()=="AUTO" else req), expected


def sha256_file(path: Path) -> str | None:
    if not path.is_file(): return None
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--league-root",required=True); p.add_argument("--season",type=int,required=True)
    p.add_argument("--derived-dir",required=True); p.add_argument("--market-root",default="data/research/market/sleeper")
    p.add_argument("--adp-key",default="AUTO"); p.add_argument("--output-dir",required=True)
    p.add_argument("--verified-market-index",default=""); p.add_argument("--current-pick",type=int,default=None)
    p.add_argument("--next-pick",type=int,default=None)
    a=p.parse_args(argv)
    root=Path(a.league_root); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    m1=load_json(root/"milestone1.json"); profile=load_json(root/"profile.json")
    if not profile:
        profile=load_json(root/"league_profile.json")
    board_path=root/"performance"/str(a.season)/"season_board.csv"
    current_path=root/"current"/"milestone5_current.json"
    pw_path=Path(a.derived_dir)/"player_week.csv.gz"; ident_path=Path(a.derived_dir)/"player_identity.csv.gz"
    if not board_path.is_file(): raise RuntimeError(f"Existing M9 season board required: {board_path}")
    if not pw_path.is_file(): raise RuntimeError(f"Existing M1 derived player_week required: {pw_path}")
    board=pd.read_csv(board_path,low_memory=False); pw=pd.read_csv(pw_path,low_memory=False)
    identity=pd.read_csv(ident_path,low_memory=False) if ident_path.is_file() else pd.DataFrame()
    adp_key, expected_adp_key=resolve_adp_key(profile,a.adp_key)

    # A: component-first preseason challenger. Never feeds ADP.
    scoring=scoring_from_m1(m1)
    pv2=validate_component_preseason(pw,scoring,identity)
    write_strict_json(out/"preseason_v2.json", pv2)

    # A3: V9.7.3 head-to-head/calibration gate.  Compare V9.7.2 and M9 football
    # models on identical chronological player-season holdouts. Historical market
    # fallback remains explicitly blocked unless immutable verified snapshots exist.
    v973,v973_predictions,v973_calibration=validate_preseason_head_to_head(
        pw,scoring,identity,v972_result=pv2
    )
    write_strict_json(out/"preseason_v973_validation.json",v973)
    v973_predictions.to_csv(out/"preseason_v973_predictions.csv",index=False)
    v973_calibration.to_csv(out/"preseason_v973_calibration.csv",index=False)

    # A2/current shadow: validated-candidate 2026 projection.  QB/WR may replace the
    # strategy input only inside this research output; V9.7.3 remains evaluation-only
    # in this release and does not alter the existing V9.7.2 strategy handoff.
    current=load_current_snapshot(current_path) if current_path.is_file() else {}
    shadow_board,shadow_meta=build_v972_shadow_season_board(
        pw,scoring,pv2,board,a.season,identity=identity,current=current
    )
    shadow_board.to_csv(out/"season_projection_v972.csv",index=False)

    # B: market evidence. Daily trend is prospective; historical curves need a verified index.
    movement,mmeta=market_movement(a.market_root,a.season,adp_key)
    movement.to_csv(out/"market_movement.csv",index=False)
    vindex=verified_index(a.verified_market_index)
    curves,cmeta=adp_outcome_curves(a.market_root,pw,adp_key,vindex)
    curves.to_csv(out/"adp_outcome_curves.csv",index=False)

    # C/E: league value and price-aware draft decisions. Current player identity/status
    # is a required relevance boundary so historical/deep catalog rows cannot become
    # actionable merely because their ADP is even deeper. The explicit V9.7.2 shadow
    # column is consumed here; original M9 fields remain side-by-side in the CSV.
    value,vmeta=build_league_value_board(shadow_board,profile,movement,curves,current=current)
    value.to_csv(out/"league_value_board.csv",index=False)
    draft=draft_actions(value,a.current_pick,a.next_pick); draft.to_csv(out/"draft_actions.csv",index=False)

    # F/G/H: current action consumers; blocked cleanly when current/V9.6 data are absent.
    injury=injury_redistribution(current) if current else {"status":"current_snapshot_unavailable","rows":[],"production_activation":False}
    write_strict_json(out/"injury_opportunity.json", injury)
    findings=actionable_findings(value,current)
    write_strict_json(out/"actionable_findings.json", findings)

    hist_panel=verified_market_panel(a.market_root,pw,adp_key,vindex)
    mistakes=market_mistake_research(curves,hist_panel)
    write_strict_json(out/"market_mistake_research.json", mistakes)
    summary=strategy_summary(value,mmeta,cmeta,pv2)
    summary["build"]="V10.4.3-STRATEGY-V973-VALIDATION-1"
    summary["phases"]["A2_v972_shadow_projection"]=shadow_meta.get("status")
    summary["phases"]["A3_v973_head_to_head_calibration"]=v973.get("status")
    summary["season_projection_v972_meta"]=shadow_meta
    summary["preseason_v973_meta"]={
        "build":v973.get("build"),
        "status":v973.get("status"),
        "football_model_promotion_review_positions":v973.get("football_model_promotion_review_positions",[]),
        "expected_season_points_ready_positions":v973.get("expected_season_points_ready_positions",[]),
        "market_fallback_replacement_validated":v973.get("replacement_claim_vs_market_fallback",False),
        "production_activation_allowed":v973.get("production_activation_allowed",False),
    }
    summary["league_value_meta"]=vmeta; summary["market_mistake_status"]=mistakes.get("status")
    latest_market=(market_snapshot_paths:=sorted((Path(a.market_root)/str(a.season)).glob("season_market_*.jsonl.gz")))
    latest_market_path=latest_market[-1] if latest_market else None
    summary["provenance"]={
        "source_commit":os.environ.get("GITHUB_SHA"),
        "league_root":str(root),
        "season":int(a.season),
        "requested_adp_key":a.adp_key,
        "resolved_adp_key":adp_key,
        "profile_expected_adp_key":expected_adp_key,
        "explicit_adp_override":str(a.adp_key).upper()!="AUTO" and adp_key!=expected_adp_key,
        "profile_sha256":sha256_file(root/"profile.json") or sha256_file(root/"league_profile.json"),
        "milestone1_sha256":sha256_file(root/"milestone1.json"),
        "milestone9_sha256":sha256_file(root/"milestone9.json"),
        "season_board_sha256":sha256_file(board_path),
        "season_projection_v972_sha256":sha256_file(out/"season_projection_v972.csv"),
        "preseason_v973_validation_sha256":sha256_file(out/"preseason_v973_validation.json"),
        "preseason_v973_predictions_sha256":sha256_file(out/"preseason_v973_predictions.csv"),
        "preseason_v973_calibration_sha256":sha256_file(out/"preseason_v973_calibration.csv"),
        "current_manifest_sha256":sha256_file(current_path),
        "current_snapshot_hydrated":bool(current.get("players")),
        "market_snapshot_count":len(latest_market),
        "latest_market_snapshot":str(latest_market_path) if latest_market_path else None,
        "latest_market_sha256":sha256_file(latest_market_path) if latest_market_path else None,
    }
    summary["phase_readiness"]={
        "preseason_v2":{p:(pv2.get("per_position",{}).get(p,{}) or {}).get("status") for p in ["QB","RB","WR","TE"]},
        "season_projection_v972":{
            "status":shadow_meta.get("status"),
            "validated_positions":shadow_meta.get("validated_positions",[]),
            "shadow_applied":shadow_meta.get("shadow_applied",0),
            "shadow_applied_by_position":shadow_meta.get("shadow_applied_by_position",{}),
        },
        "preseason_v973_head_to_head":{
            "status":v973.get("status"),
            "football_model_promotion_review_positions":v973.get("football_model_promotion_review_positions",[]),
            "expected_season_points_ready_positions":v973.get("expected_season_points_ready_positions",[]),
            "market_fallback_head_to_head":((v973.get("comparison") or {}).get("market_fallback_head_to_head") or {}).get("status"),
        },
        "market_movement":mmeta.get("status"),
        "historical_adp_curves":cmeta.get("status"),
        "market_mistakes":mistakes.get("status"),
        "injury_opportunity":injury.get("status"),
        "actionable_findings":findings.get("finding_count",0),
    }
    summary["outputs"]=["preseason_v2.json","preseason_v973_validation.json","preseason_v973_predictions.csv","preseason_v973_calibration.csv",
                        "season_projection_v972.csv","market_movement.csv","adp_outcome_curves.csv","league_value_board.csv",
                        "draft_actions.csv","injury_opportunity.json","market_mistake_research.json","actionable_findings.json"]
    write_strict_json(out/"strategy_stack.json", summary)
    print(json.dumps(json_safe({"status":summary["status"],"value_labels":summary["value_labels"],
                      "preseason_eligible":pv2.get("production_eligible_positions",[]),
                      "v972_shadow_applied":shadow_meta.get("shadow_applied",0),
                      "v972_by_position":shadow_meta.get("shadow_applied_by_position",{}),
                      "v973_promotion_review":v973.get("football_model_promotion_review_positions",[]),
                      "v973_expected_points_ready":v973.get("expected_season_points_ready_positions",[]),
                      "market_curve_status":cmeta.get("status"),"findings":findings.get("finding_count")}),indent=2,allow_nan=False))

if __name__=="__main__": main()
