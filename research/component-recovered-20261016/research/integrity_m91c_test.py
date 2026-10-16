#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
import pandas as pd
from build_m91c_season_challenger import (
    latest_team_environment,fit_role_estimators,apply_role_estimator,
    assign_role_cohorts,role_cohort_residual_anchor,
)
from validate_m91c_season_challenger import canonicalize_optional_schema

# Canonical M8 team environment: new-team QB pressure/sack fields are recoverable.
rows=[]
for w in range(1,13):
    rows.append({
      "canonical_player_id":"q1","season":2025,"week":w,"team":"NEW","position_model":"QB",
      "pfr_times_pressured_pct_prior4":20+w*.1,"pfr_times_sacked_prior4":2+w*.01,
      "snap_share_prior4":.98,"ngs_avg_time_to_throw_prior4":2.7,
    })
pw=pd.DataFrame(rows)
env=latest_team_environment(pw)
assert "NEW" in env
assert env["NEW"]["pfr_times_pressured_pct_prior4"] is not None
assert env["NEW"]["pfr_times_sacked_prior4"] is not None

# Historical role mapping can estimate current snap share from current target share.
n=160
role=pd.DataFrame({
 "position_model":["WR"]*n,
 "target_share_prior4":np.linspace(.05,.35,n),
 "offense_snap_share_prior4":np.linspace(.35,.95,n),
 "red_zone_target_share_prior4":np.linspace(.04,.34,n),
})
models,audit=fit_role_estimators(role)
adapt={"target_share_prior4":.25}
snap=apply_role_estimator(adapt,pos="WR",target="offense_snap_share_prior4",models=models)
assert snap is not None and .5<snap<1.0

# Role cohorts plus same-cohort local calibration: a high raw-FIE backup remains
# inside the DEPTH baseline neighborhood and cannot borrow starter references.
market=[]
for i,m in enumerate([10,12,14,16,18,20,22,24,210,230,250,270,290,310,330,350]):
    market.append({
      "canonical_player_id":f"q{i}","sleeper_id":f"s{i}","position_model":"QB",
      "sleeper_market_projection":m,
      "m91c_raw_fie_projection":(220+i if m<30 else 220+i*3),
      "m91c_exact_scoring_replay":True,"m91c_team_changed":False,
      "m91c_uncertainty_spread_multiplier":1.0,
      "p10":max(0,m-40),"p50":m,"p90":m+40,
    })
d=pd.DataFrame(market)
ctx={r["canonical_player_id"]:{"values":{"qb_pass_attempt_share_prior4":(.1 if r["sleeper_market_projection"]<30 else .9)}} for r in market}
avail={f"s{i}":{"depth_chart_order":(2 if r["sleeper_market_projection"]<30 else 1)} for i,r in enumerate(market)}
d=assign_role_cohorts(d,context=ctx,availability=avail)
assert set(d[d.sleeper_market_projection.lt(30)].m91c_role_cohort)=={"DEPTH"}
assert set(d[d.sleeper_market_projection.gt(200)].m91c_role_cohort).issubset({"STARTER","CLEAR_STARTER"})
proj,audit=role_cohort_residual_anchor(d,min_reference=6,max_reference=6)
low=d.index[d.sleeper_market_projection.eq(10)][0]
assert proj.loc[low] < 30,proj.loc[low]
assert d.loc[low,"m91c_reference_role_cohort"]=="DEPTH"
assert abs(d.loc[low,"m91c_applied_adjustment"])<=d.loc[low,"m91c_correction_cap"]+1e-9

# Regression: a zero-exact league is a legitimate BASELINE_ONLY board.  Optional
# calibration fields must still have a stable schema without manufacturing signal.
zero=pd.DataFrame({
    "sleeper_market_projection":[100.0,80.0],
    "m91c_projection":[100.0,80.0],
    "m91c_exact_scoring_replay":[False,False],
    "m91c_production_eligible":[False,False],
    "m91c_calibration_method":["BASELINE_ONLY","BASELINE_ONLY"],
})
zero,added=canonicalize_optional_schema(zero)
for c in (
    "m91c_signal_z","m91c_total_reliability","m91c_correction_cap",
    "m91c_applied_adjustment","m91c_reference_role_cohort",
):
    assert c in zero.columns,c
assert pd.to_numeric(zero.m91c_signal_z,errors="coerce").isna().all()
assert pd.to_numeric(zero.m91c_total_reliability,errors="coerce").isna().all()
assert pd.to_numeric(zero.m91c_correction_cap,errors="coerce").isna().all()
assert pd.to_numeric(zero.m91c_applied_adjustment,errors="coerce").eq(0.0).all()
assert zero.m91c_reference_role_cohort.isna().all()
assert "m91c_signal_z" in added

# Existing calibrated values must never be overwritten by schema canonicalization.
existing=pd.DataFrame({
    "m91c_signal_z":[2.5],
    "m91c_total_reliability":[.6],
    "m91c_correction_cap":[10.0],
    "m91c_applied_adjustment":[4.0],
    "m91c_reference_role_cohort":["CLEAR_STARTER"],
})
existing,_=canonicalize_optional_schema(existing)
assert existing.loc[0,"m91c_signal_z"]==2.5
assert existing.loc[0,"m91c_applied_adjustment"]==4.0

print("PASS M9.1c: M8 new-team environment, current-workload role estimation, role cohorts, density reliability, same-cohort calibration, correction cap and zero-exact baseline schema")
