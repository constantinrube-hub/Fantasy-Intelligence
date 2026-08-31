#!/usr/bin/env python3
import pandas as pd
import build_m91c_season_challenger as c

raw=pd.DataFrame([
    {"canonical_player_id":"q1","season":2025,"week":w,"team":"NEW","position_model":"QB"}
    for w in range(1,9)
])

original=c.add_derived_driver_features
called={"value":False}
def fake_enrich(df):
    called["value"]=True
    d=df.copy()
    d["pfr_times_pressured_pct_prior4"]=20.0
    d["pfr_times_sacked_prior4"]=2.0
    d["snap_share_prior4"]=0.98
    d["ngs_avg_time_to_throw_prior4"]=2.7
    return d

try:
    c.add_derived_driver_features=fake_enrich
    env=c.latest_team_environment(raw)
finally:
    c.add_derived_driver_features=original

assert called["value"] is True
assert "NEW" in env
assert env["NEW"]["pfr_times_pressured_pct_prior4"] is not None
assert env["NEW"]["pfr_times_sacked_prior4"] is not None
print("PASS M9.1c real-run environment ordering: M7 enrichment occurs before M8 team aggregation")
