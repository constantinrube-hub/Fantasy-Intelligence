#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

def bs(s):
    if s.dtype==bool:return s.fillna(False)
    return s.astype(str).str.lower().isin({"true","1","yes"})

def main():
    p=argparse.ArgumentParser();p.add_argument("--league-id",required=True);p.add_argument("--season",type=int,required=True);p.add_argument("--output-dir",default="")
    a=p.parse_args()
    d=Path(a.output_dir) if a.output_dir else Path(f"data/research/leagues/{a.league_id}/performance/{a.season}/m91c_challenger")
    board=d/"m91c_season_board.csv";meta=d/"m91c_meta.json";evaluation=d/"m91c_evaluation.json"
    assert board.is_file() and meta.is_file() and evaluation.is_file()
    m=json.loads(meta.read_text())
    assert m["research_build"]=="M9.1c-ROLE-COHORT-DENSITY-RELIABILITY"
    assert m["production_eligible"] is False and m["automatic_promotion"] is False
    assert m["sleeper_is_fixed_baseline"] is True and m["adp_in_football_model"] is False
    assert m["calibration"]["same_cohort_only"] is True
    assert m["team_transition_policy"]["team_change_is_never_a_block_reason"] is True
    assert m["team_transition_policy"]["old_team_context_carried"] is False

    df=pd.read_csv(board,low_memory=False)
    req={
      "m91c_projection","m91c_role_cohort","m91c_raw_fie_projection",
      "m91c_exact_scoring_replay","m91c_signal_z","m91c_total_reliability",
      "m91c_correction_cap","m91c_applied_adjustment","m91c_production_eligible",
    }
    assert req.issubset(df.columns),req-set(df.columns)
    assert not bs(df.m91c_production_eligible).any()

    mkt=pd.to_numeric(df.sleeper_market_projection,errors="coerce")
    proj=pd.to_numeric(df.m91c_projection,errors="coerce")
    changed=(proj-mkt).abs().gt(1e-9)&proj.notna()&mkt.notna()
    exact=bs(df.m91c_exact_scoring_replay)
    assert (~changed|exact).all()

    # Every calibrated row must use references from exactly its own role cohort.
    z=df[df.m91c_reference_role_cohort.notna()]
    assert (z.m91c_reference_role_cohort.astype(str)==z.m91c_role_cohort.astype(str)).all()

    # Applied adjustment must respect reliability and the data-derived cap.
    app=pd.to_numeric(df.m91c_applied_adjustment,errors="coerce")
    cap=pd.to_numeric(df.m91c_correction_cap,errors="coerce")
    q=app.notna()&cap.notna()
    assert (app[q].abs()<=cap[q]+1e-8).all()
    rel=pd.to_numeric(df.m91c_total_reliability,errors="coerce")
    assert ((rel.dropna()>=0)&(rel.dropna()<=1)).all()

    # Team transition may never itself block QB/RB/WR/TE.
    tc=df[bs(df.m91c_team_changed)&df.position_model.astype(str).isin({"QB","RB","WR","TE"})]
    assert not tc.m91c_status.astype(str).str.contains("TEAM_CHANGE",case=False,regex=False).any()

    # M8 environment replacement should materially cover true changing QBs when source exists.
    qb=tc[tc.position_model.astype(str).eq("QB")]
    if len(qb):
        covered=qb.m91c_context_m8_environment_fields.fillna("").str.contains("pfr_times_")
        assert covered.mean()>=0.75,(int(covered.sum()),len(qb))

    print(f"PASS M9.1c rows={len(df)} adjusted={int(changed.sum())} transitions={len(tc)} qb_m8_coverage={(float(covered.mean()) if len(qb) else 1.0):.3f} gate={m['residual_model_gate']['status']}")
if __name__=="__main__":main()
