#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

def bs(s):
    if s.dtype==bool:return s.fillna(False)
    return s.astype(str).str.lower().isin({"true","1","yes"})

def has_pressure_env(s):
    return s.fillna("").astype(str).str.contains(
        "pfr_times_pressured_pct_prior4|pfr_times_sacked_prior4",
        regex=True,
    )

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--league-id",required=True)
    p.add_argument("--season",type=int,required=True)
    p.add_argument("--output-dir",default="")
    a=p.parse_args()

    d=Path(a.output_dir) if a.output_dir else Path(
        f"data/research/leagues/{a.league_id}/performance/{a.season}/m91c_challenger"
    )
    board=d/"m91c_season_board.csv"
    meta=d/"m91c_meta.json"
    evaluation=d/"m91c_evaluation.json"
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
      "m91c_context_m8_environment_fields",
      "m91c_context_other_team_environment_fields",
      "m91c_context_cleared_fields",
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

    # Missing/unassigned current team is not a team transition.
    team_missing=df["team"].isna() | df["team"].astype(str).str.strip().str.upper().isin(
        {"", "NAN", "NONE", "NULL", "NA", "N/A", "<NA>"}
    )
    assert not (bs(df.m91c_team_changed) & team_missing).any(), (
        "players without a current team must not be classified as transitions",
        df.loc[
            bs(df.m91c_team_changed) & team_missing,
            ["full_name","position_model","team","profile_team"]
        ].to_dict("records"),
    )

    # Team transition may never itself block QB/RB/WR/TE.
    tc=df[
        bs(df.m91c_team_changed)
        & df.position_model.astype(str).isin({"QB","RB","WR","TE"})
    ]
    assert not tc.m91c_status.astype(str).str.contains(
        "TEAM_CHANGE",case=False,regex=False
    ).any()

    # Correct invariant for QB transition environment:
    # 1) prefer canonical M8 new-team context;
    # 2) allow the existing provenance-recorded new-team environment donor;
    # 3) when neither source exists, pressure/sack context must be explicitly
    #    cleared so no old-team context can leak into the replay.
    qb=tc[tc.position_model.astype(str).eq("QB")].copy()
    m8_covered=pd.Series(False,index=qb.index)
    other_covered=pd.Series(False,index=qb.index)
    cleared=pd.Series(False,index=qb.index)

    if len(qb):
        m8_covered=has_pressure_env(qb.m91c_context_m8_environment_fields)
        other_covered=has_pressure_env(qb.m91c_context_other_team_environment_fields)
        cleared=has_pressure_env(qb.m91c_context_cleared_fields)

        approved_replacement=m8_covered|other_covered
        governed_missing=~approved_replacement & cleared

        # Fail if a changing QB has neither a documented new-team replacement
        # nor an explicit clear/impute state. That would risk stale old-team leakage.
        assert (approved_replacement|governed_missing).all(), (
            "changing QB pressure context neither replaced nor cleared",
            qb.loc[
                ~(approved_replacement|governed_missing),
                ["full_name","team","profile_team",
                 "m91c_context_m8_environment_fields",
                 "m91c_context_other_team_environment_fields",
                 "m91c_context_cleared_fields"]
            ].to_dict("records"),
        )

        # Any row claiming M8 replacement must actually name one of the required
        # pressure/sack fields; same for the other approved new-team environment path.
        assert not (
            qb.m91c_context_m8_environment_fields.fillna("").str.contains("pfr_times_")
            & ~m8_covered
        ).any()
        assert not (
            qb.m91c_context_other_team_environment_fields.fillna("").str.contains("pfr_times_")
            & ~other_covered
        ).any()

    m8_rate=float(m8_covered.mean()) if len(qb) else 1.0
    any_env_rate=float((m8_covered|other_covered).mean()) if len(qb) else 1.0
    governed_rate=float((m8_covered|other_covered|cleared).mean()) if len(qb) else 1.0

    print(
        f"PASS M9.1c rows={len(df)} adjusted={int(changed.sum())} "
        f"transitions={len(tc)} qb_m8_env={m8_rate:.3f} "
        f"qb_any_new_team_env={any_env_rate:.3f} "
        f"qb_replaced_or_governed_clear={governed_rate:.3f} "
        f"gate={m['residual_model_gate']['status']}"
    )

if __name__=="__main__":
    main()
