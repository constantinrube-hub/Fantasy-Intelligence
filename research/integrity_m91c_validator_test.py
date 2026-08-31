#!/usr/bin/env python3
"""Regression test for M9.1c transition-environment validation semantics."""
import pandas as pd
from validate_m91c_season_challenger import has_pressure_env

df=pd.DataFrame({
    "m8":[
        "pfr_times_pressured_pct_prior4|pfr_times_sacked_prior4",
        "",
        "",
    ],
    "other":[
        "",
        "pfr_times_pressured_pct_prior4|pfr_times_sacked_prior4",
        "",
    ],
    "cleared":[
        "",
        "",
        "pfr_times_pressured_pct_prior4|pfr_times_sacked_prior4",
    ],
})
m8=has_pressure_env(df["m8"])
other=has_pressure_env(df["other"])
cleared=has_pressure_env(df["cleared"])
assert (m8|other|cleared).all()
assert int(m8.sum())==1
assert int(other.sum())==1
assert int(cleared.sum())==1
print("PASS M9.1c validator: M8 replacement, approved other new-team replacement, or governed clear are all distinguished")
