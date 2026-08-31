#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

OFFENSE={"QB","RB","WR","TE"}

def bseries(s):
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin({"true","1","yes"})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--league-id",required=True)
    ap.add_argument("--season",required=True,type=int)
    ap.add_argument("--output-dir",default="")
    a=ap.parse_args()
    d=Path(a.output_dir) if a.output_dir else Path("data/research/leagues")/str(a.league_id)/"performance"/str(a.season)/"m91_challenger"
    board=d/"m91_season_board.csv"; meta=d/"m91_meta.json"
    assert board.is_file() and meta.is_file()
    x=json.loads(meta.read_text())
    assert x["research_build"]=="M9.1-TRANSITION-AWARE-CHALLENGER"
    assert x["production_eligible"] is False
    assert x["automatic_promotion"] is False
    assert x["sleeper_is_fixed_baseline"] is True
    assert x["single_mean_centering_applied"] is False
    assert x["distribution_anchor"]["method"]=="POSITION_EMPIRICAL_QUANTILE_ANCHOR"
    assert x["profile_source"] in {
        "EXISTING_M9_DERIVED_PROFILE",
        "REHYDRATED_FROM_CANONICAL_PLAYER_WEEK_AND_COMMITTED_M9_SPEC",
    }
    assert x["profile_rehydration_refit"] is False
    policy=x["team_transition_policy"]
    assert set(policy["applies_to_positions"])==OFFENSE
    assert policy["team_change_is_never_a_block_reason"] is True
    assert policy["old_team_context_carried"] is False
    h=x["residual_model_gate"]
    assert h["status"] in {"BLOCKED_MISSING_HISTORICAL_SLEEPER_BASELINE","READY_FOR_RESIDUAL_RESEARCH"}

    df=pd.read_csv(board,low_memory=False)
    required={
      "sleeper_market_projection","m91_projection","m91_raw_fie_projection","m91_status",
      "m91_mean_centering_applied","m91_distribution_anchor_applied",
      "m91_calibration_method","m91_exact_scoring_replay",
      "m91_team_transition_status","m91_residual_gate","m91_production_eligible"
    }
    assert required.issubset(df.columns),required-set(df.columns)
    assert not bseries(df["m91_production_eligible"]).any()
    assert not bseries(df["m91_mean_centering_applied"]).any()

    mkt=pd.to_numeric(df.sleeper_market_projection,errors="coerce")
    proj=pd.to_numeric(df.m91_projection,errors="coerce")
    changed=(proj-mkt).abs().gt(1e-9) & proj.notna() & mkt.notna()
    exact=bseries(df.m91_exact_scoring_replay)
    anchored=bseries(df.m91_distribution_anchor_applied)
    # Any M9.1 movement away from Sleeper requires exact replay AND the supported
    # distribution anchor. Raw uncalibrated FIE points can never become challenger points.
    assert (~changed | (exact & anchored)).all()

    # Team change alone may not produce a blocked status at any offensive position.
    tc=df[bseries(df.team_changed) & df.position_model.astype(str).isin(OFFENSE)]
    assert not tc.m91_status.astype(str).str.contains("TEAM_CHANGE",case=False,regex=False).any()
    # When a team changer has a profile/spec, its transition adapter is the generic
    # position-independent NEW_TEAM_CONTEXT_REBUILT path.
    modeled_tc=tc[tc.m91_team_transition_status.astype(str).ne("NO_PROFILE")]
    if len(modeled_tc):
        assert modeled_tc.m91_team_transition_status.astype(str).isin({"NEW_TEAM_CONTEXT_REBUILT"}).all()

    print(f"PASS M9.1 distribution-anchored challenger rows={len(df)} changed={int(changed.sum())} team_changes={len(tc)} gate={h['status']}")

if __name__=="__main__":
    main()
