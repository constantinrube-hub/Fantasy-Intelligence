#!/usr/bin/env python3
import json,sys
from pathlib import Path
path=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone9.json');b=json.loads(path.read_text())
assert b.get('schema_version')==9 and b.get('milestone')=='M9' and b.get('status')=='complete'
r=b.get('returner_intelligence',{})
for name,s in (r.get('model_specs') or {}).items():
    agg=r.get('role_validation',{}).get('aggregate',{}) if name=='returner_role' else r.get('yard_validation',{}).get('aggregate',{})
    assert agg.get('status')=='validated_candidate'
season_ret=r.get('season_projection',{})
for target,s in (season_ret.get('model_specs') or {}).items():
    agg=season_ret.get('aggregate',{}).get(target,{})
    assert agg.get('status')=='validated_candidate' and int(agg.get('folds',0))>=4
    assert float(agg.get('bootstrap_ci95_low'))>0
    n=len(s.get('features') or [])
    assert n and len(s.get('coefficients') or [])==n and len(s.get('imputer_medians') or [])==n
pre=b.get('preseason_season_projection',{})
for pos,s in (pre.get('model_specs') or {}).items():
    assert pre.get('aggregate',{}).get(pos,{}).get('status')=='validated_candidate'
    for ts in s.get('targets') or []:
        n=len(ts.get('features') or [])
        assert n and len(ts.get('coefficients') or [])==n and len(ts.get('imputer_medians') or [])==n
for pos,c in b.get('projection_distribution',{}).get('position_calibration',{}).items():
    q=[c.get(x) for x in ['q10','q25','q50','q75','q90']];assert all(x is not None for x in q) and q==sorted(q)
assert b.get('market_report_contract',{}).get('universe')=={'QB':24,'RB':36,'WR':36,'TE':24}
print(f'PASS M9 bundle {path}')
