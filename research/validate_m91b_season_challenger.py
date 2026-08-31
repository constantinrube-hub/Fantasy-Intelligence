#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

OFFENSE={"QB","RB","WR","TE"}

def bs(s):
    if s.dtype==bool:return s.fillna(False)
    return s.astype(str).str.lower().isin({"true","1","yes"})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--league-id",required=True);p.add_argument("--season",required=True,type=int)
    p.add_argument("--output-dir",default="")
    a=p.parse_args()
    d=Path(a.output_dir) if a.output_dir else Path(f"data/research/leagues/{a.league_id}/performance/{a.season}/m91b_challenger")
    board=d/"m91b_season_board.csv"; meta=d/"m91b_meta.json"
    assert board.is_file() and meta.is_file()
    m=json.loads(meta.read_text())
    assert m["research_build"]=="M9.1b-LOCAL-RESIDUAL-TRANSITION-CONTEXT"
    assert m["production_eligible"] is False and m["automatic_promotion"] is False
    assert m["sleeper_is_fixed_baseline"] is True
    assert m["adp_in_football_model"] is False
    assert m["calibration"]["method"]=="LOCAL_BASELINE_RESIDUAL_ANCHOR"
    assert m["team_transition_policy"]["team_change_is_never_a_block_reason"] is True
    assert m["team_transition_policy"]["old_team_context_carried"] is False
    assert set(m["team_transition_policy"]["applies_to_positions"])==OFFENSE

    df=pd.read_csv(board,low_memory=False)
    req={
      "m91b_projection","m91b_raw_fie_projection","m91b_exact_scoring_replay",
      "m91b_team_changed","m91b_calibration_method","m91b_production_eligible",
      "m91b_applied_adjustment","m91b_uncertainty_spread_multiplier",
    }
    assert req.issubset(df.columns),req-set(df.columns)
    assert not bs(df.m91b_production_eligible).any()

    mkt=pd.to_numeric(df.sleeper_market_projection,errors="coerce")
    proj=pd.to_numeric(df.m91b_projection,errors="coerce")
    changed=(proj-mkt).abs().gt(1e-9)&proj.notna()&mkt.notna()
    exact=bs(df.m91b_exact_scoring_replay)
    assert (~changed|exact).all()

    # Transition itself may not be a block reason at any offensive position.
    tc=df[bs(df.m91b_team_changed)&df.position_model.astype(str).isin(OFFENSE)]
    assert not tc.m91b_status.astype(str).str.contains("TEAM_CHANGE",case=False,regex=False).any()

    # Alias normalization must specifically prevent LA/LAR from being treated as a move.
    alias=df[
      df.team.astype(str).isin(["LAR","LA"])&
      df.profile_team.astype(str).isin(["LAR","LA"])&
      df.team.notna()&df.profile_team.notna()
    ]
    if len(alias):
        assert not bs(alias.m91b_team_changed).any()

    # Local residual calibration is conservative: the applied adjustment cannot exceed
    # the unshrunk market-scale adjustment in absolute value.
    rawadj=pd.to_numeric(df.m91b_raw_market_scale_adjustment,errors="coerce")
    app=pd.to_numeric(df.m91b_applied_adjustment,errors="coerce")
    z=rawadj.notna()&app.notna()
    assert (app[z].abs()<=rawadj[z].abs()+1e-8).all()

    print(f"PASS M9.1b rows={len(df)} adjusted={int(changed.sum())} transitions={len(tc)} alias_fixes={m['team_alias_false_changes_fixed']} gate={m['residual_model_gate']['status']}")
if __name__=="__main__":main()
