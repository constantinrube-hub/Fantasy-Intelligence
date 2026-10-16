import numpy as np
import pandas as pd
from decision_validation import evaluate_domain, promotion_decision, Gate

rng=np.random.default_rng(7)
rows=[]
for w in range(1,13):
    for i in range(50):
        actual=rng.normal(10,3)
        baseline=actual+rng.normal(0,2.0)
        candidate=actual+rng.normal(0,1.2)
        rows.append({"season":2025,"week":w,"actual":actual,"baseline":baseline,"candidate":candidate})
df=pd.DataFrame(rows)
r=evaluate_domain(df,"start_sit")
assert r["status"]=="complete"
assert r["metrics"]["candidate_mae"] < r["metrics"]["baseline_mae"]
assert r["metrics"]["paired_bootstrap"]["ci_low"] > 0
assert r["promotion"]["enabled"] is True
small=evaluate_domain(df.head(20),"start_sit")
assert small["promotion"]["enabled"] is False
missing=evaluate_domain(pd.DataFrame({"actual":[1],"candidate":[1]}),"draft")
assert missing["status"]=="unavailable" and missing["promotion"]["enabled"] is False
print("decision validation integrity: OK")
