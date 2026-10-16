"""Bounded raw K source replay; no distance guesses or pre-scored points."""
from scoring_relevance import position_relevant, rule_spec
from strict_sleeper_baseline import finite

BUCKETS=('fgm_0_19','fgm_20_29','fgm_30_39','fgm_40_49','fgm_50p')
TOL=1e-10


def components(stats):
    if not isinstance(stats,dict):raise ValueError('K_SOURCE_STATS_INVALID')
    out={};proof={}
    for key,value in stats.items():
        if rule_spec(key) and position_relevant(key,'K') and key.startswith(('fgm','fgmiss','xpm','xpmiss')):
            number=finite(value)
            if number is None or number<0:raise ValueError('K_SOURCE_NEGATIVE_OR_NONFINITE')
            out[key]=number;proof[key]={'basis':'EXPLICIT_SAME_NAMED_COMPONENT','source_keys':[key]}
    for miss,attempt,made in [('fgmiss','fga','fgm'),('xpmiss','xpa','xpm')]:
        if attempt in stats and made in stats:
            a,m=finite(stats[attempt]),finite(stats[made])
            if a is None or m is None or a<0 or m<0 or a+TOL<m:raise ValueError('K_SOURCE_ATTEMPT_MAKE_CONFLICT')
            residual=max(0.,a-m)
            if miss in out and abs(out[miss]-residual)>TOL:raise ValueError('K_SOURCE_DIRECT_MISS_CONFLICT')
            out[miss]=residual;proof[miss]={'basis':'ATTEMPT_MINUS_MADE','source_keys':[attempt,made]}
    if 'fgm' in out:
        present=[key for key in BUCKETS if key in out];missing=[key for key in BUCKETS if key not in out]
        residual=out['fgm']-sum(out[key] for key in present)
        if residual < -TOL:raise ValueError('K_SOURCE_BUCKET_TOTAL_CONFLICT')
        residual=max(0.,residual)
        if not missing and residual>TOL:raise ValueError('K_SOURCE_BUCKET_TOTAL_CONFLICT')
        if len(missing)==1 or residual<=TOL:
            for key in missing:
                out[key]=residual if len(missing)==1 else 0.
                proof[key]={'basis':'EXHAUSTIVE_DISJOINT_TOTAL_RESIDUAL','source_keys':['fgm',*present]}
    return out,proof


def audit(stats,scoring):
    try:values,proof=components(stats)
    except ValueError as error:
        return {'exact':False,'points':None,'status':str(error),'keys':[]}
    rows=[];total=0.;relevant=0
    for key,raw in sorted(scoring.items()):
        weight=finite(raw)
        if weight is None:rows.append({'key':key,'status':'INVALID_WEIGHT'});continue
        if weight==0:continue
        if not position_relevant(key,'K'):continue
        relevant+=1
        if key not in values:rows.append({'key':key,'status':'MISSING_OR_UNSUPPORTED_EXPLICIT_COMPONENT'});continue
        total+=weight*values[key]
        rows.append({'key':key,'status':'EXACT_SOURCE_COMPONENT','stat_value':values[key],'weight':weight,**proof[key]})
    exact=relevant>0 and finite(total) is not None and all(row['status']=='EXACT_SOURCE_COMPONENT' for row in rows)
    return {'exact':exact,'points':round(total,6) if exact else None,'status':'EXACT_K_SOURCE_COMPONENTS' if exact else 'BLOCKED_K_SOURCE_COMPONENTS','position':'K','keys':rows}
