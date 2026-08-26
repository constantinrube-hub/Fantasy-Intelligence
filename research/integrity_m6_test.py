#!/usr/bin/env python3
import json, math, tempfile
from pathlib import Path
import pandas as pd
from build_current_snapshot import predict_linear_spec
from fie_m6 import add_opponent_role_prior, blocked_advanced_ledger
from fie_governance import build
from types import SimpleNamespace

# Linear export must reconstruct standardize+ridge deterministically.
spec={'features':['a','b'],'imputer_medians':[2,4],'scaler_mean':[1,2],'scaler_scale':[1,2],'coefficients':[3,4],'intercept':5,'prediction_floor':0}
p,c=predict_linear_spec(spec,{'a':2,'b':6})
assert abs(p-16)<1e-9 and abs(c-1)<1e-9,(p,c)
p,c=predict_linear_spec(spec,{'a':None,'b':6})
assert abs(p-16)<1e-9 and abs(c-.5)<1e-9,(p,c)

# Opponent-role prior must not use the same game's allowed points.
df=pd.DataFrame({'season':[2024]*5,'week':[1,2,3,4,5],'opponent_team':['X']*5,'position_model':['WR']*5,'fantasy_points':[10,20,30,40,100]})
o=add_opponent_role_prior(df)
assert pd.isna(o.loc[o.week==1,'opp_pos_fp_allowed_prior4']).all()
# week 5 prior should be based on weeks 1-4 only, not the 100-point current outcome.
v=float(o.loc[o.week==5,'opp_pos_fp_allowed_prior4'].iloc[0]);assert abs(v-25)<1e-9,v
assert any(x['analysis']=='all_route_alignment_and_separation' for x in blocked_advanced_ledger())

# CONTROL override must hard-disable runtime even if every artifact otherwise looks good.
with tempfile.TemporaryDirectory() as td:
    q=Path(td)
    def w(name,obj):(q/name).write_text(json.dumps(obj))
    w('m4.json',{'status':'complete'});w('m5.json',{'status':'complete','scoring_signature':'abc','activation':{'decision_gates':{}}});w('m6.json',{'status':'complete','scoring_signature':'abc'})
    w('cur.json',{'status':'complete','producer_build':'V8.8-M6','m5_build':'V8.7-M5','scoring_signature':'abc','generated_at':pd.Timestamp.utcnow().isoformat(),'snapshot_max_age_hours':18,'target_week_realised_stats_excluded':True,'summary':{'activation_eligible':3}})
    w('override.json',{'mode':'CONTROL'})
    a=SimpleNamespace(m4_bundle=str(q/'m4.json'),m5_bundle=str(q/'m5.json'),m6_bundle=str(q/'m6.json'),current_snapshot=str(q/'cur.json'),operator_override=str(q/'override.json'),mode='KEEP',max_age_hours=18)
    g=build(a);assert g['runtime_enabled'] is False and g['fallback']=='V8.2.2'
print('M6 integrity tests passed')
