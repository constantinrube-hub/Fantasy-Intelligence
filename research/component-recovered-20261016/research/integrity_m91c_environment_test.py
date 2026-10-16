#!/usr/bin/env python3
import pandas as pd
import build_m91c_season_challenger as c

raw=pd.DataFrame([
    {
        "canonical_player_id":"q1","season":2025,"week":w,
        "team":"NEW","position_model":"QB","fantasy_points":20.0
    }
    for w in range(1,9)
])
identity=pd.DataFrame([{"canonical_player_id":"q1","pfr_id":"Q1"}])

orig_enrich=c.add_public_enrichment
orig_lag=c.add_lagged_advanced
calls={"enrich":False,"lag":False}

def fake_enrich(df,identity,cache_dir,seasons):
    calls["enrich"]=True
    d=df.copy()
    # Mimic raw M3 PFR/NGS columns before lagging.
    d["pfr_times_pressured_pct"]=20.0
    d["pfr_times_sacked"]=2.0
    d["ngs_avg_time_to_throw"]=2.7
    return d,{"feature_columns":[
        "pfr_times_pressured_pct","pfr_times_sacked","ngs_avg_time_to_throw"
    ]}

def fake_lag(df,cols):
    calls["lag"]=True
    d=df.copy()
    g=d.groupby(["canonical_player_id","season"],group_keys=False)
    for col in cols:
        d[f"{col}_prior4"]=g[col].transform(
            lambda x:pd.to_numeric(x,errors="coerce").shift(1).rolling(4,min_periods=2).mean()
        )
    # M8 weights by snap_share_prior4 when present, but does not require it.
    return d

try:
    c.add_public_enrichment=fake_enrich
    c.add_lagged_advanced=fake_lag
    env=c.latest_team_environment(
        raw,identity=identity,cache_dir=pd.io.common.Path("/tmp") if False else __import__("pathlib").Path("/tmp"),
        seasons=[2025]
    )
finally:
    c.add_public_enrichment=orig_enrich
    c.add_lagged_advanced=orig_lag

assert calls["enrich"] is True
assert calls["lag"] is True
assert "NEW" in env,env
assert env["NEW"]["pfr_times_pressured_pct_prior4"] is not None,env
assert env["NEW"]["pfr_times_sacked_prior4"] is not None,env
print("PASS M9.1c canonical environment ordering: M3 public enrichment -> lagged advanced -> M8")
